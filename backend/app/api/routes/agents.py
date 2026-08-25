from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent import Agent
from app.db.session import get_db
from app.schemas.agent import AgentCreate, AgentRead
from app.services.resources import ResourceService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)) -> Agent:
    return await ResourceService(db, Agent, "Agent").create(payload)


@router.get("", response_model=list[AgentRead])
async def list_agents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[Agent]:
    return await ResourceService(db, Agent, "Agent").list(offset=offset, limit=limit)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: UUID, db: AsyncSession = Depends(get_db)) -> Agent:
    return await ResourceService(db, Agent, "Agent").get(agent_id)
