from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
import json
from typing import TypeVar
from pydantic import BaseModel

StructuredT = TypeVar("StructuredT", bound=BaseModel)


@dataclass(slots=True)
class ChatResponse:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class ChatModel(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> ChatResponse: ...

    @abstractmethod
    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        if False:
            yield ""

    async def generate_structured(self, system_prompt: str, user_prompt: str, schema: type[StructuredT]) -> StructuredT:
        response = await self.generate(system_prompt + "\nReturn only valid JSON matching this schema:\n" + json.dumps(schema.model_json_schema()), user_prompt)
        try:
            return schema.model_validate_json(response.text)
        except Exception as exc:
            from app.core.exceptions import ApplicationError
            raise ApplicationError("LLM_STRUCTURED_OUTPUT_INVALID", "Model returned invalid structured output", 502) from exc
