from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class StorageProvider(ABC):
    @abstractmethod
    async def save(self, key: str, chunks: AsyncIterator[bytes]) -> tuple[str, int]: ...

    @abstractmethod
    async def read(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...
