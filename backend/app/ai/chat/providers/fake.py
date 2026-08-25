from collections.abc import AsyncIterator

from app.ai.chat.base import ChatModel, ChatResponse


class FakeChatModel(ChatModel):
    async def generate(self, system_prompt: str, user_prompt: str) -> ChatResponse:
        source_count = user_prompt.count("[SOURCE ")
        text = "Based on the retrieved evidence, the requested policy is described in the supplied context"
        if source_count:
            text += " [1]."
        else:
            text = "There is not enough evidence in the knowledge base to answer this question."
        return ChatResponse(text, len(user_prompt) // 4, len(text) // 4)

    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        response = await self.generate(system_prompt, user_prompt)
        for token in response.text.split(" "):
            yield token + " "
