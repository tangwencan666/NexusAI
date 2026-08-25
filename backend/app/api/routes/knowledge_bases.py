from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_base import KnowledgeBase
from app.db.session import get_db
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead
from app.services.resources import ResourceService

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)
) -> KnowledgeBase:
    return await ResourceService(db, KnowledgeBase, "Knowledge base").create(payload)


@router.get("", response_model=list[KnowledgeBaseRead])
async def list_knowledge_bases(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeBase]:
    return await ResourceService(db, KnowledgeBase, "Knowledge base").list(
        offset=offset, limit=limit
    )
