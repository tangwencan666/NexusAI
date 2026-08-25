import re
from typing import Any

import sqlglot
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.agents.tools.base import BaseTool, ToolContext, ToolResult
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.db.session import engine


class SQLReadOnlyInput(BaseModel):
    sql: str = Field(min_length=1, max_length=20000)


class SQLReadOnlyTool(BaseTool):
    name = "sql_readonly"
    description = "Execute one validated read-only PostgreSQL SELECT query."
    input_schema = SQLReadOnlyInput
    timeout_seconds = settings.sql_tool_timeout_seconds

    @staticmethod
    def validate_sql(sql: str) -> tuple[str, set[str]]:
        try:
            expressions = sqlglot.parse(sql, read="postgres")
        except sqlglot.errors.ParseError as exc:
            raise ApplicationError("SQL_VALIDATION_FAILED", "SQL could not be parsed", 422) from exc
        if len(expressions) != 1:
            raise ApplicationError("SQL_VALIDATION_FAILED", "Exactly one SQL statement is allowed", 422)
        root = expressions[0]
        prohibited = (sqlglot.exp.Insert, sqlglot.exp.Update, sqlglot.exp.Delete, sqlglot.exp.Create, sqlglot.exp.Drop, sqlglot.exp.Alter, sqlglot.exp.Command, sqlglot.exp.Merge, sqlglot.exp.Transaction)
        if not isinstance(root, (sqlglot.exp.Select, sqlglot.exp.Union)) or any(root.find(kind) for kind in prohibited):
            raise ApplicationError("SQL_READ_ONLY_VIOLATION", "Only SELECT or WITH ... SELECT is allowed", 403)
        schemas = {table.db or "public" for table in root.find_all(sqlglot.exp.Table)}
        allowed_schemas = {x.strip() for x in settings.sql_tool_allowed_schemas.split(",") if x.strip()}
        if not schemas <= allowed_schemas:
            raise ApplicationError("SQL_SCHEMA_DENIED", "Query references a schema outside the allowlist", 403)
        allowed_tables = {x.strip() for x in settings.sql_tool_allowed_tables.split(",") if x.strip()}
        tables = {table.name for table in root.find_all(sqlglot.exp.Table)}
        if allowed_tables and not tables <= allowed_tables:
            raise ApplicationError("SQL_TABLE_DENIED", "Query references a table outside the allowlist", 403)
        return root.sql(dialect="postgres"), tables

    async def execute(self, context: ToolContext, params: SQLReadOnlyInput) -> ToolResult:
        sql, tables = self.validate_sql(params.sql)
        wrapped = f"SELECT * FROM ({sql.rstrip(';')}) AS nexusai_readonly_query LIMIT {settings.sql_tool_max_rows + 1}"
        async with engine.connect() as connection:
            async with connection.begin():
                await connection.execute(text("SET TRANSACTION READ ONLY"))
                await connection.execute(text(f"SET LOCAL statement_timeout = {int(settings.sql_tool_timeout_seconds * 1000)}"))
                result = await connection.execute(text(wrapped))
                rows = [dict(row) for row in result.mappings().all()]
        truncated = len(rows) > settings.sql_tool_max_rows
        rows = rows[: settings.sql_tool_max_rows]
        return ToolResult(True, {"columns": list(result.keys()), "rows": rows, "row_count": len(rows), "truncated": truncated}, metadata={"tables": sorted(tables), "read_only": True})


def redact_sql(sql: str) -> str:
    return re.sub(r"'(?:''|[^'])*'", "'[REDACTED]'", sql)
