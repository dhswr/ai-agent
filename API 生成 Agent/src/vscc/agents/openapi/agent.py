"""Agent 3: OpenAPI 生成 —— 从内部规范生成 OpenAPI 3.x 文档."""

from ...shared.state import PipelineState
from ..base import BaseAgent
from .generator import build_openapi_spec, serialize_yaml, serialize_json


class OpenApiGenerationAgent(BaseAgent):
    name = "openapi_generator"

    def run(self, **kwargs) -> PipelineState:
        self.state.mark_agent_start(self.name)

        try:
            spec = self.state.spec
            openapi_dict = build_openapi_spec(spec)

            # 用 LLM 补充描述和示例（如果有的话）
            if spec.endpoints:
                self._enrich_with_llm(openapi_dict)

            spec.openapi_yaml = serialize_yaml(openapi_dict)
            spec.openapi_json = serialize_json(openapi_dict)
            self.state.mark_agent_done(self.name)

        except Exception as e:
            self.state.mark_agent_failed(self.name, str(e))

        return self.state

    def _enrich_with_llm(self, openapi_dict: dict) -> None:
        """可选: 用 LLM 为缺少描述的端点补充描述和示例."""
        # MVP: 跳过 LLM 增强，保持纯模板输出
        _ = openapi_dict
        return
