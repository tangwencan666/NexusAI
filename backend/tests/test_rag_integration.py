import os
import uuid

import psycopg
import pytest

from app.knowledge.retrieval.models import RetrievalResult
from app.knowledge.retrieval.rrf import reciprocal_rank_fusion

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="set RUN_INTEGRATION=1"),
]


def test_real_postgres_fts_vector_rrf() -> None:
    connection = psycopg.connect("postgresql://nexusai:nexusai_dev_password@localhost:5432/nexusai")
    try:
        with connection.transaction():
            connection.execute(
                "CREATE TEMP TABLE rag_integration (id uuid, content text, embedding vector(3), "
                "search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED) ON COMMIT DROP"
            )
            ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
            connection.cursor().executemany(
                "INSERT INTO rag_integration VALUES (%s,%s,%s)",
                [
                    (ids[0], "refund requests are accepted within thirty days", "[1,0,0]"),
                    (ids[1], "shipping normally takes five business days", "[0.7,0.3,0]"),
                    (ids[2], "privacy data deletion is available", "[-1,0,0]"),
                ],
            )
            vector_rows = connection.execute(
                "SELECT id,content,1-(embedding <=> '[1,0,0]'::vector) score FROM rag_integration ORDER BY embedding <=> '[1,0,0]'::vector"
            ).fetchall()
            bm25_rows = connection.execute(
                "SELECT id,content,ts_rank_cd(search_vector,websearch_to_tsquery('simple','refund thirty days')) score "
                "FROM rag_integration WHERE search_vector @@ websearch_to_tsquery('simple','refund thirty days') ORDER BY score DESC"
            ).fetchall()
            document_id = uuid.uuid4()
            vector_results = [RetrievalResult(row[0], document_id, row[1], {}, {}, float(row[2]), rank, "vector", vector_score=float(row[2]), ranks={"vector": rank}) for rank, row in enumerate(vector_rows, 1)]
            bm25_results = [RetrievalResult(row[0], document_id, row[1], {}, {}, float(row[2]), rank, "bm25", lexical_score=float(row[2]), ranks={"bm25": rank}) for rank, row in enumerate(bm25_rows, 1)]
            fused = reciprocal_rank_fusion([vector_results, bm25_results], 60)
            assert fused[0].chunk_id == ids[0]
            assert fused[0].ranks == {"vector": 1, "bm25": 1}
    finally:
        connection.close()
