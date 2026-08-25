from abc import ABC, abstractmethod

from app.ai.chat.base import ChatModel


class QueryRewriter(ABC):
    @abstractmethod
    async def rewrite(self, query: str, conversation: list[str]) -> str: ...


class FallbackQueryRewriter(QueryRewriter):
    async def rewrite(self, query: str, conversation: list[str]) -> str:
        return query


class ChatQueryRewriter(QueryRewriter):
    def __init__(self, model: ChatModel) -> None:
        self.model = model

    async def rewrite(self, query: str, conversation: list[str]) -> str:
        if not conversation:
            return query
        try:
            context = "\n".join(conversation[-6:])
            response = await self.model.generate(
                "Rewrite the latest question as one concise standalone search query. Return only the query.",
                f"Conversation:\n{context}\n\nLatest question:\n{query}",
            )
            return response.text.strip() or query
        except Exception:
            return query
