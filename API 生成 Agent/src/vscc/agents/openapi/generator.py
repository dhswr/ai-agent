"""OpenAPI 3.1 规范构建器 —— 模板驱动，确定性生成."""

import json
from typing import Any

import yaml

from ...shared.spec import InternalApiSpec, ApiEndpoint, ApiField, FieldType, HttpMethod

OPENAPI_TYPE_MAP = {
    FieldType.STRING: "string",
    FieldType.INTEGER: "integer",
    FieldType.NUMBER: "number",
    FieldType.BOOLEAN: "boolean",
    FieldType.ARRAY: "array",
    FieldType.OBJECT: "object",
    FieldType.DATE: "string",
    FieldType.DATETIME: "string",
    FieldType.UUID: "string",
    FieldType.EMAIL: "string",
}

OPENAPI_FORMAT_MAP = {
    FieldType.DATE: "date",
    FieldType.DATETIME: "date-time",
    FieldType.UUID: "uuid",
    FieldType.EMAIL: "email",
}


def _field_to_schema(field: ApiField) -> dict[str, Any]:
    schema: dict[str, Any] = {}
    oa_type = OPENAPI_TYPE_MAP.get(field.field_type, "string")
    schema["type"] = oa_type
    fmt = OPENAPI_FORMAT_MAP.get(field.field_type)
    if fmt:
        schema["format"] = fmt
    if field.description:
        schema["description"] = field.description
    if field.example_value is not None:
        schema["example"] = field.example_value
    if field.nullable:
        schema["nullable"] = True

    # Nested fields for objects
    if field.field_type == FieldType.OBJECT and field.nested_fields:
        schema["properties"] = {}
        required = []
        for nf in field.nested_fields:
            schema["properties"][nf.name] = _field_to_schema(nf)
            if nf.required:
                required.append(nf.name)
        if required:
            schema["required"] = required

    # Items for arrays
    if field.field_type == FieldType.ARRAY and field.nested_fields:
        schema["items"] = _field_to_schema(field.nested_fields[0])

    # Validation
    for rule in field.validation_rules:
        if rule.rule_type == "min_length":
            schema["minLength"] = rule.params.get("value", 1)
        elif rule.rule_type == "max_length":
            schema["maxLength"] = rule.params.get("value", 255)
        elif rule.rule_type == "min_value":
            schema["minimum"] = rule.params.get("value", 0)
        elif rule.rule_type == "max_value":
            schema["maximum"] = rule.params.get("value", 0)
        elif rule.rule_type == "regex":
            schema["pattern"] = rule.params.get("pattern", ".*")

    return schema


def _params_schema(params: list[ApiField]) -> list[dict[str, Any]]:
    result = []
    for p in params:
        ps: dict[str, Any] = {
            "name": p.name,
            "in": "path" if "path" in str(p.parent_field or "") else "query",
            "required": p.required,
            "schema": _field_to_schema(p),
        }
        if p.description:
            ps["description"] = p.description
        result.append(ps)
    return result


def _endpoint_to_operation(ep: ApiEndpoint) -> dict[str, Any]:
    op: dict[str, Any] = {
        "summary": ep.summary,
        "operationId": f"{ep.method.value.lower()}{ep.path.strip('/').replace('/', '_').replace('{', '').replace('}', '')}",
        "responses": {
            str(ep.response_status): {"description": "Successful response"}
        },
    }
    if ep.description:
        op["description"] = ep.description
    if ep.tags:
        op["tags"] = ep.tags

    # Parameters
    all_params = []
    path_fields = [p for p in ep.path_params]
    query_fields = [p for p in ep.query_params]
    if path_fields:
        for p in path_fields:
            ps = _params_schema([p])[0]
            ps["in"] = "path"
            all_params.append(ps)
    if query_fields:
        for p in query_fields:
            ps = _params_schema([p])[0]
            ps["in"] = "query"
            all_params.append(ps)
    if all_params:
        op["parameters"] = all_params

    # Request body
    if ep.request_body and ep.request_body.nested_fields:
        req_schema = _field_to_schema(ep.request_body)
        op["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": req_schema}},
        }

    # Response body
    if ep.response_body and ep.response_body.nested_fields:
        resp_schema = _field_to_schema(ep.response_body)
        op["responses"][str(ep.response_status)]["content"] = {
            "application/json": {"schema": resp_schema}
        }

    return op


def build_openapi_spec(spec: InternalApiSpec) -> dict[str, Any]:
    """从 InternalApiSpec 构建完整 OpenAPI 3.1 文档."""
    paths: dict[str, dict[str, Any]] = {}
    for ep in spec.endpoints:
        method = ep.method.value.lower()
        if ep.path not in paths:
            paths[ep.path] = {}
        paths[ep.path][method] = _endpoint_to_operation(ep)

    # Build schemas from DTOs
    schemas: dict[str, Any] = {}
    for model_name, _ in spec.dto_models.items():
        schemas[model_name] = {"type": "object", "description": f"{model_name} DTO"}

    doc: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": spec.api_name or "API",
            "version": spec.api_version,
        },
        "servers": [{"url": spec.base_url}],
        "paths": paths,
    }

    if spec.description:
        doc["info"]["description"] = spec.description

    if schemas:
        doc["components"] = {"schemas": schemas}

    return doc


def serialize_yaml(spec_dict: dict[str, Any]) -> str:
    return yaml.dump(spec_dict, allow_unicode=True, sort_keys=False, default_flow_style=False)


def serialize_json(spec_dict: dict[str, Any]) -> str:
    return json.dumps(spec_dict, ensure_ascii=False, indent=2)
