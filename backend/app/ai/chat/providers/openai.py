from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.ai.chat.base import ChatModel, ChatResponse
from app.core.exceptions import ApplicationError


class OpenAIChatModel(ChatModel):
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise ApplicationError("LLM_PROVIDER_UNAVAILABLE", "OPENAI_API_KEY is not configured", 503)
        return AsyncOpenAI(api_key=self.api_key)

    async def generate(self, system_prompt: str, user_prompt: str) -> ChatResponse:
        try:
            result = await self.client().responses.create(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
            )
            usage = result.usage
            return ChatResponse(
                result.output_text,
                getattr(usage, "input_tokens", None),
                getattr(usage, "output_tokens", None),
            )
        except ApplicationError:
            raise
        except Exception as exc:
            raise ApplicationError("LLM_GENERATION_FAILED", "OpenAI generation failed", 502) from exc

    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        try:
            async with self.client().responses.stream(
                model=self.model, instructions=system_prompt, input=user_prompt
            ) as stream:
                async for event in stream:
                    if event.type == "response.output_text.delta":
                        yield event.delta
        except ApplicationError:
            raise
        except Exception as exc:
            raise ApplicationError("STREAM_INTERRUPTED", "OpenAI stream interrupted", 502) from exc
