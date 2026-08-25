import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runtime.planner import FakePlanner, Planner
from app.agents.runtime.router import FakeRouter, Router
from app.agents.runtime.state import AgentState
from app.agents.runtime.verifier import FakeVerifier, Verifier
from app.agents.tools.base import ToolContext
from app.agents.tools.registry import ToolRegistry
from app.agents.trace.service import redact
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.db.models.agent_runtime import AgentApprovalRequest, AgentRun, AgentRunStatus, AgentRunStep, ApprovalStatus


class AgentRuntime:
    def __init__(self, session: AsyncSession, registry: ToolRegistry, planner: Planner | None = None, router: Router | None = None, verifier: Verifier | None = None) -> None:
        self.session = session
        self.registry = registry
        self.planner = planner or FakePlanner()
        self.router = router or FakeRouter()
        self.verifier = verifier or FakeVerifier()
        self.graph = self._build_graph()

    async def _trace(self, state: AgentState, node: str, started: float, input_data: dict, output: dict, status: str = "completed") -> None:
        self.session.add(AgentRunStep(agent_run_id=uuid.UUID(state["run_id"]), step_index=state.get("step_count", 0), node=node, status=status, input=redact(input_data), output=redact(output), duration_ms=(time.perf_counter() - started) * 1000))
        await self.session.flush()

    async def bootstrap_node(self, state: AgentState) -> dict:
        return {}

    async def router_node(self, state: AgentState) -> dict:
        started = time.perf_counter(); route = await self.router.route(state["user_request"])
        output = {"route": route, "status": "planning", "step_count": state.get("step_count", 0) + 1}
        await self._trace(state, "router", started, {"request": state["user_request"]}, output)
        return output

    async def planner_node(self, state: AgentState) -> dict:
        started = time.perf_counter()
        plan = await self.planner.plan(state["user_request"], self.registry.enabled_tools(set(state["enabled_tools"])), state.get("knowledge_base_id"))
        output = {"plan": plan.model_dump(mode="json"), "current_step": 0, "status": "running", "step_count": state.get("step_count", 0) + 1}
        await self._trace(state, "planner", started, {"route": state.get("route")}, output)
        return output

    async def executor_node(self, state: AgentState) -> dict:
        started = time.perf_counter(); index = state.get("current_step", 0); steps = state["plan"]["steps"]
        if index >= len(steps):
            return {}
        step = steps[index]; tool_name = step.get("tool_hint")
        if not tool_name:
            output = {"current_step": index + 1, "completed_steps": state.get("completed_steps", []) + [step], "observations": state.get("observations", []) + ["Direct response step completed."], "step_count": state.get("step_count", 0) + 1}
            await self._trace(state, "executor", started, step, output)
            return output
        tool = self.registry.get(tool_name, set(state["enabled_tools"]))
        call = {"id": str(uuid.uuid4()), "tool": tool_name, "arguments": step.get("arguments", {})}
        if tool.requires_approval:
            approval = AgentApprovalRequest(agent_run_id=uuid.UUID(state["run_id"]), tool_call_id=call["id"], tool_name=tool_name, action_description=step["description"], arguments=redact(call["arguments"]), risk_level=tool.risk_level.value)
            self.session.add(approval); await self.session.flush()
            output = {"approval_required": True, "approval_request_id": str(approval.id), "status": "waiting_approval", "tool_calls": state.get("tool_calls", []) + [call], "step_count": state.get("step_count", 0) + 1}
            await self._trace(state, "approval", started, call, output, "waiting_approval")
            return output
        result = None
        for attempt in range(settings.agent_tool_retries + 1):
            result = await tool.invoke(ToolContext(self.session, state["run_id"], set(state["enabled_tools"])), call["arguments"])
            if result.success or tool.risk_level.value == "high": break
            if attempt < settings.agent_tool_retries: await asyncio.sleep(0.05 * (2 ** attempt))
        assert result is not None
        output = {"tool_calls": state.get("tool_calls", []) + [call], "tool_results": state.get("tool_results", []) + [{"tool": tool_name, "success": result.success, "output": result.output, "error": result.error, "metadata": result.metadata, "duration_ms": result.duration_ms}], "observations": state.get("observations", []) + [f"{tool_name}: {'success' if result.success else result.error}"], "current_step": index + 1, "completed_steps": state.get("completed_steps", []) + [step], "retry_count": state.get("retry_count", 0) + (0 if result.success else 1), "step_count": state.get("step_count", 0) + 1}
        if tool_name == "knowledge_search" and result.success:
            output["citations"] = state.get("citations", []) + result.output.get("citations", [])
        await self._trace(state, f"tool:{tool_name}", started, call, output, "completed" if result.success else "failed")
        return output

    async def verifier_node(self, state: AgentState) -> dict:
        started = time.perf_counter()
        if state.get("step_count", 0) >= settings.agent_max_steps:
            output = {"status": "failed", "error": "AGENT_MAX_STEPS_EXCEEDED"}
        else:
            verdict = await self.verifier.verify(state)
            if verdict.status == "complete":
                facts = [item.get("output") for item in state.get("tool_results", []) if item.get("success")]
                prepared = next((item.get("output") for item in state.get("tool_results", []) if item.get("tool") == "refund.prepare" and item.get("success")), None)
                if prepared:
                    answer = f"Order {prepared['order_code']} appears {'eligible' if prepared['eligible'] else 'not eligible'} for refund based on its delivery/refund status and the {prepared['age_days']}-day age."
                    if state.get("citations"): answer += " The retrieved refund policy is cited in source [1]."
                elif any(item.get("tool") == "refund.create" and item.get("success") for item in state.get("tool_results", [])):
                    answer = "The approved refund request was created successfully."
                else: answer = f"Completed the plan using {len(facts)} tool result(s). The recorded evidence is available in the run trace."
                output = {"status": "completed", "final_answer": answer}
            elif verdict.status == "continue": output = {"status": "running"}
            elif verdict.status == "replan": output = {"status": "planning", "plan": {}, "current_step": 0}
            else: output = {"status": "failed", "error": verdict.reason}
        output["step_count"] = state.get("step_count", 0) + 1
        await self._trace(state, "verifier", started, {}, output, output["status"])
        return output

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("bootstrap", self.bootstrap_node); graph.add_node("router", self.router_node); graph.add_node("planner", self.planner_node); graph.add_node("executor", self.executor_node); graph.add_node("verifier", self.verifier_node)
        graph.add_edge(START, "bootstrap")
        graph.add_conditional_edges("bootstrap", lambda s: "resume" if s.get("plan", {}).get("steps") else "new", {"new": "router", "resume": "executor"})
        graph.add_edge("router", "planner"); graph.add_edge("planner", "executor")
        graph.add_conditional_edges("executor", lambda s: "wait" if s.get("status") == "waiting_approval" else "verify", {"wait": END, "verify": "verifier"})
        graph.add_conditional_edges("verifier", lambda s: "continue" if s.get("status") == "running" else "replan" if s.get("status") == "planning" else "end", {"continue": "executor", "replan": "planner", "end": END})
        return graph.compile()

    async def execute(self, run: AgentRun, enabled_tools: list[str], knowledge_base_id: str | None = None, prior_state: dict | None = None) -> AgentState:
        state: AgentState = prior_state or {"messages": [], "user_request": run.input, "knowledge_base_id": knowledge_base_id, "plan": {}, "current_step": 0, "completed_steps": [], "tool_calls": [], "tool_results": [], "observations": [], "working_memory": {}, "citations": [], "approval_required": False, "approval_request_id": None, "retry_count": 0, "step_count": 0, "status": "pending", "final_answer": None, "error": None, "enabled_tools": enabled_tools, "run_id": str(run.id)}
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(self.graph.ainvoke(state, {"recursion_limit": settings.agent_max_steps * 3}), timeout=settings.agent_timeout_seconds)
        except TimeoutError:
            result = {**state, "status": "failed", "error": "AGENT_TIMEOUT"}
        run.status = AgentRunStatus(result["status"]); run.state = redact(dict(result)); run.final_answer = result.get("final_answer"); run.error = result.get("error"); run.step_count = result.get("step_count", 0); run.total_duration_ms = (time.perf_counter() - started) * 1000
        if run.status in {AgentRunStatus.COMPLETED, AgentRunStatus.FAILED, AgentRunStatus.CANCELLED}: run.finished_at = datetime.now(UTC)
        await self.session.commit(); await self.session.refresh(run)
        return result

    async def resume(self, run: AgentRun) -> AgentState:
        if run.status != AgentRunStatus.WAITING_APPROVAL:
            raise ApplicationError("RUN_NOT_WAITING_APPROVAL", "Agent run is not waiting for approval", 409)
        approval_id = run.state.get("approval_request_id")
        approval = await self.session.get(AgentApprovalRequest, uuid.UUID(approval_id))
        if not approval or approval.status == ApprovalStatus.PENDING:
            raise ApplicationError("APPROVAL_PENDING", "Approval has not been decided", 409)
        state = dict(run.state); state["approval_required"] = False; state["approval_request_id"] = None
        if approval.status == ApprovalStatus.REJECTED:
            state["observations"] = state.get("observations", []) + ["User rejected action."]
            state["current_step"] = state.get("current_step", 0) + 1
        else:
            tool = self.registry.get(approval.tool_name, set(state["enabled_tools"]))
            result = await tool.invoke(ToolContext(self.session, str(run.id), set(state["enabled_tools"])), approval.arguments)
            state["tool_results"] = state.get("tool_results", []) + [{"tool": approval.tool_name, "success": result.success, "output": result.output, "error": result.error, "metadata": result.metadata, "duration_ms": result.duration_ms}]
            state["current_step"] = state.get("current_step", 0) + 1
        state["status"] = "running"
        return await self.execute(run, state["enabled_tools"], state.get("knowledge_base_id"), state)
