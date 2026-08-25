# Customer Service

Customer Service is an Agent Runtime configuration, not another runtime. Its default permission set is `customer.lookup`, `order.lookup`, `knowledge_search`, `ticket.create`, `refund.prepare`, and `refund.create`; arbitrary HTTP and web search are excluded.

Read tools return customer, order, ticket, and eligibility evidence. `refund.prepare` is deterministic and read-only. `ticket.create` and `refund.create` are approval-gated. The high-risk refund call is persisted, the graph stops, and the exact saved arguments execute only after approval and resume. Duplicate pending refund requests are idempotent.

Tool results and policies remain untrusted observations. Policy citations come from the existing Phase 3 Hybrid Retriever. API endpoints are under `/api/v1/customer-service`; approval and resume reuse Phase 4 APIs. The UI at `/customer-service` presents customers, service chat, customer/order context, results, citations, and trace data.
