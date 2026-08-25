# Hybrid RAG Architecture

```text
Query → Analyze / Rewrite → pgvector + PostgreSQL FTS
      → Reciprocal Rank Fusion → Reranker → Context Builder
      → Chat Model → Citation Builder / Validator → JSON or SSE
```

PostgreSQL FTS is the Phase 3 lexical engine because chunks already live beside their vectors and metadata. A generated `tsvector` and GIN index add keyword retrieval without operating OpenSearch prematurely. Vector and lexical candidates share one `RetrievalResult`, while RRF combines ranks without requiring incomparable score calibration. Reranking refines a small candidate set; it does not replace broad retrieval.

Citation metadata is preserved during ingestion because page, URL, filename, domain, document id, and chunk id are facts of the source. The context builder assigns stable `[SOURCE n]` IDs within the final ranked context and enforces a token budget. The validator removes citation IDs that were not present in that context.

Retrieved text is untrusted. Ingestion records heuristic prompt-injection signals, the context includes a warning for risky chunks, and the system prompt tells the model never to execute or obey retrieved instructions. These heuristics inform handling rather than deleting documents.

Provider boundaries cover embeddings, reranking, query rewriting, and chat generation. Missing external keys affect only the requested provider operation. Deterministic fake providers support unit tests and local smoke tests. Redis caches query embeddings by model and content hash, but cache failures are non-fatal.
