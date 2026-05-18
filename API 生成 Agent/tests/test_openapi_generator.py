"""测试 OpenAPI 生成器."""

import pytest

from vscc.shared.spec import (
    InternalApiSpec,
    ApiEndpoint,
    ApiField,
    FieldType,
    HttpMethod,
    ValidationRule,
)
from vscc.agents.openapi.generator import build_openapi_spec, serialize_yaml, serialize_json


@pytest.fixture
def sample_spec() -> InternalApiSpec:
    return InternalApiSpec(
        api_name="Test API",
        api_version="1.0.0",
        base_url="http://localhost:8000",
        description="A test API",
        endpoints=[
            ApiEndpoint(
                path="/api/users",
                method=HttpMethod.GET,
                summary="获取用户列表",
                description="分页获取用户列表",
                tags=["Users"],
                query_params=[
                    ApiField(
                        name="page",
                        field_type=FieldType.INTEGER,
                        required=False,
                        description="页码",
                        default=1,
                    ),
                    ApiField(
                        name="size",
                        field_type=FieldType.INTEGER,
                        required=False,
                        description="每页数量",
                        default=20,
                        validation_rules=[ValidationRule(rule_type="max_value", params={"value": 100})],
                    ),
                ],
                response_body=ApiField(
                    name="UserList",
                    field_type=FieldType.OBJECT,
                    nested_fields=[
                        ApiField(name="total", field_type=FieldType.INTEGER, required=True),
                    ],
                ),
            ),
        ],
        dto_models={"UserResponse": "class UserResponse(BaseModel): ..."},
    )


def test_build_openapi_basic(sample_spec):
    doc = build_openapi_spec(sample_spec)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Test API"
    assert doc["info"]["version"] == "1.0.0"
    assert len(doc["servers"]) == 1


def test_build_openapi_paths(sample_spec):
    doc = build_openapi_spec(sample_spec)
    assert "/api/users" in doc["paths"]
    assert "get" in doc["paths"]["/api/users"]
    op = doc["paths"]["/api/users"]["get"]
    assert op["summary"] == "获取用户列表"


def test_build_openapi_params(sample_spec):
    doc = build_openapi_spec(sample_spec)
    op = doc["paths"]["/api/users"]["get"]
    assert "parameters" in op
    param_names = [p["name"] for p in op["parameters"]]
    assert "page" in param_names
    assert "size" in param_names


def test_build_openapi_components(sample_spec):
    doc = build_openapi_spec(sample_spec)
    assert "components" in doc
    assert "schemas" in doc["components"]
    assert "UserResponse" in doc["components"]["schemas"]


def test_serialize_yaml(sample_spec):
    doc = build_openapi_spec(sample_spec)
    yaml_str = serialize_yaml(doc)
    assert "openapi: 3.1.0" in yaml_str or "openapi: '3.1.0'" in yaml_str or 'openapi: "3.1.0"' in yaml_str
    assert "Test API" in yaml_str


def test_serialize_json(sample_spec):
    doc = build_openapi_spec(sample_spec)
    json_str = serialize_json(doc)
    assert '"openapi"' in json_str
    assert '"Test API"' in json_str
