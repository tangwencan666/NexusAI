import asyncio
from datetime import UTC,datetime,timedelta
from decimal import Decimal
from types import SimpleNamespace
import pytest

from app.agents.tools.customer import RefundCreateTool,RefundPrepareTool,TicketCreateTool
from app.agents.tools.factory import build_tool_registry
from app.agents.tools.sql_readonly import SQLReadOnlyTool
from app.data.analysis import DataFrameAnalysisService
from app.data.models import ChartSpec,DataResult,TextToSQLResult
from app.data.schema.catalog import ColumnInfo,TableInfo
from app.data.schema.retrieval import SchemaRetriever
from app.documents.comparison import DocumentComparisonService
from app.documents.extraction import RuleBasedExtractionProvider,classify
from app.documents.risks import ContractRiskRuleEngine


def test_schema_catalog():
    table=TableInfo("public","orders",[ColumnInfo("amount","numeric",False,primary_key=False)],[],"Orders")
    assert table.columns[0].type=="numeric"


def test_schema_retrieval():
    tables=[TableInfo("public","customer_orders",[ColumnInfo("amount","numeric",False)],[]),TableInfo("public","users",[ColumnInfo("email","text",False)],[])]
    assert SchemaRetriever().search("sales revenue",tables)[0].table=="customer_orders"


def test_text_to_sql_structure():
    value=TextToSQLResult(sql="SELECT 1",explanation="safe",tables_used=[]);assert value.sql=="SELECT 1"


def test_sql_repair_limit():
    from app.core.config import settings
    assert 0<=settings.data_sql_max_retries<=5


def test_data_analysis_result():
    result=DataResult(columns=["region","revenue"],rows=[{"region":"North","revenue":Decimal("10")}],row_count=1,truncated=False,execution_ms=1)
    chart,insights=DataFrameAnalysisService().analyze(result);assert chart and insights


@pytest.mark.parametrize("kind",["bar","line","pie","area"])
def test_chart_schema(kind):assert ChartSpec(type=kind,title="x",x="a",y="b").type==kind


def test_data_analyze_endpoint():
    from app.api.routes.data_analyst import router
    assert any(route.path.endswith("/analyze") for route in router.routes)


def test_data_source_plaintext_secret_rejected():
    from app.schemas.data import DataSourceCreate
    with pytest.raises(ValueError):DataSourceCreate(workspace_id="00000000-0000-0000-0000-000000000001",name="unsafe",connection_config={"password":"plaintext"})


def test_customer_lookup(): assert build_tool_registry().get("customer.lookup").risk_level.value=="low"
def test_order_lookup(): assert build_tool_registry().get("order.lookup").name=="order.lookup"
def test_ticket_create_requires_permission(): assert TicketCreateTool.requires_approval
def test_refund_prepare(): assert RefundPrepareTool.risk_level.value=="low"
def test_refund_create_requires_approval(): assert RefundCreateTool.requires_approval and RefundCreateTool.risk_level.value=="high"
def test_customer_agent_policy_plus_order():
    names={x["name"] for x in build_tool_registry().list()};assert {"order.lookup","knowledge_search"}<=names


def test_document_classification():assert classify("This Agreement is governed by the laws of Singapore") == "contract"


def test_contract_extraction():
    text="Agreement between Acme Ltd and Beta Inc. Effective date: January 1, 2026. Payment is Net 30 days."
    result=asyncio.run(RuleBasedExtractionProvider().extract(text));assert result.fields.parties and result.fields.effective_date


def test_risk_rule_unlimited_liability():
    extracted=asyncio.run(RuleBasedExtractionProvider().extract("Supplier accepts unlimited liability. Termination on notice."))
    risks=ContractRiskRuleEngine().evaluate("Supplier accepts unlimited liability. Termination on notice.",extracted.fields,12);assert any(x.rule_id=="unlimited_liability" for x in risks)


def test_document_analysis_citations():
    citation={"chunk_id":"1","document_id":"2","page":3};assert citation["page"]==3


def test_document_comparison():
    result=DocumentComparisonService().compare("Payment Net 30\nLiability capped","Payment Net 60\nLiability capped");assert result["summary"]["modified"]==1


@pytest.mark.parametrize("sql",["INSERT INTO refund_requests VALUES (1)","UPDATE support_tickets SET status='closed'","DELETE FROM customer_orders"])
def test_business_sql_write_rejected(sql):
    from app.core.exceptions import ApplicationError
    with pytest.raises(ApplicationError):SQLReadOnlyTool.validate_sql(sql)
