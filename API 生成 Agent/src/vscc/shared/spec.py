"""内部 API 规范模型 —— 贯穿所有 Agent 的共享数据结构."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"
    UUID = "uuid"
    EMAIL = "email"


class ValidationRule(BaseModel):
    rule_type: str
    params: dict = Field(default_factory=dict)
    message: Optional[str] = None


class ApiField(BaseModel):
    name: str
    field_type: FieldType = FieldType.STRING
    required: bool = False
    nullable: bool = False
    default: Optional[object] = None
    description: Optional[str] = None
    example_value: Optional[object] = None
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    nested_fields: list["ApiField"] = Field(default_factory=list)
    parent_field: Optional[str] = None


class ApiEndpoint(BaseModel):
    path: str
    method: HttpMethod
    summary: str = ""
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    request_body: Optional[ApiField] = None
    path_params: list[ApiField] = Field(default_factory=list)
    query_params: list[ApiField] = Field(default_factory=list)
    header_params: list[ApiField] = Field(default_factory=list)
    response_body: Optional[ApiField] = None
    response_status: int = 200
    validation_rules: list[ValidationRule] = Field(default_factory=list)


class DatabaseEntity(BaseModel):
    table_name: str
    columns: list[ApiField] = Field(default_factory=list)
    primary_key: list[str] = Field(default_factory=list)
    foreign_keys: list[dict] = Field(default_factory=list)
    indexes: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class InternalApiSpec(BaseModel):
    """共享数据结构 —— 在 4 个 Agent 之间流转."""

    api_name: str = ""
    api_version: str = "1.0.0"
    base_url: str = "http://localhost:8000"
    description: Optional[str] = None

    # Agent 1 产出
    endpoints: list[ApiEndpoint] = Field(default_factory=list)
    entities: list[DatabaseEntity] = Field(default_factory=list)

    # Agent 2 产出
    sql_ddl: Optional[str] = None
    dto_models: dict[str, str] = Field(default_factory=dict)

    # Agent 3 产出
    openapi_yaml: Optional[str] = None
    openapi_json: Optional[str] = None

    # Agent 4 产出
    test_files: dict[str, str] = Field(default_factory=dict)
    test_results: Optional[str] = None

    # 追踪
    source_doc_path: Optional[str] = None
    agent_statuses: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
