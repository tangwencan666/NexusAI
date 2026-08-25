from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NexusAI"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://nexusai:nexusai_dev_password@localhost:5432/nexusai"
    redis_url: str = "redis://localhost:6379/0"
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    upload_directory: str = "data/uploads"
    max_upload_size_mb: int = 50
    max_url_response_size_mb: int = 10
    url_connect_timeout_seconds: float = 5.0
    url_read_timeout_seconds: float = 20.0
    url_max_redirects: int = 5
    crawler_user_agent: str = "NexusAIKnowledgeBot/0.2"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    openai_api_key: str | None = None
    vector_top_k: int = 20
    bm25_top_k: int = 20
    hybrid_top_k: int = 10
    rrf_k: int = 60
    reranker_provider: str = "fake"
    reranker_model: str = "rerank-v3.5"
    rerank_top_k: int = 5
    cohere_api_key: str | None = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    rag_max_context_tokens: int = 6000
    query_cache_ttl_seconds: int = 3600
    min_recall_at_5: float = 0.5
    min_mrr: float = 0.4
    agent_max_steps: int = 10
    agent_timeout_seconds: float = 120.0
    agent_max_retries: int = 2
    agent_tool_retries: int = 1
    agent_conversation_window: int = 10
    sql_tool_max_rows: int = 100
    sql_tool_timeout_seconds: float = 10.0
    sql_tool_allowed_schemas: str = "public"
    sql_tool_allowed_tables: str = ""
    http_tool_allowed_hosts: str = ""
    http_tool_timeout_seconds: float = 15.0
    http_tool_max_response_bytes: int = 1048576
    web_search_provider: str = "fake"
    tavily_api_key: str | None = None
    data_sql_max_retries: int = 2

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
