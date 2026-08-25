from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.factory import get_embedding_provider
from app.core.exceptions import ResourceNotFoundError
from app.db.models.website_crawl_job import WebsiteCrawlJob
from app.db.session import get_db
from app.schemas.crawls import CrawlJobRead
from app.schemas.documents import WebsiteCrawlRequest
from app.services.knowledge import KnowledgeService
from app.storage.factory import get_storage_provider

router = APIRouter(tags=["website-crawls"])


@router.post(
    "/knowledge-bases/{knowledge_base_id}/website-crawls",
    response_model=CrawlJobRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_crawl(
    knowledge_base_id: UUID,
    payload: WebsiteCrawlRequest,
    db: AsyncSession = Depends(get_db),
) -> WebsiteCrawlJob:
    return await KnowledgeService(
        db, get_embedding_provider(), get_storage_provider()
    ).crawl_website(knowledge_base_id, str(payload.root_url), payload.max_pages, payload.max_depth)


@router.get("/website-crawls/{job_id}", response_model=CrawlJobRead)
async def get_crawl(job_id: UUID, db: AsyncSession = Depends(get_db)) -> WebsiteCrawlJob:
    job = await db.get(WebsiteCrawlJob, job_id)
    if job is None:
        raise ResourceNotFoundError("Website crawl", job_id)
    return job
