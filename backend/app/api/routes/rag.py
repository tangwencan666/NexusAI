import json
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chat.factory import get_chat_model
from app.ai.embeddings.factory import get_embedding_provider
from app.core.config import settings
from app.db.session import get_db
from app.knowledge.query.rewrite import ChatQueryRewriter
from app.knowledge.rag.pipeline import RAGPipeline
from app.knowledge.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from app.knowledge.reranking.factory import get_reranker
from app.knowledge.retrieval.bm25 import BM25Retriever
from app.knowledge.retrieval.hybrid import HybridRetriever
from app.knowledge.retrieval.vector import VectorSearchService
from app.schemas.rag import ChatRequest, ChatResponse, RetrievalDebugRequest, RetrievalDebugResponse

router = APIRouter(tags=["rag"])


def build_pipeline(db: AsyncSession) -> RAGPipeline:
    chat_model = get_chat_model()
    hybrid = HybridRetriever(
        VectorSearchService(db, get_embedding_provider()), BM25Retriever(db)
    )
    return RAGPipeline(hybrid, get_reranker(), ChatQueryRewriter(chat_model), chat_model)


@router.post("/knowledge-bases/{knowledge_base_id}/retrieve", response_model=RetrievalDebugResponse)
async def retrieve(
    knowledge_base_id: UUID,
    payload: RetrievalDebugRequest,
    db: AsyncSession = Depends(get_db),
) -> RetrievalDebugResponse:
    pipeline = build_pipeline(db)
    trace = await pipeline.hybrid.search(knowledge_base_id, payload.query)
    if payload.mode == "rerank":
        trace.reranked_results = await pipeline.reranker.rerank(
            payload.query, trace.rrf_results, min(payload.top_k, settings.rerank_top_k)
        )
    elif payload.mode == "vector":
        trace.bm25_results = []
        trace.rrf_results = []
    elif payload.mode == "bm25":
        trace.vector_results = []
        trace.rrf_results = []
    return RetrievalDebugResponse(**asdict(trace))


@router.post("/knowledge-bases/{knowledge_base_id}/chat", response_model=ChatResponse)
async def chat(
    knowledge_base_id: UUID,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    result = await build_pipeline(db).run(
        knowledge_base_id, payload.message, payload.recent_messages
    )
    return ChatResponse(
        answer=result.answer,
        citations=[asdict(citation) for citation in result.citations],
        retrieval={
            "original_query": result.trace.retrieval.original_query,
            "rewritten_query": result.trace.retrieval.rewritten_query,
            "results_count": len(result.trace.retrieval.reranked_results),
        },
        trace={
            "timings_ms": result.trace.timings_ms,
            "token_usage": result.trace.token_usage,
            "invalid_citations": result.trace.invalid_citations,
        },
    )


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


@router.post("/knowledge-bases/{knowledge_base_id}/chat/stream")
async def chat_stream(
    knowledge_base_id: UUID,
    payload: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    pipeline = build_pipeline(db)

    async def generate():
        try:
            retrieval, analysis, context, citations, timings = await pipeline.prepare(
                knowledge_base_id, payload.message, payload.recent_messages
            )
            yield sse("metadata", {"original_query": payload.message, "rewritten_query": retrieval.rewritten_query, "timings_ms": timings})
            async for token in pipeline.chat.stream(
                SYSTEM_PROMPT, build_user_prompt(payload.message, context.text)
            ):
                if await request.is_disconnected():
                    return
                yield sse("token", {"text": token})
            for citation in citations:
                yield sse("citation", asdict(citation))
            yield sse("done", {"citations": len(citations)})
        except Exception as exc:
            yield sse("error", {"code": getattr(exc, "code", "STREAM_INTERRUPTED"), "message": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
