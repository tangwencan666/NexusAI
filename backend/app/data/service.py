import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import ToolContext
from app.agents.tools.sql_readonly import SQLReadOnlyTool
from app.ai.chat.factory import get_chat_model
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.data.analysis import DataFrameAnalysisService
from app.data.models import DataAnalysisResponse,DataResult
from app.data.schema.catalog import SchemaCatalog
from app.data.schema.retrieval import SchemaRetriever
from app.data.text_to_sql import TextToSQLService
from app.db.models.business import DataSource


class DataAnalystService:
    def __init__(self,session:AsyncSession):self.session=session

    async def analyze(self,source:DataSource,question:str)->DataAnalysisResponse:
        if not source.is_active:raise ApplicationError("DATA_SOURCE_INACTIVE","Data source is inactive",409)
        if source.type not in {"postgresql","demo"}:raise ApplicationError("DATA_SOURCE_UNSUPPORTED","Only PostgreSQL is supported in Phase 5",422)
        total=time.perf_counter();started=time.perf_counter()
        catalog=await SchemaCatalog(self.session).inspect(source.allowed_schemas,source.allowed_tables)
        relevant=SchemaRetriever().search(question,catalog);schema_ms=(time.perf_counter()-started)*1000
        started=time.perf_counter();generator=TextToSQLService(get_chat_model());generated=await generator.generate(question,relevant);generation_ms=(time.perf_counter()-started)*1000
        _,used=SQLReadOnlyTool.validate_sql(generated.sql)
        if source.allowed_tables and not used <= set(source.allowed_tables):raise ApplicationError("SQL_TABLE_DENIED","Generated SQL references a table outside the data source allowlist",403)
        result=None;last_error=None;sql=generated
        for attempt in range(settings.data_sql_max_retries+1):
            executed=await SQLReadOnlyTool().invoke(ToolContext(self.session),{"sql":sql.sql})
            if executed.success:result=executed;break
            last_error=executed.error
            if attempt<settings.data_sql_max_retries:sql=await generator.repair(question,relevant,sql,last_error or "unknown error")
        if not result:raise ApplicationError("DATA_SQL_EXECUTION_FAILED",last_error or "SQL execution failed",422)
        data=DataResult(columns=result.output["columns"],rows=result.output["rows"],row_count=result.output["row_count"],truncated=result.output["truncated"],execution_ms=result.duration_ms)
        started=time.perf_counter();chart,insights=DataFrameAnalysisService().analyze(data);analysis_ms=(time.perf_counter()-started)*1000
        return DataAnalysisResponse(sql=sql.sql,explanation=sql.explanation,columns=data.columns,rows=data.rows,row_count=data.row_count,truncated=data.truncated,chart=chart,insights=insights,trace={"schema_retrieval_ms":schema_ms,"sql_generation_ms":generation_ms,"sql_execution_ms":data.execution_ms,"analysis_chart_ms":analysis_ms,"total_ms":(time.perf_counter()-total)*1000,"tables_used":sql.tables_used,"repair_limit":settings.data_sql_max_retries})

    async def get(self,source_id:uuid.UUID)->DataSource:
        item=await self.session.get(DataSource,source_id)
        if not item:raise ApplicationError("DATA_SOURCE_NOT_FOUND","Data source not found",404)
        return item


def redact_connection(config:dict)->dict:
    sensitive={"password","secret","token","api_key","authorization"}
    return {key:("[REDACTED]" if key.lower() in sensitive else value) for key,value in config.items()}
