# Phase 1 Architecture

HTTP requests flow through versioned FastAPI routers into application services. Services coordinate reusable repositories, which are the only layer responsible for SQLAlchemy persistence. ORM models and Pydantic API contracts remain separate.

The boundaries intentionally leave room for future `rag`, `agent_runtime`, `tools`, and `integrations` application modules without coupling those capabilities to HTTP handlers or core persistence.
