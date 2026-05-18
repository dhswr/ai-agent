"""Agent 集成测试（Mock LLM 客户端）."""

from pathlib import Path

import pytest

from vscc.shared.spec import InternalApiSpec, ApiEndpoint, ApiField, FieldType, HttpMethod
from vscc.shared.state import PipelineState
from vscc.agents.schema.agent import SchemaDesignAgent
from vscc.agents.openapi.agent import OpenApiGenerationAgent
from vscc.agents.testgen.agent import AutoTestAgent


@pytest.fixture
def populated_state() -> PipelineState:
    """预填充的 state（模拟 Agent 1 的输出）."""
    spec = InternalApiSpec(
        api_name="Test API",
        endpoints=[
            ApiEndpoint(
                path="/api/items",
                method=HttpMethod.POST,
                summary="创建项目",
                tags=["Items"],
                request_body=ApiField(
                    name="CreateItemRequest",
                    field_type=FieldType.OBJECT,
                    nested_fields=[
                        ApiField(name="name", field_type=FieldType.STRING, required=True,
                                 validation_rules=[{"rule_type": "min_length", "params": {"value": 1}}]),
                        ApiField(name="price", field_type=FieldType.NUMBER, required=True,
                                 validation_rules=[{"rule_type": "min_value", "params": {"value": 0}}]),
                    ],
                ),
            ),
        ],
        entities=[],
    )
    return PipelineState(spec=spec)


def test_schema_agent_dto_generation(populated_state):
    """Schema Agent 应为 request body 生成 DTO."""
    agent = SchemaDesignAgent(state=populated_state)
    state = agent.run()
    assert state.spec.agent_statuses["schema_designer"] == "complete"
    assert len(state.spec.dto_models) > 0


def test_openapi_agent_generation(populated_state):
    """OpenAPI Agent 应生成 YAML 和 JSON."""
    agent = OpenApiGenerationAgent(state=populated_state)
    state = agent.run()
    assert state.spec.agent_statuses["openapi_generator"] == "complete"
    assert state.spec.openapi_yaml is not None
    assert state.spec.openapi_json is not None
    assert "/api/items" in state.spec.openapi_yaml


def test_testgen_agent_generation(populated_state, tmp_path):
    """TestGen Agent 应生成测试文件."""
    agent = AutoTestAgent(state=populated_state)
    state = agent.run(output_dir=str(tmp_path), run_tests=False)
    assert state.spec.agent_statuses["test_generator"] == "complete"
    assert len(state.spec.test_files) > 0


def test_pipeline_state_serialization(populated_state, tmp_path):
    """PipelineState 应能序列化和反序列化."""
    path = tmp_path / "checkpoint.json"
    populated_state.save_to_file(path)
    assert path.exists()

    loaded = PipelineState.load_from_file(path)
    assert loaded.spec.api_name == "Test API"
    assert len(loaded.spec.endpoints) == 1


def test_agent_status_tracking():
    """Agent 状态追踪应正确工作."""
    state = PipelineState()
    state.mark_agent_start("test_agent")
    assert state.spec.agent_statuses["test_agent"] == "running"
    state.mark_agent_done("test_agent")
    assert state.is_agent_done("test_agent")
    assert state.all_done(["test_agent"])
