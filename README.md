# NexusAI

> **Enterprise AI Workspace — from knowledge ingestion and Hybrid RAG to tool-using Agents, human approval, Text-to-SQL, customer service, and document intelligence.**

NexusAI is a full-stack **LLM application engineering portfolio project** designed around the kinds of systems used in enterprise AI applications. Instead of stopping at a chatbot demo, the project connects data ingestion, retrieval, generation, agent orchestration, tool permissions, approval workflows, business applications, evaluation, and security boundaries into one extensible workspace.

The source is organized around **Phase 1–5** engineering areas for LLM / AI Application Engineer roles: RAG pipelines, structured and unstructured data, bounded agent workflows, approval, evaluation, and a FastAPI + React interface. The current public snapshot has the publication and validation gaps below; the feature list is not a claim that every path is runnable or production-ready.

## Current Validation Status

Documentation review: **2026-11-05**. This was a source and repository inspection, not a new application test run.

- **Source publication gap:** the tracked tree does not contain `backend/app/data/`, although [the data-analysis route](backend/app/api/routes/data_analyst.py) imports `app.data.models` and `app.data.service` and is loaded by [the API router](backend/app/api/router.py). A clean checkout therefore has an unresolved backend import risk. Restore and verify the missing source before treating the public snapshot as a runnable full application. The broad `data/` rule in [.gitignore](.gitignore) needs checking; its role in the omission has not been confirmed.
- **Agent planning is deterministic:** the API constructs [AgentRuntime](backend/app/agents/runtime/executor.py) with `FakePlanner`, `FakeRouter`, and `FakeVerifier`. The LangGraph, tools, traces, and approval flow are inspectable engineering implementations; configuring a chat provider does not turn these components into a verified model-driven planner.
- **Validation evidence:** test commands below describe how to check the project. This review did not rerun unit/integration tests, real providers, browser flows, or deployment, and adds no new pass counts.

## What NexusAI Can Do

| Capability | What is implemented |
| --- | --- |
| Knowledge ingestion | PDF, DOCX, TXT, Markdown, URL ingestion, bounded website crawling |
| Hybrid RAG | pgvector semantic search + PostgreSQL FTS + RRF fusion + optional reranking |
| Grounded answers | Context budgeting, source metadata, citation building/validation, SSE streaming |
| Agent runtime | LangGraph state machine, deterministic planner/router/verifier, tool execution, retries and bounded steps |
| Tool system | Permissioned Tool Registry, knowledge search, read-only SQL, HTTP and web-search boundaries |
| Human approval | High-risk actions pause, persist approval state, and resume after approve/reject |
| AI Data Analyst | Intended schema → SQL → table/chart workflow; public snapshot is missing the imported `app.data` module, so this path is not currently verified runnable |
| Customer Service | Customer/order context + policy RAG + refund eligibility + approval-gated action |
| Document Intelligence | Structured extraction, summaries, deterministic risk rules, citations and comparison |
| Evaluation | Deterministic RAG, Agent and business-workflow regression datasets and integration tests |

## Why This Project Is More Than a Chatbot

A basic LLM demo usually ends at `prompt → model → answer`. NexusAI focuses on the engineering layers around the model:

```text
Enterprise Data
   │
   ├── Files / URLs / Websites ──→ Ingestion ──→ Chunking ──→ Embeddings
   │                                                     │
   │                                                     ▼
   │                                           PostgreSQL + pgvector
   │                                                     │
User ──→ React UI ──→ FastAPI ──→ Hybrid Retrieval ──→ RAG + Citations
                           │
                           ├──→ LangGraph Agent Runtime
                           │       ├── Planner / Router / Verifier
                           │       ├── Knowledge Tool
                           │       ├── Read-only SQL Tool
                           │       ├── HTTP / Web Tools
                           │       └── Human Approval for high-risk actions
                           │
                           └──→ Business Applications
                                   ├── AI Data Analyst
                                   ├── Customer Service
                                   └── Document Intelligence
```

The emphasis is on **grounding, permissions, observability, deterministic evaluation, and safe execution**, not merely generating fluent text.

## Engineering Highlights

- **Real Hybrid Retrieval:** pgvector cosine retrieval and PostgreSQL full-text retrieval run as separate paths and are fused with Reciprocal Rank Fusion (RRF).
- **Source-grounded RAG:** retrieved chunks retain document/page/URL metadata and answers use validated `[1]`, `[2]` style citations.
- **Bounded Agent Runtime:** LangGraph execution has explicit state, maximum steps, timeout/retry boundaries, verifier decisions and persistent run traces.
- **Human-in-the-loop safety:** high-risk tools do not execute immediately; the run pauses until an approval decision is persisted and execution is resumed.
- **Safe Text-to-SQL:** generated SQL is parsed with `sqlglot`, restricted to read-only queries, constrained by schema/table allowlists, statement timeout and row limits.
- **SSRF-aware networking:** URL ingestion and HTTP tools reject localhost/private/reserved targets and revalidate redirects.
- **Provider abstraction:** real OpenAI/Cohere/Tavily integrations can be configured while deterministic fake providers keep development and tests reproducible.
- **Real database validation:** migrations, pgvector retrieval, PostgreSQL FTS, RRF and business workflows have integration paths against PostgreSQL rather than being UI-only mocks.

## Architecture

```text
React + TypeScript
        |
FastAPI / Pydantic
        |
RAG Pipeline -------- LangGraph Agent Runtime -------- Business Applications
Vector + FTS + RRF    Tool Registry + Approval        Data / Customer / Documents
        |                         |                              |
PostgreSQL + pgvector          Redis                     Auditable Traces
```

## Technology Stack

- **Backend:** FastAPI, Pydantic v2, SQLAlchemy async, Alembic
- **Frontend:** React, TypeScript, Vite
- **Data:** PostgreSQL, pgvector, PostgreSQL Full Text Search, Redis
- **LLM / Agent:** LangGraph, OpenAI provider abstractions, optional Cohere/Tavily providers
- **Safety:** sqlglot AST validation, SSRF controls, tool allowlists, persisted human approval
- **Engineering:** Docker Compose, pytest, deterministic evaluation fixtures

## Quick Start

**The commands below start only PostgreSQL and Redis.** They do not start the API or UI, install dependencies, or resolve the source publication gap above. After the missing source has been restored and verified, continue with Backend Setup and Frontend Setup.

```bash
git clone https://github.com/tangwencan666/NexusAI.git
cd NexusAI
cp .env.example .env
docker compose up -d
```

## One-command Local Startup

For an already prepared Windows development checkout only: complete Backend Setup and Frontend Setup, create the local environment files, and resolve the source gap above first. The script expects `backend/.venv/Scripts/python.exe` and installed frontend dependencies; it is not a first-time installer. Automatic Docker Desktop launch currently uses a developer-specific installation path, so start Docker yourself if it is installed elsewhere.

Windows PowerShell:

```powershell
.\start.ps1
```

View status:

```powershell
.\status.ps1
```

Stop NexusAI:

```powershell
.\stop.ps1
```

The start command launches Docker Desktop when needed, starts PostgreSQL/pgvector and Redis, waits for both containers to become healthy, upgrades Alembic to `head`, and then starts the FastAPI backend and React/Vite frontend. The stop command stops only the backend/frontend processes recorded by these scripts and runs `docker compose stop`; it does not delete database or Redis volumes.

## Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ and Redis 7+, or Docker Compose
- An OpenAI API key for real embeddings/generation, or deterministic fake providers for development

## Database Setup

From the project root:

```powershell
Copy-Item .env.example .env
docker compose up -d
```

The Compose file starts PostgreSQL on port 5432 and Redis on port 6379 with persistent volumes. Change `POSTGRES_PASSWORD` outside local development; no real secrets are committed.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, OpenAPI docs at `/docs`, and versioned endpoints under `/api/v1`.

## Frontend Setup

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. `VITE_API_BASE_URL` controls the backend URL and defaults to `http://127.0.0.1:8000` for local development. The backend also permits `http://localhost:5173` as a local CORS origin.

## Knowledge Base & Ingestion

Phase 2 supports `.pdf`, `.docx`, `.txt`, and `.md` documents, individual HTTP(S) pages, and bounded same-domain website crawls. Source files use local storage in `backend/data/uploads`; chunks and embeddings are stored in PostgreSQL.

The ingestion path is:

```text
File / URL / Website
→ validation
→ parsing / main-content extraction
→ cleaning
→ metadata-aware chunking
→ embedding
→ PostgreSQL + pgvector
```

PDF page numbers, filenames and URL metadata are retained so later RAG answers can point back to their sources.

## Hybrid RAG

Phase 3 combines pgvector semantic retrieval with PostgreSQL full-text keyword retrieval. Vector search finds semantic similarity while FTS preserves exact lexical matches. Reciprocal Rank Fusion merges both ranked lists before optional reranking.

```text
Query
 ├──→ Vector Search ──┐
 └──→ PostgreSQL FTS ─┤
                      ▼
                     RRF
                      ▼
                  Reranker
                      ▼
               Context Builder
                      ▼
                  Chat Model
                      ▼
             Citation Validation
```

Migration `20260825_0003` adds the generated `tsvector` and GIN index. The lexical retriever currently uses PostgreSQL cover-density ranking rather than claiming a full Okapi BM25 implementation.

## Citation & Streaming

Answers cite only sources that survive final context construction. Unknown citation IDs are removed and reported in the trace. `POST /api/v1/knowledge-bases/{id}/chat/stream` emits SSE metadata, token, citation, done and error events.

## Agent Runtime

Phase 4 adds a bounded LangGraph runtime:

```text
START
→ Bootstrap
→ Router
→ Planner
→ Executor
→ Tool / Approval
→ Verifier
→ Continue / Replan / Complete / Fail
```

Agent state is JSON-serializable and runs persist structured steps and redacted traces. Agents can only call tools explicitly enabled for them.

## Tool Calling & Human Approval

The Tool Registry includes knowledge retrieval, AST-validated read-only SQL, SSRF-protected HTTP access, web-search provider boundaries and demo business actions.

High-risk actions follow a separate execution path:

```text
Tool Call
→ Risk Check
→ Persist Approval Request
→ Pause Run
→ Approve / Reject
→ Resume
→ Execute or Cancel
```

This prevents a model from directly turning generated intent into an irreversible write action.

## AI Data Analyst

Phase 5 describes the following analytics workflow. The public snapshot currently lacks the imported `app.data` implementation; this section records the intended flow, not a completed clean-checkout acceptance:

```text
Natural-language Question
→ Relevant Schema Retrieval
→ Structured Text-to-SQL
→ SQLReadOnlyTool Validation
→ PostgreSQL
→ Result Table
→ Declarative Chart
→ Grounded Insight
```

SQL execution remains behind the same read-only safety layer even when a failed query is repaired and regenerated.

## Customer Service

The Customer Service workflow combines customer/order lookup, policy retrieval and refund eligibility. Read operations can run directly, while a refund creation is a high-risk action that must pass the Phase 4 approval workflow before a database write occurs.

## Document Intelligence

Indexed documents can be classified, extracted into typed contract fields, summarized with chunk/page citations, checked by deterministic risk rules and compared at section level. The current comparison engine is intentionally described as section-level diff rather than professional legal redlining.

## Evaluation & Testing

NexusAI includes deterministic regression fixtures for RAG, Agent behavior and Phase 5 business workflows. These datasets are intended to catch regressions and demonstrate evaluation methodology; **they are not production benchmarks**.

Examples:

```powershell
cd backend
pytest

python -m app.evaluation.rag_eval --retriever hybrid
python -m app.evaluation.agent_eval
python -m app.evaluation.business_eval --dataset evals/data_analyst.jsonl
```

Run PostgreSQL integration tests with:

```powershell
$env:RUN_INTEGRATION='1'
pytest -m integration -q
```

## Security Design

- Real `.env` files, uploads, virtual environments, dependency folders, build output, caches, logs, database files and Docker disks are excluded from Git.
- API keys are loaded from environment variables; production credentials are not committed.
- SQL tools use AST validation, one-statement enforcement, read-only transactions, timeouts, row limits and schema/table allowlists.
- URL ingestion and HTTP tools reuse SSRF controls and reject localhost/private/reserved addresses.
- High-risk tools pause for persisted human approval before execution.
- Retrieved documents and tool output are treated as untrusted observations rather than instructions that can expand Agent permissions.
- Trace redaction covers authorization, API-key, password, secret, token and cookie-like fields.

## Project Structure

```text
backend/
  app/agents/          Agent runtime, tools, approvals and traces
  app/api/             FastAPI routers
  app/ai/              Chat / embedding provider abstractions
  app/data/            Schema retrieval, Text-to-SQL and analysis
  app/documents/       Document extraction, risks and comparison
  app/knowledge/       Ingestion, retrieval, RAG, reranking and citations
  app/db/models/       SQLAlchemy domain models
  app/evaluation/      RAG / Agent / business evaluation
  migrations/          Alembic migrations
  evals/               deterministic evaluation datasets
  tests/               unit and integration tests
frontend/
  src/pages/           Knowledge, Agent, Data, Customer and Document UIs
  src/api/             typed HTTP client
  src/components/      shared components
docs/                  architecture documentation
docker-compose.yml     PostgreSQL + pgvector and Redis
```

## Roadmap

- **Phase 1 — Foundation:** FastAPI, React, PostgreSQL, Redis, migrations, core models and dashboard.
- **Phase 2 — Knowledge Platform:** file/URL ingestion, website crawler, embeddings and pgvector retrieval.
- **Phase 3 — Hybrid RAG:** vector + FTS, RRF, reranking, citations, streaming and retrieval evaluation.
- **Phase 4 — Agent Runtime:** LangGraph, permissioned tools, traces, SQL safety and human approval.
- **Phase 5 — Business Applications:** AI Data Analyst, Customer Service and Document Intelligence.
- **Phase 6 — Planned:** MCP + Coding Agent.
- **Phase 7 — Planned:** deeper evaluation, observability and security hardening.

## Current Scope

NexusAI is an engineering portfolio / development project, not a production SaaS claim. The public source publication gap and deterministic Agent components in Current Validation Status remain unresolved. Some external-provider paths require API keys, deterministic fake providers are intentionally used in regression tests, and several Phase 6–7 capabilities remain on the roadmap. The goal is to make those boundaries explicit while keeping the implemented paths testable and inspectable.
