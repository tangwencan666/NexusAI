import asyncio,os,uuid
from types import SimpleNamespace
import pytest
from sqlalchemy import delete
from app.agents.tools.base import ToolContext
from app.agents.tools.customer import CustomerLookupTool,OrderLookupTool,RefundPrepareTool
from app.ai.embeddings.providers.fake import FakeEmbeddingProvider
from app.core.config import settings
from app.data.service import DataAnalystService
from app.db.models.document_chunk import DocumentChunk
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.knowledge_document import DocumentSourceType,DocumentStatus,KnowledgeDocument
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.session import AsyncSessionLocal,engine
from app.documents.service import DocumentIntelligenceService

pytestmark=[pytest.mark.integration,pytest.mark.skipif(os.getenv("RUN_INTEGRATION")!="1",reason="set RUN_INTEGRATION=1")]

def test_phase5_business_apps_real_postgres():
    async def execute():
        settings.embedding_provider="fake"
        async with AsyncSessionLocal() as session:
            source=SimpleNamespace(is_active=True,type="demo",allowed_schemas=["public"],allowed_tables=[])
            data=await DataAnalystService(session).analyze(source,"Which three regions grew fastest this year, and show monthly revenue for them?")
            assert data.row_count>0 and data.chart and data.chart.x=="month"
            customer=await CustomerLookupTool().invoke(ToolContext(session),{"customer_code":"C1001"});orders=await OrderLookupTool().invoke(ToolContext(session),{"customer_code":"C1001"});prepared=await RefundPrepareTool().invoke(ToolContext(session),{"order_code":"O10001"})
            assert customer.success and orders.success and prepared.output["eligible"]
            marker=uuid.uuid4().hex[:8];user=User(email=f"integration-{marker}@test.local",username=f"integration-{marker}");session.add(user);await session.flush();workspace=Workspace(name=marker,owner_id=user.id);session.add(workspace);await session.flush();kb=KnowledgeBase(workspace_id=workspace.id,name=marker);session.add(kb);await session.flush();doc=KnowledgeDocument(knowledge_base_id=kb.id,source_type=DocumentSourceType.FILE,filename="contract.txt",status=DocumentStatus.READY,document_metadata={});session.add(doc);await session.flush();content="Agreement between Acme Ltd and Beta Inc. Supplier accepts unlimited liability.";embedding=await FakeEmbeddingProvider(1536).embed_text(content);session.add(DocumentChunk(document_id=doc.id,knowledge_base_id=kb.id,chunk_index=0,content=content,token_count=10,chunk_metadata={"page":1},embedding=embedding));await session.commit()
            analysis=await DocumentIntelligenceService(session).analyze(doc.id);assert analysis["citations"] and any(x["rule_id"]=="unlimited_liability" for x in analysis["risks"])
            await session.execute(delete(User).where(User.id==user.id));await session.commit()
        await engine.dispose()
    asyncio.run(execute(),loop_factory=asyncio.SelectorEventLoop)
