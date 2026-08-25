import uuid
from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.documents.service import DocumentIntelligenceService
from app.schemas.document_intelligence import DocumentAnalyzeRequest,DocumentCompareRequest

router=APIRouter(tags=["document-intelligence"])

@router.post("/documents/{document_id}/analyze")
async def analyze(document_id:uuid.UUID,payload:DocumentAnalyzeRequest,db:AsyncSession=Depends(get_db))->dict:return await DocumentIntelligenceService(db).analyze(document_id,payload.document_type)

@router.get("/documents/{document_id}/analysis")
async def get_analysis(document_id:uuid.UUID,db:AsyncSession=Depends(get_db))->dict:return await DocumentIntelligenceService(db).get(document_id)

@router.post("/documents/compare")
async def compare(payload:DocumentCompareRequest,db:AsyncSession=Depends(get_db))->dict:return await DocumentIntelligenceService(db).compare(payload.document_a_id,payload.document_b_id)
