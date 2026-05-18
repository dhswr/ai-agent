"""Agent 基类."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from anthropic import Anthropic

from ..config import settings
from ..shared.state import PipelineState


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, client: Optional[Anthropic] = None, state: Optional[PipelineState] = None):
        self.client = client or Anthropic(api_key=settings.anthropic_api_key)
        self.state = state or PipelineState()

    @abstractmethod
    def run(self, **kwargs) -> PipelineState:
        """执行此 Agent，返回更新后的 state."""
        ...

    def _llm_chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        msg = self.client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        block = msg.content[0]
        return block.text if hasattr(block, "text") else str(block)
