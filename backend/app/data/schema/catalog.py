from dataclasses import asdict, dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    description: str | None = None
    primary_key: bool = False


@dataclass(slots=True)
class TableInfo:
    schema: str
    table: str
    columns: list[ColumnInfo]
    foreign_keys: list[dict]
    description: str | None = None


class SchemaCatalog:
    def __init__(self, session: AsyncSession): self.session = session

    async def inspect(self, schemas: list[str], allowed_tables: list[str] | None = None) -> list[TableInfo]:
        rows = (await self.session.execute(text("""
            SELECT c.table_schema,c.table_name,c.column_name,c.data_type,c.is_nullable,
              obj_description((quote_ident(c.table_schema)||'.'||quote_ident(c.table_name))::regclass) table_comment,
              EXISTS(SELECT 1 FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu USING(constraint_catalog,constraint_schema,constraint_name) WHERE tc.constraint_type='PRIMARY KEY' AND tc.table_schema=c.table_schema AND tc.table_name=c.table_name AND kcu.column_name=c.column_name) is_pk
            FROM information_schema.columns c WHERE c.table_schema = ANY(:schemas)
            ORDER BY c.table_schema,c.table_name,c.ordinal_position
        """), {"schemas": schemas})).mappings().all()
        grouped: dict[tuple[str,str],TableInfo] = {}
        allowed = set(allowed_tables or [])
        for row in rows:
            if allowed and row["table_name"] not in allowed: continue
            key=(row["table_schema"],row["table_name"])
            grouped.setdefault(key,TableInfo(row["table_schema"],row["table_name"],[],[],row["table_comment"])).columns.append(ColumnInfo(row["column_name"],row["data_type"],row["is_nullable"]=="YES",primary_key=row["is_pk"]))
        fk_rows=(await self.session.execute(text("""SELECT tc.table_schema,tc.table_name,kcu.column_name,ccu.table_schema foreign_schema,ccu.table_name foreign_table,ccu.column_name foreign_column FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu USING(constraint_catalog,constraint_schema,constraint_name) JOIN information_schema.constraint_column_usage ccu USING(constraint_catalog,constraint_schema,constraint_name) WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema = ANY(:schemas)"""),{"schemas":schemas})).mappings().all()
        for row in fk_rows:
            item=grouped.get((row["table_schema"],row["table_name"]))
            if item:item.foreign_keys.append(dict(row))
        return list(grouped.values())

    @staticmethod
    def serialize(tables:list[TableInfo])->list[dict]: return [asdict(item) for item in tables]
