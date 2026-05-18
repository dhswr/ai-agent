"""REST API 路由."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from .schemas import PipelineRequest, PipelineResponse, AgentRequest, AgentResponse
from ..orchestrator.loop import RalphLoop, RalphLoopConfig

router = APIRouter()


@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(req: PipelineRequest) -> PipelineResponse:
    """执行完整 4 Agent 流水线."""
    input_path = Path(req.input_file_path)
    if not input_path.exists():
        raise HTTPException(status_code=400, detail=f"文件不存在: {req.input_file_path}")

    output_dir = Path("./output") / str(uuid.uuid4())[:8]
    config = RalphLoopConfig(
        max_iterations=req.max_iterations,
        output_dir=output_dir,
    )
    loop = RalphLoop(config)
    state = loop.run_pipeline(
        input_path=input_path,
        pipeline_stages=req.pipeline_stages,
        run_tests=req.run_tests,
        db_dialect=req.db_dialect,
    )

    spec = state.spec
    return PipelineResponse(
        run_id=output_dir.name,
        status="complete" if not spec.errors else "partial",
        api_name=spec.api_name,
        endpoints_count=len(spec.endpoints),
        entities_count=len(spec.entities),
        openapi_yaml=spec.openapi_yaml,
        sql_ddl=spec.sql_ddl,
        dto_models=spec.dto_models,
        test_files=spec.test_files,
        test_results=spec.test_results,
        errors=spec.errors,
    )


@router.post("/agent/parse-requirements", response_model=AgentResponse)
async def parse_requirements(req: AgentRequest) -> AgentResponse:
    """仅运行需求解析 Agent."""
    if not req.input_file_path:
        raise HTTPException(status_code=400, detail="需要 input_file_path")
    loop = RalphLoop()
    state = loop.run_single_agent("requirements_parser", file_path=req.input_file_path)
    return AgentResponse(
        status=state.spec.agent_statuses.get("requirements_parser", "unknown"),
        artifacts={"spec": state.spec.model_dump_json(indent=2)},
    )


@router.post("/agent/design-schema", response_model=AgentResponse)
async def design_schema(req: AgentRequest) -> AgentResponse:
    """仅运行 Schema 设计 Agent."""
    loop = RalphLoop()
    # 从之前的 spec 加载状态
    state = loop.run_single_agent("schema_designer")
    return AgentResponse(
        status=state.spec.agent_statuses.get("schema_designer", "unknown"),
        artifacts={
            "ddl": state.spec.sql_ddl or "",
            "dto_models": "\n\n".join(state.spec.dto_models.values()),
        },
    )


@router.post("/agent/generate-openapi", response_model=AgentResponse)
async def generate_openapi(req: AgentRequest) -> AgentResponse:
    """仅运行 OpenAPI 生成 Agent."""
    loop = RalphLoop()
    state = loop.run_single_agent("openapi_generator")
    return AgentResponse(
        status=state.spec.agent_statuses.get("openapi_generator", "unknown"),
        artifacts={
            "openapi_yaml": state.spec.openapi_yaml or "",
            "openapi_json": state.spec.openapi_json or "",
        },
    )


@router.get("/artifacts/{run_id}/openapi.yaml")
async def get_openapi_yaml(run_id: str) -> PlainTextResponse:
    """获取生成的 OpenAPI YAML."""
    path = Path(f"./output/{run_id}/checkpoint-001.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="run_id 不存在")
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    yaml_content = data.get("spec", {}).get("openapi_yaml", "")
    return PlainTextResponse(content=yaml_content, media_type="application/yaml")


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
