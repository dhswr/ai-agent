"""测试代码生成器 — 针对 Pytest 框架."""

from ...shared.spec import ApiEndpoint, InternalApiSpec, FieldType, ApiField


def _test_class_name(ep: ApiEndpoint) -> str:
    tag = ep.tags[0] if ep.tags else "Default"
    return f"Test{tag}{ep.summary.replace(' ', '')}"


def _generate_success_test(ep: ApiEndpoint) -> str:
    """生成成功响应的测试用例."""
    method = ep.method.value.lower()
    path = ep.path
    test_name = f"test_{method}_{path.strip('/').replace('/', '_').replace('{', '').replace('}', '')}_success"

    body = ""
    if ep.request_body:
        body = ',\n        json={}\n    '.format(repr(_sample_body(ep.request_body)))

    lines = [
        f"    async def {test_name}(self, client: AsyncClient):",
        f'        """测试 {ep.summary} - 成功场景."""',
        f'        response = await client.{method}(',
        f'            "{path}"',
    ]
    if body:
        lines.append(f"            {body},")
    lines.append("        )")
    lines.append(f"        assert response.status_code == {ep.response_status}")
    lines.append("")

    return "\n".join(lines)


def _generate_validation_tests(ep: ApiEndpoint) -> str:
    """为有校验规则的字段生成边界测试."""
    tests = []
    if not ep.request_body or not ep.request_body.nested_fields:
        return ""

    for field in ep.request_body.nested_fields:
        for rule in field.validation_rules:
            if rule.rule_type == "required" and field.required:
                tests.append(_missing_required_test(ep, field))
            elif rule.rule_type == "min_length":
                tests.append(_min_length_test(ep, field, rule.params.get("value", 1)))
            elif rule.rule_type == "max_length":
                tests.append(_max_length_test(ep, field, rule.params.get("value", 255)))

    return "\n".join(tests)


def _missing_required_test(ep: ApiEndpoint, field: ApiField) -> str:
    method = ep.method.value.lower()
    path = ep.path
    clean_path = path.strip('/').replace('/', '_').replace('{', '').replace('}', '')
    test_name = f"test_{method}_{clean_path}_missing_{field.name}"

    return (
        f"    async def {test_name}(self, client: AsyncClient):\n"
        f"        \"\"\"测试缺少必填字段 {field.name} 时返回 422.\"\"\"\n"
        f'        response = await client.{method}("{path}", json={{}})\n'
        f"        assert response.status_code == 422\n"
    )


def _min_length_test(ep: ApiEndpoint, field: ApiField, min_val: int) -> str:
    method = ep.method.value.lower()
    path = ep.path
    clean_path = path.strip('/').replace('/', '_').replace('{', '').replace('}', '')
    test_name = f"test_{method}_{clean_path}_{field.name}_too_short"

    too_short = "a" * max(0, min_val - 1)
    return (
        f"    async def {test_name}(self, client: AsyncClient):\n"
        f"        \"\"\"测试 {field.name} 长度不足 min_length={min_val}.\"\"\"\n"
        f'        response = await client.{method}("{path}", json={{"{field.name}": "{too_short}"}})\n'
        f"        assert response.status_code == 422\n"
    )


def _max_length_test(ep: ApiEndpoint, field: ApiField, max_val: int) -> str:
    method = ep.method.value.lower()
    path = ep.path
    clean_path = path.strip('/').replace('/', '_').replace('{', '').replace('}', '')
    test_name = f"test_{method}_{clean_path}_{field.name}_too_long"

    too_long = "a" * (max_val + 1)
    return (
        f"    async def {test_name}(self, client: AsyncClient):\n"
        f"        \"\"\"测试 {field.name} 长度超过 max_length={max_val}.\"\"\"\n"
        f'        response = await client.{method}("{path}", json={{"{field.name}": "{too_long}"}})\n'
        f"        assert response.status_code == 422\n"
    )


def _sample_body(field: ApiField) -> dict:
    """生成样例请求体."""
    if not field.nested_fields:
        return {}
    result = {}
    for nf in field.nested_fields:
        if nf.field_type == FieldType.STRING:
            result[nf.name] = nf.example_value or "string"
        elif nf.field_type == FieldType.INTEGER:
            result[nf.name] = nf.example_value or 1
        elif nf.field_type == FieldType.BOOLEAN:
            result[nf.name] = nf.example_value or True
        elif nf.field_type == FieldType.EMAIL:
            result[nf.name] = nf.example_value or "test@example.com"
        else:
            result[nf.name] = nf.example_value or "sample"
    return result


def generate_pytest(endpoints: list[ApiEndpoint], spec: InternalApiSpec) -> str:
    """为所有端点生成 Pytest 异步测试文件."""
    imports = [
        "import pytest",
        "from httpx import AsyncClient, ASGITransport",
        "",
    ]
    body_lines = []
    has_async = False

    for ep in endpoints:
        class_name = _test_class_name(ep)
        body = [
            f"@pytest.mark.asyncio",
            f"class {class_name}:",
        ]
        success = _generate_success_test(ep)
        if success.strip():
            body.append(success)
            has_async = True

        validation = _generate_validation_tests(ep)
        if validation.strip():
            body.append(validation)
            has_async = True

        body_lines.append("\n".join(body))

    if not has_async:
        return ""

    return "\n".join(imports) + "\n\n" + "\n\n".join(body_lines)


def generate_pytest_from_spec(spec: InternalApiSpec) -> dict[str, str]:
    """返回 {文件名: 内容} 的测试文件字典."""
    code = generate_pytest(spec.endpoints, spec)
    if not code:
        return {}
    return {"test_api.py": code}
