from uuid import UUID
from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.factory import get_embedding_provider
from app.db.session import get_db
from app.knowledge.retrieval.vector import VectorSearchService
from app.schemas.documents import (
    DocumentRead,
    SearchRequest,
    SearchResponse,
    URLImportRequest,
)
from app.services.knowledge import KnowledgeService
from app.storage.factory import get_storage_provider

router = APIRouter(tags=["knowledge-documents"])


def service(db: AsyncSession) -> KnowledgeService:
    return KnowledgeService(db, get_embedding_provider(), get_storage_provider())


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentRead:
    document = await service(db).upload(knowledge_base_id, file)
    return await service(db).get_document(document.id)


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents/url",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def import_url(
    knowledge_base_id: UUID, payload: URLImportRequest, db: AsyncSession = Depends(get_db)
) -> DocumentRead:
    document = await service(db).import_url(knowledge_base_id, str(payload.url))
    return await service(db).get_document(document.id)


@router.get("/knowledge-bases/{knowledge_base_id}/documents", response_model=list[DocumentRead])
async def list_documents(
    knowledge_base_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[DocumentRead]:
    return await service(db).list_documents(knowledge_base_id)


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(document_id: UUID, db: AsyncSession = Depends(get_db)) -> DocumentRead:
    return await service(db).get_document(document_id)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db)) -> Response:
    await service(db).delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/knowledge-bases/{knowledge_base_id}/search", response_model=SearchResponse)
async def search_knowledge_base(
    knowledge_base_id: UUID, payload: SearchRequest, db: AsyncSession = Depends(get_db)
) -> SearchResponse:
    hits = await VectorSearchService(db, get_embedding_provider()).search(
        knowledge_base_id, payload.query, payload.top_k
    )
    return SearchResponse(query=payload.query, results=[asdict(hit) for hit in hits])
