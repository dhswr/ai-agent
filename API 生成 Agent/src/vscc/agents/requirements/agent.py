"""Agent 1: 需求解析 —— 从 PRD 文档提取 API 端点和实体定义."""

from __future__ import annotations

import json
from pathlib import Path

from ..base import BaseAgent
from ...shared.spec import InternalApiSpec
from ...shared.state import PipelineState
from .parsers import detect_and_parse

EXTRACTION_SYSTEM_PROMPT = """你是一个需求分析专家。从给定的 PRD 文档中提取 API 接口定义和数据库实体。

对于每个 API 端点，提取:
- path: 接口路径 (如 /api/users/{id})
- method: HTTP 方法 (GET/POST/PUT/DELETE/PATCH)
- summary: 简要说明
- description: 详细描述
- request_body: 请求体字段 (名称、类型、是否必填、校验规则)
- path_params: 路径参数
- query_params: 查询参数
- response_body: 响应体字段
- tags: 标签分类

对于数据库实体:
- table_name: 表名
- columns: 列定义 (名称、类型、约束)
- primary_key: 主键列

请以 JSON 格式输出，结构为:
{
  "api_name": "应用名称",
  "endpoints": [...],
  "entities": [...]
}

字段类型必须为以下之一: string, integer, number, boolean, array, object, date, datetime, uuid, email"""


class RequirementsParsingAgent(BaseAgent):
    name = "requirements_parser"

    def run(self, *, file_path: Path | str, **kwargs) -> PipelineState:
        file_path = Path(file_path)
        self.state.mark_agent_start(self.name)
        self.state.spec.source_doc_path = str(file_path)

        try:
            raw_text = detect_and_parse(file_path)
            structured = self._extract_with_llm(raw_text)
            spec = self._apply_to_spec(structured)
            self.state.spec = spec
            self.state.mark_agent_done(self.name)
        except Exception as e:
            self.state.mark_agent_failed(self.name, str(e))

        return self.state

    def _extract_with_llm(self, raw_text: str) -> dict:
        response = self._llm_chat(EXTRACTION_SYSTEM_PROMPT, raw_text, max_tokens=8192)
        # 尝试从 LLM 响应中提取 JSON
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> dict:
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        # 尝试提取 ```json ... ``` 块
        if "```json" in response:
            block = response.split("```json")[1].split("```")[0]
            return json.loads(block)
        if "```" in response:
            block = response.split("```")[1].split("```")[0]
            return json.loads(block)
        raise ValueError(f"无法从 LLM 响应中提取 JSON: {response[:500]}")

    def _apply_to_spec(self, data: dict) -> InternalApiSpec:
        spec = InternalApiSpec(
            api_name=data.get("api_name", ""),
            description=data.get("description"),
            base_url=data.get("base_url", "http://localhost:8000"),
            endpoints=data.get("endpoints", []),
            entities=data.get("entities", []),
        )
        return spec
