"""Ralph Loop 多轮编排器 —— 串联 4 个 Agent 执行流水线."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from anthropic import Anthropic

from ..config import settings
from ..shared.state import PipelineState
from ..shared.io import ensure_dir
from ..agents.base import BaseAgent
from ..agents.requirements.agent import RequirementsParsingAgent
from ..agents.schema.agent import SchemaDesignAgent
from ..agents.openapi.agent import OpenApiGenerationAgent
from ..agents.testgen.agent import AutoTestAgent

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "requirements_parser": RequirementsParsingAgent,
    "schema_designer": SchemaDesignAgent,
    "openapi_generator": OpenApiGenerationAgent,
    "test_generator": AutoTestAgent,
}

PIPELINE_ORDER = [
    "requirements_parser",
    "schema_designer",
    "openapi_generator",
    "test_generator",
]


@dataclass
class RalphLoopConfig:
    max_iterations: int = 10
    max_session_usage_pct: int = 80
    logs_dir: Optional[Path] = None
    checkpoint: bool = True
    output_dir: Path = field(default_factory=lambda: Path("./output"))


class RalphLoop:
    """多轮自主编排器，按依赖顺序执行各 Agent."""

    def __init__(self, config: Optional[RalphLoopConfig] = None):
        self.config = config or RalphLoopConfig()
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def run_pipeline(
        self,
        input_path: Path | str,
        pipeline_stages: Optional[list[str]] = None,
        run_tests: bool = False,
        db_dialect: str = "postgresql",
    ) -> PipelineState:
        """执行完整流水线，返回最终 state."""
        input_path = Path(input_path)
        stages = pipeline_stages or PIPELINE_ORDER
        state = PipelineState(max_iterations=self.config.max_iterations)

        ensure_dir(self.config.output_dir)

        for iteration in range(1, self.config.max_iterations + 1):
            state.iteration = iteration

            for stage in stages:
                if state.is_agent_done(stage):
                    continue

                agent_cls = AGENT_REGISTRY.get(stage)
                if agent_cls is None:
                    state.mark_agent_failed(stage, f"未知 Agent: {stage}")
                    continue

                agent = agent_cls(client=self.client, state=state)

                # Agent 1 需要文件路径
                if stage == "requirements_parser":
                    state = agent.run(file_path=input_path)
                # Agent 4 需要输出目录和 run_tests 标志
                elif stage == "test_generator":
                    test_output = self.config.output_dir / "tests"
                    state = agent.run(output_dir=str(test_output), run_tests=run_tests)
                else:
                    state = agent.run()

                # 检查 Agent 是否失败
                if stage in state.spec.agent_statuses and state.spec.agent_statuses[stage] == "failed":
                    # 前序 Agent 失败则中断后续
                    break

            # 检查是否全部完成
            if state.all_done(stages):
                break

            # 保存检查点
            if self.config.checkpoint:
                checkpoint_path = self.config.output_dir / f"checkpoint-{iteration:03d}.json"
                state.save_to_file(checkpoint_path)

        return state

    def run_single_agent(self, agent_name: str, **kwargs) -> PipelineState:
        """单独运行一个 Agent."""
        agent_cls = AGENT_REGISTRY.get(agent_name)
        if agent_cls is None:
            raise ValueError(f"Unknown agent: {agent_name}")

        state = PipelineState()
        agent = agent_cls(client=self.client, state=state)
        return agent.run(**kwargs)
