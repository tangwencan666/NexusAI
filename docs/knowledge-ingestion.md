# Knowledge Ingestion Architecture

```text
File / URL / Website
        ↓
Parser → ParsedDocument / ParsedSection
        ↓
Conservative text cleaner
        ↓
Recursive paragraph/sentence chunker
        ↓
EmbeddingProvider
        ↓
PostgreSQL + pgvector
        ↓
VectorSearchService
```

## Boundaries

Every parser produces the same `ParsedDocument` contract. PDF can therefore preserve page-level sections while DOCX, Markdown, text, and HTML use the same downstream pipeline. Parser and chunker abstractions allow format-specific extraction and improved token-aware chunking without changing persistence or API routes.

Storage is also abstracted. Phase 2 uses `LocalStorageProvider` under `data/uploads`; a later MinIO implementation can implement the same save/read/delete contract.

`EmbeddingProvider` exposes the model name, dimension, single-text embedding, and batch embedding. OpenAI is the real provider. It is created lazily and a missing key affects only ingestion/search operations, not application startup or health checks. Tests use a normalized deterministic fake provider.

## Metadata and citations

Document metadata holds source-level facts such as URL, title, domain, crawl time, and published date. Chunk metadata copies the relevant source facts and adds `document_id`, `chunk_index`, and PDF `page`. Retrieval can therefore return citation-ready results without joining external systems:

- file citation: document id, original filename, page;
- web citation: document id, URL, title, domain.

## Content hashes and transactions

The pipeline computes SHA-256 after parsing and conservative cleaning. A ready document with the same hash in the same knowledge base prevents duplicate embedding and chunk storage. Duplicate checks are scoped by knowledge base.

Documents move from `pending` to `processing` and then to `ready`. Chunks, embedding vectors, hash, and the ready transition share a commit. Failures roll back partial chunk writes, clear prior chunks, and commit a `failed` status with a bounded error message.

## URL safety and crawling

Only HTTP(S) is accepted. Each initial URL and redirect target is DNS-resolved and every returned address must be public; loopback, private, link-local, multicast, reserved, unspecified, credential-bearing, and unsupported-scheme URLs are rejected. Fetches use explicit timeouts, redirect and response-size limits.

The crawler normalizes URLs, removes fragments, de-duplicates, stays on the exact hostname, applies breadth-first depth/page limits, and consults `robots.txt`. Individual page failures are logged and do not terminate the queue.
