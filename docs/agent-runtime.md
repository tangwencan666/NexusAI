# Agent Runtime

```text
User → Router → Planner → Executor → Tool → Verifier
                                  ↓                ↓
                              Approval         Continue / Complete
```

Phase 4 uses a bounded LangGraph `StateGraph`. Runtime state contains only JSON-compatible messages, plan steps, tool calls/results, observations, working memory, citations, approval state, counters, status, answer, and error. `AGENT_MAX_STEPS` and the run timeout prevent loops.

The Tool Registry is independent of the graph so capabilities can later be supplied by other runtimes without coupling the agent to concrete tools. Every agent has an explicit `enabled_tools` list. Inputs use Pydantic JSON schemas and results use one `ToolResult` contract.

`KnowledgeSearchTool` calls the Phase 3 Hybrid Retriever. `SQLReadOnlyTool` parses PostgreSQL with sqlglot, accepts one SELECT/CTE, enforces schema/table allowlists, runs in a separate read-only transaction, applies statement timeout and a hard row limit. HTTP reuses Phase 2 SSRF validation and revalidates redirects. Web search has fake and optional Tavily providers.

High-risk tools create a persisted approval request and the graph stops at `waiting_approval`. Approve or reject the request and call `/api/v1/agent-runs/{id}/resume`. Approval executes the saved call once; rejection records an observation without executing it. Repeated decisions are rejected.

Run nodes are persisted to `agent_run_steps` with duration and redacted inputs/outputs. Authorization, API keys, passwords, secrets, tokens, and cookies are never stored. Tool outputs and retrieved documents are untrusted observations and cannot grant capabilities.

Reranking, multi-agent coordination, long-term memory, MCP, sandbox execution, and production write integrations remain outside Phase 4.
