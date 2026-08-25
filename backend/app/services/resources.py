from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.db.base import Base
from app.repositories.base import Repository

ModelT = TypeVar("ModelT", bound=Base)
CreateT = TypeVar("CreateT", bound=BaseModel)


class ResourceService(Generic[ModelT, CreateT]):
    def __init__(self, session: AsyncSession, model: type[ModelT], resource_name: str) -> None:
        self.session = session
        self.repository = Repository(session, model)
        self.resource_name = resource_name

    async def get(self, resource_id: UUID) -> ModelT:
        resource = await self.repository.get(resource_id)
        if resource is None:
            raise ResourceNotFoundError(self.resource_name, resource_id)
        return resource

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        return await self.repository.list(offset=offset, limit=limit)

    async def create(self, payload: CreateT) -> ModelT:
        resource = await self.repository.create(**payload.model_dump())
        await self.session.commit()
        return resource
