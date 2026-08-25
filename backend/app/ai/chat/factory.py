from app.ai.chat.base import ChatModel
from app.ai.chat.providers.fake import FakeChatModel
from app.ai.chat.providers.openai import OpenAIChatModel
from app.core.config import settings
from app.core.exceptions import ApplicationError


def get_chat_model() -> ChatModel:
    if settings.llm_provider == "fake":
        return FakeChatModel()
    if settings.llm_provider == "openai":
        return OpenAIChatModel(settings.openai_api_key, settings.llm_model)
    raise ApplicationError("LLM_PROVIDER_UNAVAILABLE", f"Unknown LLM provider: {settings.llm_provider}", 503)
