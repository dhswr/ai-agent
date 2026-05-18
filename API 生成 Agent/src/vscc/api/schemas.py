"""REST API 请求/响应模型."""

from typing import Optional

from pydantic import BaseModel


class PipelineRequest(BaseModel):
    input_file_path: str
    pipeline_stages: Optional[list[str]] = None
    framework: str = "pytest"
    db_dialect: str = "postgresql"
    run_tests: bool = False
    max_iterations: int = 10


class PipelineResponse(BaseModel):
    run_id: str
    status: str
    api_name: Optional[str] = None
    endpoints_count: int = 0
    entities_count: int = 0
    openapi_yaml: Optional[str] = None
    sql_ddl: Optional[str] = None
    dto_models: dict[str, str] = {}
    test_files: dict[str, str] = {}
    test_results: Optional[str] = None
    errors: list[str] = []


class AgentRequest(BaseModel):
    spec_json: Optional[str] = None
    input_file_path: Optional[str] = None
    output_dir: Optional[str] = "./output"


class AgentResponse(BaseModel):
    status: str
    message: str = ""
    artifacts: dict[str, str] = {}
