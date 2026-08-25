import time
import uuid
from dataclasses import dataclass, field

from app.ai.chat.base import ChatModel
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.knowledge.citations.builder import Citation, build_citations
from app.knowledge.citations.validator import validate_citations
from app.knowledge.context.builder import BuiltContext, ContextBuilder
from app.knowledge.query.analyzer import QueryAnalysis, analyze_query
from app.knowledge.query.rewrite import QueryRewriter
from app.knowledge.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from app.knowledge.reranking.base import Reranker
from app.knowledge.retrieval.hybrid import HybridRetriever
from app.knowledge.retrieval.models import RetrievalTrace


@dataclass(slots=True)
class RAGTrace:
    retrieval: RetrievalTrace
    analysis: QueryAnalysis
    final_context: str
    timings_ms: dict[str, float] = field(default_factory=dict)
    token_usage: dict[str, int | None] = field(default_factory=dict)
    invalid_citations: list[int] = field(default_factory=list)


@dataclass(slots=True)
class RAGResult:
    answer: str
    citations: list[Citation]
    trace: RAGTrace


class RAGPipeline:
    def __init__(self, hybrid: HybridRetriever, reranker: Reranker, rewriter: QueryRewriter, chat: ChatModel) -> None:
        self.hybrid = hybrid
        self.reranker = reranker
        self.rewriter = rewriter
        self.chat = chat

    async def prepare(
        self, knowledge_base_id: uuid.UUID, message: str, conversation: list[str] | None = None
    ) -> tuple[RetrievalTrace, QueryAnalysis, BuiltContext, list[Citation], dict[str, float]]:
        total_started = time.perf_counter()
        analysis = analyze_query(message)
        rewrite_started = time.perf_counter()
        rewritten = await self.rewriter.rewrite(message, conversation or [])
        rewrite_done = time.perf_counter()
        retrieval = await self.hybrid.search(knowledge_base_id, rewritten)
        retrieval.original_query = message
        retrieval.rewritten_query = rewritten
        rerank_started = time.perf_counter()
        reranked = await self.reranker.rerank(rewritten, retrieval.rrf_results, settings.rerank_top_k)
        rerank_done = time.perf_counter()
        retrieval.reranked_results = reranked
        context = ContextBuilder(settings.rag_max_context_tokens).build(reranked)
        if not context.sources:
            raise ApplicationError("RAG_NO_CONTEXT", "No relevant context was found", 404)
        citations = build_citations(context)
        timings = {
            **retrieval.timings_ms,
            "query_rewrite": (rewrite_done - rewrite_started) * 1000,
            "rerank": (rerank_done - rerank_started) * 1000,
            "prepare_total": (time.perf_counter() - total_started) * 1000,
        }
        return retrieval, analysis, context, citations, timings

    async def run(
        self, knowledge_base_id: uuid.UUID, message: str, conversation: list[str] | None = None
    ) -> RAGResult:
        started = time.perf_counter()
        retrieval, analysis, context, citations, timings = await self.prepare(
            knowledge_base_id, message, conversation
        )
        llm_started = time.perf_counter()
        response = await self.chat.generate(SYSTEM_PROMPT, build_user_prompt(message, context.text))
        answer, invalid = validate_citations(response.text, citations)
        timings["llm"] = (time.perf_counter() - llm_started) * 1000
        timings["total"] = (time.perf_counter() - started) * 1000
        trace = RAGTrace(
            retrieval,
            analysis,
            context.text,
            timings,
            {"prompt_tokens": response.prompt_tokens, "completion_tokens": response.completion_tokens},
            invalid,
        )
        return RAGResult(answer, citations, trace)
