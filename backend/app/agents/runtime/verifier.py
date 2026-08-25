from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel, Field


class Verification(BaseModel):
    status: Literal["complete", "continue", "replan", "fail"]
    reason: str
    missing_information: list[str] = Field(default_factory=list)


class Verifier(ABC):
    @abstractmethod
    async def verify(self, state: dict) -> Verification: ...


class FakeVerifier(Verifier):
    async def verify(self, state: dict) -> Verification:
        if state.get("error"):
            return Verification(status="fail", reason=state["error"])
        if state.get("current_step", 0) < len(state.get("plan", {}).get("steps", [])):
            return Verification(status="continue", reason="The plan still has executable steps")
        return Verification(status="complete", reason="All planned steps completed with recorded observations")
