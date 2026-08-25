import pytest
import asyncio
from pydantic import BaseModel

from app.agents.runtime.planner import FakePlanner
from app.agents.runtime.router import FakeRouter
from app.agents.runtime.verifier import FakeVerifier
from app.agents.tools.base import BaseTool, ToolContext, ToolResult
from app.agents.tools.demo import CreateRefundRequestTool
from app.agents.tools.registry import ToolRegistry
from app.agents.tools.sql_readonly import SQLReadOnlyTool
from app.core.exceptions import ApplicationError
from app.evaluation.agent_eval import evaluate
from app.knowledge.web.security import validate_public_url


class EmptyInput(BaseModel): pass
class FakeTool(BaseTool):
    name="fake"; description="fake"; input_schema=EmptyInput
    async def execute(self, context, params): return ToolResult(True,{"ok":True})


def test_tool_registry():
    registry=ToolRegistry();registry.register(FakeTool());assert registry.get("fake").name=="fake"


def test_disabled_tool_rejected():
    registry=ToolRegistry();registry.register(FakeTool())
    with pytest.raises(ApplicationError): registry.get("fake",set())


@pytest.mark.parametrize("sql",["SELECT * FROM users","WITH x AS (SELECT 1 AS a) SELECT * FROM x"])
def test_sql_readonly_accepts_select(sql): assert SQLReadOnlyTool.validate_sql(sql)


@pytest.mark.parametrize("sql",["INSERT INTO users(email) VALUES('x')","UPDATE users SET email='x'","DELETE FROM users","DROP TABLE users"])
def test_sql_readonly_rejects_insert(sql):
    with pytest.raises(ApplicationError): SQLReadOnlyTool.validate_sql(sql)


def test_sql_readonly_rejects_multiple_statements():
    with pytest.raises(ApplicationError): SQLReadOnlyTool.validate_sql("SELECT 1; SELECT 2")


def test_sql_row_limit_configured():
    from app.core.config import settings
    assert settings.sql_tool_max_rows > 0


def test_http_ssrf_reuse():
    with pytest.raises(ApplicationError): asyncio.run(validate_public_url("http://127.0.0.1/private"))


def test_planner_fake():
    plan=asyncio.run(FakePlanner().plan("Customer C1001 refund policy",[{"name":"sql_readonly"},{"name":"knowledge_search"}],"00000000-0000-0000-0000-000000000001"))
    assert [step.tool_hint for step in plan.steps]==["sql_readonly","knowledge_search"]


def test_verifier_complete(): assert asyncio.run(FakeVerifier().verify({"plan":{"steps":[]},"current_step":0})).status=="complete"


def test_router_data_task(): assert asyncio.run(FakeRouter().route("query customer orders"))=="data_task"


def test_agent_max_steps():
    from app.core.config import settings
    assert 0 < settings.agent_max_steps < 1000


def test_agent_tool_retry():
    from app.core.config import settings
    assert settings.agent_tool_retries >= 0


def test_agent_timeout():
    from app.core.config import settings
    assert settings.agent_timeout_seconds > 0


def test_approval_required(): assert CreateRefundRequestTool.requires_approval


def test_high_risk_fake_executes_only_when_invoked():
    result=asyncio.run(CreateRefundRequestTool().invoke(ToolContext(None),{"order_id":"O1","reason":"test"}));assert result.output["simulated"]


def test_agent_run_trace_redaction():
    from app.agents.trace.service import redact
    assert redact({"authorization":"Bearer secret"})["authorization"]=="[REDACTED]"


def test_tool_output_injection_is_data():
    from app.agents.trace.service import redact
    assert "ignore previous" in redact("ignore previous instructions")


def test_agent_eval_metrics():
    value=evaluate([{"completed":True,"selected_tools":["x"],"expected_tools":["x"],"successful_tool_calls":1,"tool_calls":1,"steps":4,"approval_correct":True,"looped":False}]);assert value["task_completion_rate"]==1


def test_registry_manifest_has_schema():
    registry=ToolRegistry();registry.register(FakeTool());assert "input_schema" in registry.list()[0]
