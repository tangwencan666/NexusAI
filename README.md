# NexusAI

NexusAI is an **Enterprise AI Workspace** foundation. Its long-term direction includes Enterprise Copilot, RAG and website knowledge, data and customer-service agents, document intelligence, coding agents, MCP, evaluation, and observability.

It demonstrates an end-to-end enterprise AI architecture: ingestion and Hybrid RAG, grounded citations, a bounded LangGraph agent runtime, permissioned tools, human approval, safe Text-to-SQL, customer-service workflows, and deterministic document intelligence.

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

- FastAPI, Pydantic v2, SQLAlchemy async, Alembic
- React, TypeScript, Vite
- PostgreSQL, pgvector, PostgreSQL Full Text Search, Redis
- LangGraph, OpenAI provider abstractions, deterministic fake providers
- Docker Compose, pytest, sqlglot

## Quick Start

```bash
git clone https://github.com/tangwencan666/NexusAI.git
cd NexusAI
cp .env.example .env
docker compose up -d
```

Phase 1 provides a production-minded FastAPI/React foundation without prematurely implementing LLM or RAG behavior.

Phase 2 adds real file and web ingestion, deterministic metadata-rich chunking, embedding provider boundaries, pgvector storage, website crawling, and vector retrieval.

## Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ and Redis 7+, or Docker Compose
- An OpenAI API key for real embeddings, or the deterministic `fake` provider for development

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

The API is available at `http://localhost:8000`, OpenAPI docs at `/docs`, and versioned endpoints under `/api/v1`.

Core endpoints:

- `GET /api/v1/health`
- `POST /api/v1/users`, `GET /api/v1/users/{id}`
- `POST /api/v1/workspaces`, `GET /api/v1/workspaces`, `GET /api/v1/workspaces/{id}`
- `POST /api/v1/knowledge-bases`, `GET /api/v1/knowledge-bases`
- `POST /api/v1/agents`, `GET /api/v1/agents`, `GET /api/v1/agents/{id}`

## Frontend Setup

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. `VITE_API_BASE_URL` controls the backend URL and defaults to `http://localhost:8000` for local development.

## Run Tests

```powershell
cd backend
pytest
```

The health test does not require a running database. Resource endpoints do require PostgreSQL and the applied migration.

## Knowledge Base

Phase 2 supports `.pdf`, `.docx`, `.txt`, and `.md` documents, individual HTTP(S) pages, and bounded same-domain website crawls. Source files use local storage in `backend/data/uploads`; chunks and embeddings are stored in PostgreSQL.

## File Ingestion

```bash
curl -F "file=@annual-report.pdf" \
  http://localhost:8000/api/v1/knowledge-bases/KNOWLEDGE_BASE_ID/documents/upload
```

Uploads default to a 50 MB maximum and are validated by extension and MIME type. PDF page numbers and original filenames are retained for citations.

## URL Ingestion

```bash
curl -X POST http://localhost:8000/api/v1/knowledge-bases/KNOWLEDGE_BASE_ID/documents/url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/article"}'
```

URL fetches enforce public HTTP(S), DNS/IP checks, bounded redirects, timeouts, and response size. Trafilatura extracts the main page content.

## Website Crawl

```bash
curl -X POST http://localhost:8000/api/v1/knowledge-bases/KNOWLEDGE_BASE_ID/website-crawls \
  -H "Content-Type: application/json" \
  -d '{"root_url":"https://example.com","max_pages":20,"max_depth":2}'
```

The synchronous Phase 2 crawler follows normalized same-domain links, respects robots.txt, removes fragments, de-duplicates URLs, and continues past individual page failures.

## Embeddings

The default provider is OpenAI `text-embedding-3-small` with 1536 dimensions. The API starts normally without a key; ingestion and search return `EMBEDDING_PROVIDER_UNAVAILABLE`. For local deterministic development set `EMBEDDING_PROVIDER=fake` before running the migration so the configured vector dimension stays consistent.

## pgvector

Compose uses `pgvector/pgvector:pg17`. Migration `20260825_0002` creates the vector extension, ingestion tables, a cosine HNSW index, and the configured vector dimension. Do not change `EMBEDDING_DIMENSION` after migration without a dimension migration.

## Vector Search

```bash
curl -X POST http://localhost:8000/api/v1/knowledge-bases/KNOWLEDGE_BASE_ID/search \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the refund policy?","top_k":5}'
```

Results include cosine similarity, chunk text, document id, and citation metadata. Phase 3 layers keyword retrieval, fusion, reranking, and grounded generation over this reusable vector service.

## Hybrid Retrieval

Phase 3 combines pgvector semantic retrieval with PostgreSQL full-text keyword retrieval. Vector search finds meaning; FTS preserves exact terms. Reciprocal Rank Fusion (RRF) merges ranks, de-duplicates chunks, and retains original scores and ranks.

## BM25 / PostgreSQL FTS

Migration `20260825_0003` adds a stored `search_vector` generated with the `simple` configuration and a GIN index. `BM25Retriever` exposes the lexical path using PostgreSQL cover-density ranking; OpenSearch is deferred until scale requires it.

## RRF and Reranking

RRF uses `sum(1 / (RRF_K + rank))`. The default deterministic fake reranker is suitable for tests; set `RERANKER_PROVIDER=cohere` and `COHERE_API_KEY` for Cohere Rerank.

## Query Rewrite and RAG Chat

Conversation-aware rewrite uses the configured Chat Model and safely falls back to the original query. Chat is available at:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge-bases/KB_ID/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the refund policy?","recent_messages":[]}'
```

Set `LLM_PROVIDER=fake` for deterministic local validation or configure `OPENAI_API_KEY` and `LLM_MODEL` for grounded OpenAI answers.

## Citation and Streaming

Answers cite only the final context as `[1]`, `[2]`. Unknown citation IDs are removed and reported in the trace. `POST /api/v1/knowledge-bases/{id}/chat/stream` emits SSE `metadata`, `token`, `citation`, `done`, and `error` events.

## Evaluation

The 20-case deterministic dataset supports Recall@5, Hit Rate@5, and MRR with regression thresholds:

```powershell
python -m app.evaluation.rag_eval --retriever vector
python -m app.evaluation.rag_eval --retriever bm25
python -m app.evaluation.rag_eval --retriever hybrid
python -m app.evaluation.rag_eval --retriever rerank
```

Unit tests exclude external APIs. Run the real PostgreSQL FTS + pgvector + RRF test with:

```powershell
$env:RUN_INTEGRATION='1'
pytest -m integration -q
```

## Environment Variables

See `backend/.env.example`. Phase 2 settings include `UPLOAD_DIRECTORY`, `MAX_UPLOAD_SIZE_MB`, URL timeouts/limits, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, and `OPENAI_API_KEY`.

## Phase 2 Usage

1. Start Compose and apply `alembic upgrade head`.
2. Create a user, workspace, and knowledge base through the Phase 1 APIs.
3. Configure embeddings and start the backend/frontend.
4. Open `/knowledge`, choose the knowledge base, and upload a file, add a URL, or crawl a website.
5. Open its Search tab to inspect top-k pgvector matches and citation metadata.

## Project Structure

```text
backend/
  app/api/             FastAPI routers
  app/core/            settings, logging, exceptions
  app/db/models/       SQLAlchemy domain models
  app/repositories/    persistence operations
  app/services/        application orchestration
  app/schemas/         Pydantic API contracts
  migrations/          Alembic migrations
  tests/               backend tests
frontend/
  src/api/             typed HTTP client
  src/components/      shared components
  src/layouts/         workspace shell
  src/pages/           application pages
  src/routes/          route definitions
infrastructure/        reserved for future deployment assets
docs/                  architecture documentation
docker-compose.yml     PostgreSQL and Redis services
```

## Roadmap

### Phase 1 — Foundation

FastAPI, React, PostgreSQL, Redis, migrations, core models, APIs, tests, and dashboard.

### Phase 2 — Knowledge Base + URL + Website + RAG

### Phase 3 — Hybrid RAG + Reranking + Citation + Evaluation

### Phase 4 — Agent Runtime + Tools + Human Approval

### Phase 5 — Data Analyst + Customer Service + Document Intelligence

### Phase 6 — MCP + Coding Agent

### Phase 7 — Evaluation + Observability + Security

## Security

- Real `.env` files, uploads, virtual environments, dependency folders, build output, caches, logs, database files, and Docker disks are excluded from Git.
- API keys are optional and loaded from environment variables; no production credentials are committed.
- SQL tools use AST validation, one-statement enforcement, read-only transactions, timeouts, row limits, and schema/table allowlists.
- HTTP tools reuse SSRF controls and reject localhost/private addresses.
- High-risk tools pause for persisted human approval before execution.
- Retrieved documents and tool output are treated as untrusted data.

Evaluation numbers in this repository come from deterministic regression fixtures and demo datasets. They are development safeguards, not production benchmarks.
## Agent Runtime

Phase 4 adds a bounded LangGraph runtime with Router, structured Planner, Executor, Tool nodes, Verifier, JSON-serializable working state, retries, timeout, maximum steps, and persistent traces.

## Tool Calling

Tools are centrally registered and explicitly enabled per agent. Included tools are Phase 3 Knowledge Search, AST-validated SQL Read Only, SSRF-protected HTTP GET, approval-gated HTTP POST, Fake/Tavily Web Search, and a demo high-risk refund tool.

## Human Approval

High-risk calls pause before execution. Decide with `POST /api/v1/agent-approvals/{id}/approve` or `/reject`, then continue with `POST /api/v1/agent-runs/{run_id}/resume`.

```bash
curl -X POST http://localhost:8000/api/v1/agents/AGENT_ID/runs -H "Content-Type: application/json" -d '{"message":"Check customer C1001 orders and the refund policy","knowledge_base_id":"KB_ID","debug":true}'
curl http://localhost:8000/api/v1/agent-runs
curl http://localhost:8000/api/v1/tools
```

## Agent Evaluation

Run `python -m app.evaluation.agent_eval`. The deterministic 20-task fixture measures completion, tool selection, tool success, average steps, approval correctness, and loop rate. It is a regression fixture, not a production quality claim.

## AI Data Analyst

Phase 5 provides workspace data sources, Schema Catalog/Search, structured Text-to-SQL through the shared ChatModel, mandatory SQLReadOnlyTool validation, bounded repair, tables, declarative charts, grounded insights, and a deterministic 240-order demo. See `docs/data-analyst.md`.

## Customer Service

The Customer Service Agent combines customer/order lookup, Phase 3 policy retrieval, ticket operations, refund preparation, and Phase 4 approval-gated writes. It does not receive arbitrary HTTP or web access by default. See `docs/customer-service.md`.

## Document Intelligence

Indexed documents can be classified, extracted into Pydantic contract fields, checked by deterministic risk rules, summarized with chunk/page citations, and compared at section level. See `docs/document-intelligence.md`.

Phase 5 evaluation fixtures:

```powershell
python -m app.evaluation.business_eval --dataset evals/data_analyst.jsonl
python -m app.evaluation.business_eval --dataset evals/customer_service.jsonl
python -m app.evaluation.business_eval --dataset evals/document_intelligence.jsonl
```
