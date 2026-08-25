from app.core.config import settings
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider


def get_storage_provider() -> StorageProvider:
    return LocalStorageProvider(settings.upload_directory)
