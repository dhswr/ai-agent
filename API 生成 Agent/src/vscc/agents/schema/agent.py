"""Agent 2: Schema 设计 —— 生成 SQL DDL 和 Pydantic DTO 模型."""

from ...shared.state import PipelineState
from ..base import BaseAgent
from .ddl import generate_all_ddl
from .dto import generate_dto_from_endpoints, generate_dto


class SchemaDesignAgent(BaseAgent):
    name = "schema_designer"

    def run(self, **kwargs) -> PipelineState:
        self.state.mark_agent_start(self.name)

        try:
            spec = self.state.spec

            # 从实体生成 DDL
            if spec.entities:
                spec.sql_ddl = generate_all_ddl(spec.entities)
            else:
                spec.sql_ddl = "-- 未检测到数据库实体"

            # 从端点生成 DTO
            dto_models: dict[str, str] = {}
            if spec.endpoints:
                dto_models = generate_dto_from_endpoints(spec.endpoints)

            # 也为每个实体生成 DTO
            for entity in spec.entities:
                model_name = "".join(w.title() for w in entity.table_name.split("_"))
                dto_models[model_name] = generate_dto(model_name, entity.columns)

            spec.dto_models = dto_models
            self.state.mark_agent_done(self.name)

        except Exception as e:
            self.state.mark_agent_failed(self.name, str(e))

        return self.state
