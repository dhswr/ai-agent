"""流水线状态 —— Agent 间通信的共享状态对象."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .spec import InternalApiSpec


@dataclass
class PipelineState:
    spec: InternalApiSpec = field(default_factory=InternalApiSpec)
    work_dir: Path = field(default_factory=Path.cwd)
    iteration: int = 0
    max_iterations: int = 10
    started_at: str = ""

    def __post_init__(self) -> None:
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

    def mark_agent_start(self, agent_name: str) -> None:
        self.spec.agent_statuses[agent_name] = "running"

    def mark_agent_done(self, agent_name: str) -> None:
        self.spec.agent_statuses[agent_name] = "complete"

    def mark_agent_failed(self, agent_name: str, error: str) -> None:
        self.spec.agent_statuses[agent_name] = "failed"
        self.spec.errors.append(f"[{agent_name}] {error}")

    def is_agent_done(self, agent_name: str) -> bool:
        return self.spec.agent_statuses.get(agent_name) in ("complete", "failed")

    def all_done(self, agent_names: list[str]) -> bool:
        return all(self.is_agent_done(a) for a in agent_names)

    def save_to_file(self, path: Path) -> None:
        data = {
            "spec": self.spec.model_dump(),
            "iteration": self.iteration,
            "started_at": self.started_at,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load_from_file(cls, path: Path) -> PipelineState:
        data = json.loads(path.read_text(encoding="utf-8"))
        spec = InternalApiSpec(**data["spec"])
        return cls(
            spec=spec,
            iteration=data.get("iteration", 0),
            started_at=data.get("started_at", ""),
        )
