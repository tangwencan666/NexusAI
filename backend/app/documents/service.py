import time,uuid
from sqlalchemy import delete,select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ApplicationError
from app.db.models.business import DocumentAnalysis,DocumentComparison,DocumentRisk
from app.db.models.document_chunk import DocumentChunk
from app.db.models.knowledge_document import KnowledgeDocument
from app.documents.comparison import DocumentComparisonService
from app.documents.extraction import RuleBasedExtractionProvider,classify
from app.documents.risks import ContractRiskRuleEngine


class DocumentIntelligenceService:
    def __init__(self,session:AsyncSession):self.session=session
    async def text(self,document_id:uuid.UUID)->tuple[KnowledgeDocument,list[DocumentChunk],str]:
        doc=await self.session.get(KnowledgeDocument,document_id)
        if not doc:raise ApplicationError("DOCUMENT_NOT_FOUND","Document not found",404)
        chunks=list((await self.session.scalars(select(DocumentChunk).where(DocumentChunk.document_id==document_id).order_by(DocumentChunk.chunk_index))).all())
        if not chunks:raise ApplicationError("DOCUMENT_NO_CONTENT","Document has no indexed content",422)
        return doc,chunks,"\n".join(x.content for x in chunks)
    async def analyze(self,document_id:uuid.UUID,document_type:str|None=None)->dict:
        total=time.perf_counter();doc,chunks,content=await self.text(document_id);started=time.perf_counter();result=await RuleBasedExtractionProvider().extract(content,document_type or classify(content,doc.filename or ""));extract_ms=(time.perf_counter()-started)*1000
        started=time.perf_counter();page=chunks[0].chunk_metadata.get("page");risks=ContractRiskRuleEngine().evaluate(content,result.fields,page) if result.document_type=="contract" else [];risk_ms=(time.perf_counter()-started)*1000
        citations=[{"id":i,"chunk_id":str(c.id),"document_id":str(document_id),"filename":doc.original_filename or doc.filename,"page":c.chunk_metadata.get("page")} for i,c in enumerate(chunks[:5],1)]
        summary={"executive_summary":content[:600],"key_terms":[x for x in (result.fields.payment_terms,result.fields.termination_terms,result.fields.liability) if x],"important_dates":[x for x in (result.fields.effective_date,result.fields.expiration_date) if x],"key_risks":[x.title for x in risks]}
        analysis=(await self.session.scalars(select(DocumentAnalysis).where(DocumentAnalysis.document_id==document_id))).first()
        if not analysis:analysis=DocumentAnalysis(document_id=document_id,document_type=result.document_type,summary=summary,extraction=result.fields.model_dump(),citations=citations,status="completed",model_provider="rule",model_name="deterministic-v1");self.session.add(analysis);await self.session.flush()
        else:analysis.document_type=result.document_type;analysis.summary=summary;analysis.extraction=result.fields.model_dump();analysis.citations=citations
        await self.session.execute(delete(DocumentRisk).where(DocumentRisk.analysis_id==analysis.id))
        for risk in risks:self.session.add(DocumentRisk(analysis_id=analysis.id,rule_id=risk.rule_id,source="rule",severity=risk.severity,title=risk.title,description=risk.description,evidence=risk.evidence,page=risk.page,risk_metadata={}))
        await self.session.commit()
        return {"analysis_id":str(analysis.id),"document_type":result.document_type,"summary":summary,"extraction":result.fields.model_dump(),"risks":[x.model_dump() for x in risks],"citations":citations,"trace":{"extraction_ms":extract_ms,"risk_rules_ms":risk_ms,"total_ms":(time.perf_counter()-total)*1000}}
    async def get(self,document_id:uuid.UUID)->dict:
        analysis=(await self.session.scalars(select(DocumentAnalysis).where(DocumentAnalysis.document_id==document_id))).first()
        if not analysis:raise ApplicationError("DOCUMENT_ANALYSIS_NOT_FOUND","Document analysis not found",404)
        risks=list((await self.session.scalars(select(DocumentRisk).where(DocumentRisk.analysis_id==analysis.id))).all())
        return {"analysis_id":str(analysis.id),"document_type":analysis.document_type,"summary":analysis.summary,"extraction":analysis.extraction,"citations":analysis.citations,"risks":[{"id":str(x.id),"rule_id":x.rule_id,"source":x.source,"severity":x.severity,"title":x.title,"description":x.description,"evidence":x.evidence,"page":x.page} for x in risks]}
    async def compare(self,a:uuid.UUID,b:uuid.UUID)->dict:
        _,_,left=await self.text(a);_,_,right=await self.text(b);result=DocumentComparisonService().compare(left,right);item=DocumentComparison(document_a_id=a,document_b_id=b,result=result);self.session.add(item);await self.session.commit();await self.session.refresh(item);return {"comparison_id":str(item.id),**result}
