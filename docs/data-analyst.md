# AI Data Analyst

`Question → Schema Catalog → lexical schema retrieval → structured Text-to-SQL → sqlglot validation → SQLReadOnlyTool → DataResult → ChartSpec → Insight`.

Data sources store workspace ownership, type, an environment-reference connection configuration, schema/table allowlists, and status. Password-like fields are redacted from API responses and traces. Phase 5 executes PostgreSQL through the existing read-only tool; MySQL is represented but intentionally unavailable.

Schema Catalog reads columns, types, primary/foreign keys, and comments. Only relevant tables are sent to a model. The deterministic demo query works without an API key; other natural-language questions use the shared ChatModel structured-output method and return `LLM_PROVIDER_UNAVAILABLE` when appropriate. Failed SQL may be repaired at most `DATA_SQL_MAX_RETRIES` times and every candidate is revalidated.

Charts are declarative `bar|line|pie|area` specifications. Analysis uses safe built-in aggregation over actual rows and never executes generated Python or JavaScript.

API: CRUD `/api/v1/data-sources`, analysis `/api/v1/data-sources/{id}/analyze`. Seed with `python scripts/seed_phase5_demo.py`; evaluate with `python -m app.evaluation.business_eval --dataset evals/data_analyst.jsonl`.
