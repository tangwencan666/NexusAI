import uuid
from fastapi import APIRouter,Depends,Response,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.data.models import DataAnalysisResponse
from app.data.service import DataAnalystService,redact_connection
from app.db.models.business import DataSource
from app.db.session import get_db
from app.schemas.data import AnalyzeRequest,DataSourceCreate,DataSourceRead

router=APIRouter(prefix="/data-sources",tags=["data-analyst"])

def public(item:DataSource)->DataSourceRead:
    return DataSourceRead.model_validate(item).model_copy(update={"connection_config":redact_connection(item.connection_config)})

@router.post("",response_model=DataSourceRead,status_code=status.HTTP_201_CREATED)
async def create(payload:DataSourceCreate,db:AsyncSession=Depends(get_db))->DataSourceRead:
    item=DataSource(**payload.model_dump());db.add(item);await db.commit();await db.refresh(item);return public(item)

@router.get("",response_model=list[DataSourceRead])
async def list_sources(db:AsyncSession=Depends(get_db))->list[DataSourceRead]:return [public(x) for x in (await db.scalars(select(DataSource).order_by(DataSource.created_at.desc()))).all()]

@router.get("/{source_id}",response_model=DataSourceRead)
async def get_source(source_id:uuid.UUID,db:AsyncSession=Depends(get_db))->DataSourceRead:return public(await DataAnalystService(db).get(source_id))

@router.delete("/{source_id}",status_code=204)
async def delete_source(source_id:uuid.UUID,db:AsyncSession=Depends(get_db))->Response:
    item=await DataAnalystService(db).get(source_id);await db.delete(item);await db.commit();return Response(status_code=204)

@router.post("/{source_id}/analyze",response_model=DataAnalysisResponse)
async def analyze(source_id:uuid.UUID,payload:AnalyzeRequest,db:AsyncSession=Depends(get_db))->DataAnalysisResponse:return await DataAnalystService(db).analyze(await DataAnalystService(db).get(source_id),payload.question)
