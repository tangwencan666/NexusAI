import uuid
import json
from dataclasses import asdict

from pydantic import BaseModel, Field

from app.agents.tools.base import BaseTool, ToolContext, ToolResult
from app.ai.embeddings.factory import get_embedding_provider
from app.knowledge.retrieval.bm25 import BM25Retriever
from app.knowledge.retrieval.hybrid import HybridRetriever
from app.knowledge.retrieval.vector import VectorSearchService


class KnowledgeSearchInput(BaseModel):
    knowledge_base_id: uuid.UUID
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchTool(BaseTool):
    name = "knowledge_search"
    description = "Retrieve evidence from a NexusAI knowledge base using Phase 3 hybrid retrieval."
    input_schema = KnowledgeSearchInput

    async def execute(self, context: ToolContext, params: KnowledgeSearchInput) -> ToolResult:
        hybrid = HybridRetriever(VectorSearchService(context.session, get_embedding_provider()), BM25Retriever(context.session))
        trace = await hybrid.search(params.knowledge_base_id, params.query)
        chunks = trace.rrf_results[: params.top_k]
        payload = {"chunks": [asdict(item) for item in chunks], "citations": [{"id": index, "chunk_id": str(item.chunk_id), "document_id": str(item.document_id), **item.source} for index, item in enumerate(chunks, 1)], "sources": [item.source for item in chunks]}
        return ToolResult(True, json.loads(json.dumps(payload, default=str)), metadata={"timings_ms": trace.timings_ms})
