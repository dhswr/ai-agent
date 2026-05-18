"""SQL DDL 生成器 —— 模板驱动，确定性生成."""

from ...shared.spec import DatabaseEntity, ApiField, FieldType

TYPE_MAPPING = {
    FieldType.STRING: "VARCHAR",
    FieldType.INTEGER: "INTEGER",
    FieldType.NUMBER: "NUMERIC",
    FieldType.BOOLEAN: "BOOLEAN",
    FieldType.DATE: "DATE",
    FieldType.DATETIME: "TIMESTAMPTZ",
    FieldType.UUID: "UUID",
    FieldType.EMAIL: "VARCHAR(320)",
    FieldType.ARRAY: "JSONB",
    FieldType.OBJECT: "JSONB",
}


def _column_def(col: ApiField) -> str:
    type_sql = TYPE_MAPPING.get(col.field_type, "VARCHAR")
    # 对于 STRING 且没有特殊映射的，加长度
    if col.field_type == FieldType.STRING and "VARCHAR" in type_sql and "(" not in type_sql:
        type_sql = "VARCHAR(255)"

    parts = [f"  {col.name} {type_sql}"]
    if col.required:
        parts.append("NOT NULL")
    if col.nullable and not col.required:
        parts.append("NULL")
    else:
        pass  # NOT NULL already added

    if col.default is not None:
        default_val = col.default
        if isinstance(default_val, bool):
            parts.append(f"DEFAULT {'true' if default_val else 'false'}")
        elif isinstance(default_val, str):
            parts.append(f"DEFAULT '{default_val}'")
        else:
            parts.append(f"DEFAULT {default_val}")

    for rule in col.validation_rules:
        if rule.rule_type == "max_length":
            length = rule.params.get("value", 255)
            # replace existing VARCHAR(N) if present
            parts[0] = f"  {col.name} VARCHAR({length})"

    return " ".join(parts)


def generate_ddl(entity: DatabaseEntity, dialect: str = "postgresql") -> str:
    """从 DatabaseEntity 生成 CREATE TABLE 语句."""
    lines = [f"-- Table: {entity.table_name}"]
    if entity.description:
        lines.append(f"-- {entity.description}")
    lines.append(f"CREATE TABLE {entity.table_name} (")

    col_defs = [_column_def(c) for c in entity.columns]
    lines.append(",\n".join(col_defs))

    if entity.primary_key:
        pk_cols = ", ".join(entity.primary_key)
        lines.append(f",\n  PRIMARY KEY ({pk_cols})")

    for fk in entity.foreign_keys:
        col = fk.get("column", "")
        ref_table = fk.get("ref_table", "")
        ref_col = fk.get("ref_column", "id")
        lines.append(f",\n  FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})")

    lines.append("\n);")

    # Indexes
    for idx in entity.indexes:
        lines.append(f"\nCREATE INDEX idx_{entity.table_name}_{idx.replace(', ', '_')} "
                     f"ON {entity.table_name}({idx});")

    return "\n".join(lines)


def generate_all_ddl(entities: list[DatabaseEntity], dialect: str = "postgresql") -> str:
    return "\n\n".join(generate_ddl(e, dialect) for e in entities)
