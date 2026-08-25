# Document Intelligence

`Indexed document → classification → Pydantic extraction → deterministic risk rules → summary and citations → persisted analysis`.

Supported types are contract, policy, report, invoice, and general. Contract extraction covers parties, effective/expiration dates, payment and termination terms, liability, confidentiality, governing law, renewal, and amount. The rule engine separately identifies unlimited/missing liability, automatic renewal, long payment terms, and missing termination clauses. Rule findings remain distinguishable from future LLM findings.

Summaries, extracted fields, and risks reference existing document chunks and pages. Retrieved document content is untrusted and is never executed. Comparison uses line/section-level sequence matching and returns added, removed, and modified cards; it is not represented as a professional legal redline.

API: `POST /api/v1/documents/{id}/analyze`, `GET /api/v1/documents/{id}/analysis`, and `POST /api/v1/documents/compare`. The UI is available at `/documents/intelligence`.
