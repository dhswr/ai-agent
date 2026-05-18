"""Typer CLI 命令."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

app = typer.Typer(name="vscc", help="智能 API 接口定义与测试生成 Agent")

PIPELINE_STAGES = [
    "requirements_parser",
    "schema_designer",
    "openapi_generator",
    "test_generator",
]


@app.command()
def parse(
    input: Annotated[Path, typer.Argument(help="PRD 文件路径 (md/txt/pdf)")],
    output: Annotated[
        Optional[Path], typer.Option("-o", help="输出 JSON 路径")
    ] = None,
):
    """仅运行需求解析 Agent，提取 API 字段和实体."""
    from ..orchestrator.loop import RalphLoop

    loop = RalphLoop()
    state = loop.run_single_agent("requirements_parser", file_path=input)
    spec = state.spec

    result = spec.model_dump_json(indent=2)
    if output:
        output.write_text(result, encoding="utf-8")
        typer.echo(f"已写入 {output}")
    else:
        typer.echo(result)

    typer.echo(f"\n端点: {len(spec.endpoints)} | 实体: {len(spec.entities)}")


@app.command()
def pipeline(
    input: Annotated[Path, typer.Argument(help="PRD 文件路径 (md/txt/pdf)")],
    stages: Annotated[
        Optional[str], typer.Option("--stages", help="逗号分隔的 Agent 名称")
    ] = None,
    framework: Annotated[str, typer.Option("--framework", help="测试框架")] = "pytest",
    dialect: Annotated[str, typer.Option("--dialect", help="SQL 方言")] = "postgresql",
    run_tests: Annotated[
        bool, typer.Option("--run-tests", help="执行生成的测试")
    ] = False,
    output_dir: Annotated[
        Optional[Path], typer.Option("-o", help="输出目录")
    ] = None,
    max_iters: Annotated[int, typer.Option("--max-iters", help="最大循环次数")] = 10,
):
    """运行完整 4 Agent 流水线."""
    from ..orchestrator.loop import RalphLoop, RalphLoopConfig

    stage_list = stages.split(",") if stages else None

    # 验证 stage 名称
    if stage_list:
        for s in stage_list:
            if s not in PIPELINE_STAGES:
                typer.echo(f"未知 Agent: {s} (可选: {', '.join(PIPELINE_STAGES)})")
                raise typer.Exit(1)

    out = output_dir or Path("./output")
    config = RalphLoopConfig(
        max_iterations=max_iters,
        output_dir=out,
        checkpoint=True,
    )
    loop = RalphLoop(config)

    typer.echo(f"开始执行流水线...")
    typer.echo(f"  输入: {input}")
    typer.echo(f"  Agent: {stage_list or PIPELINE_STAGES}")
    typer.echo(f"  输出: {out}")
    typer.echo()

    state = loop.run_pipeline(
        input_path=input,
        pipeline_stages=stage_list,
        run_tests=run_tests,
        db_dialect=dialect,
    )

    spec = state.spec

    # 写入产出文件
    if spec.openapi_yaml:
        (out / "openapi.yaml").write_text(spec.openapi_yaml, encoding="utf-8")
        typer.echo(f"[OK] OpenAPI 规范 → {out / 'openapi.yaml'}")

    if spec.openapi_json:
        (out / "openapi.json").write_text(spec.openapi_json, encoding="utf-8")

    if spec.sql_ddl:
        (out / "schema.sql").write_text(spec.sql_ddl, encoding="utf-8")
        typer.echo(f"[OK] SQL DDL → {out / 'schema.sql'}")

    if spec.dto_models:
        dto_dir = out / "dto"
        dto_dir.mkdir(parents=True, exist_ok=True)
        for name, code in spec.dto_models.items():
            (dto_dir / f"{name.lower()}.py").write_text(code, encoding="utf-8")
        typer.echo(f"[OK] DTO 模型 → {dto_dir}/ ({len(spec.dto_models)} 个)")

    if spec.test_files:
        test_dir = out / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "__init__.py").touch()
        for name, code in spec.test_files.items():
            (test_dir / name).write_text(code, encoding="utf-8")
        typer.echo(f"[OK] 测试文件 → {test_dir}/ ({len(spec.test_files)} 个)")

    if spec.errors:
        typer.echo(f"\n[警告] 错误:")
        for err in spec.errors:
            typer.echo(f"  - {err}")

    typer.echo(f"\n流水线完成! 端点: {len(spec.endpoints)} | 实体: {len(spec.entities)}")
    typer.echo(f"文件已输出到: {out}")


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8000,
):
    """启动 FastAPI REST 服务."""
    import uvicorn

    typer.echo(f"启动 VSCC API 服务 → http://{host}:{port}")
    typer.echo(f"API 文档 → http://{host}:{port}/docs")
    uvicorn.run("vscc.api.app:create_app", host=host, port=port, factory=True)
