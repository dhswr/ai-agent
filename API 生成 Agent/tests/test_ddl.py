"""测试 SQL DDL 生成器."""

import pytest

from vscc.shared.spec import DatabaseEntity, ApiField, FieldType, ValidationRule
from vscc.agents.schema.ddl import generate_ddl, generate_all_ddl


@pytest.fixture
def users_entity() -> DatabaseEntity:
    return DatabaseEntity(
        table_name="users",
        description="用户表",
        columns=[
            ApiField(name="id", field_type=FieldType.UUID, required=True),
            ApiField(name="username", field_type=FieldType.STRING, required=True,
                     validation_rules=[ValidationRule(rule_type="max_length", params={"value": 50})]),
            ApiField(name="email", field_type=FieldType.EMAIL, required=True),
            ApiField(name="age", field_type=FieldType.INTEGER, required=False, nullable=True),
            ApiField(name="is_active", field_type=FieldType.BOOLEAN, required=True,
                     default=False),
        ],
        primary_key=["id"],
        indexes=["email", "username"],
    )


def test_generate_ddl_basic(users_entity):
    ddl = generate_ddl(users_entity)
    assert "CREATE TABLE users" in ddl
    assert "id UUID NOT NULL" in ddl
    assert "PRIMARY KEY (id)" in ddl


def test_generate_ddl_varchar_length(users_entity):
    ddl = generate_ddl(users_entity)
    # username 有 max_length=50
    assert "VARCHAR(50)" in ddl


def test_generate_ddl_default_value(users_entity):
    ddl = generate_ddl(users_entity)
    assert "DEFAULT false" in ddl


def test_generate_ddl_indexes(users_entity):
    ddl = generate_ddl(users_entity)
    assert "CREATE INDEX idx_users_email" in ddl
    assert "CREATE INDEX idx_users_username" in ddl


def test_generate_all_ddl(users_entity):
    ddl = generate_all_ddl([users_entity])
    assert "CREATE TABLE users" in ddl


def test_generate_ddl_empty_entity():
    entity = DatabaseEntity(table_name="empty_table")
    ddl = generate_ddl(entity)
    assert "CREATE TABLE empty_table" in ddl
    assert ");" in ddl
