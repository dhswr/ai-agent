"""Pydantic DTO 代码生成器."""

from ...shared.spec import ApiField, ApiEndpoint, FieldType, ValidationRule

TYPE_MAP = {
    FieldType.STRING: "str",
    FieldType.INTEGER: "int",
    FieldType.NUMBER: "float",
    FieldType.BOOLEAN: "bool",
    FieldType.DATE: "date",
    FieldType.DATETIME: "datetime",
    FieldType.UUID: "UUID",
    FieldType.EMAIL: "str",
    FieldType.ARRAY: "list",
    FieldType.OBJECT: "dict",
}

FIELD_IMPORTS = {
    FieldType.DATE: "from datetime import date",
    FieldType.DATETIME: "from datetime import datetime",
    FieldType.UUID: "from uuid import UUID",
}


def _field_def(f: ApiField, indent: str = "    ") -> str:
    python_type = TYPE_MAP.get(f.field_type, "object")
    if f.field_type == FieldType.ARRAY:
        if f.nested_fields:
            item_type = TYPE_MAP.get(f.nested_fields[0].field_type, "object")
            python_type = f"list[{item_type}]"

    parts = [f"{indent}{f.name}: {python_type}"]

    # Build Field() constraints
    constraints = []
    if f.required:
        constraints.append("...")
    else:
        constraints.append("None")
        constraints.append("default=None")

    for rule in f.validation_rules:
        if rule.rule_type == "min_length":
            constraints.append(f"min_length={rule.params.get('value', 1)}")
        elif rule.rule_type == "max_length":
            constraints.append(f"max_length={rule.params.get('value', 255)}")
        elif rule.rule_type == "min_value":
            constraints.append(f"ge={rule.params.get('value', 0)}")
        elif rule.rule_type == "max_value":
            constraints.append(f"le={rule.params.get('value', 0)}")
        elif rule.rule_type == "regex":
            constraints.append(f'pattern=r"{rule.params.get("pattern", ".*")}"')

    if f.description:
        constraints.insert(0, f'description="{f.description}"')

    if len(constraints) > 1:
        parts.append(f" = Field({', '.join(constraints)})")

    return "".join(parts)


def _needed_imports(fields: list[ApiField]) -> set[str]:
    imports = set()
    for f in fields:
        imp = FIELD_IMPORTS.get(f.field_type)
        if imp:
            imports.add(imp)
        if f.validation_rules:
            imports.add("from pydantic import BaseModel, Field")
    if not imports or not any("BaseModel" in i for i in imports):
        imports.add("from pydantic import BaseModel")
    return imports


def generate_dto(model_name: str, fields: list[ApiField]) -> str:
    """生成单个 Pydantic 模型类."""
    imports = _needed_imports(fields)
    lines = list(sorted(imports))
    lines.append("")
    lines.append(f"class {model_name}(BaseModel):")

    if not fields:
        lines.append("    pass")
        return "\n".join(lines)

    for f in fields:
        lines.append(_field_def(f))

    # 递归生成嵌套类型
    for f in fields:
        if f.nested_fields and f.field_type == FieldType.OBJECT:
            nested_name = f"{model_name}{f.name.title()}"
            lines.append("\n")
            lines.append(f"class {nested_name}(BaseModel):")
            for nf in f.nested_fields:
                lines.append(_field_def(nf))

    return "\n".join(lines)


def generate_dto_from_endpoints(endpoints: list[ApiEndpoint]) -> dict[str, str]:
    """为所有端点的 request/response body 生成 DTO."""
    models: dict[str, str] = {}
    for ep in endpoints:
        tag = ep.tags[0] if ep.tags else "Default"
        if ep.request_body and ep.request_body.nested_fields:
            model_name = f"{tag}{ep.summary.replace(' ', '')}Request"
            models[model_name] = generate_dto(model_name, ep.request_body.nested_fields)
        if ep.response_body and ep.response_body.nested_fields:
            model_name = f"{tag}{ep.summary.replace(' ', '')}Response"
            models[model_name] = generate_dto(model_name, ep.response_body.nested_fields)
    return models
