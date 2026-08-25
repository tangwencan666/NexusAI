from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workspace import Workspace
from app.db.session import get_db
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead
from app.services.resources import ResourceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(payload: WorkspaceCreate, db: AsyncSession = Depends(get_db)) -> Workspace:
    return await ResourceService(db, Workspace, "Workspace").create(payload)


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[Workspace]:
    return await ResourceService(db, Workspace, "Workspace").list(offset=offset, limit=limit)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(workspace_id: UUID, db: AsyncSession = Depends(get_db)) -> Workspace:
    return await ResourceService(db, Workspace, "Workspace").get(workspace_id)
