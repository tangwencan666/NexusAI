export interface HealthResponse {
  status: 'ok'
}

export interface KnowledgeBase { id: string; name: string; description: string | null }
export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed'
export interface KnowledgeDocument {
  id: string; knowledge_base_id: string; source_type: 'file' | 'url' | 'website'
  original_filename: string | null; filename: string | null; url: string | null; title: string | null
  status: DocumentStatus; error_message: string | null; file_size: number | null
  chunk_count: number; created_at: string; metadata: Record<string, unknown>
}
export interface CrawlJob { id: string; status: string; pages_discovered: number; pages_processed: number; error_message: string | null }
export interface SearchResult { chunk_id: string; content: string; score: number; document_id: string; source: Record<string, string | number | null>; metadata: Record<string, unknown> }
export interface SearchResponse { query: string; results: SearchResult[] }
export interface RetrievalResult extends SearchResult { rank: number; retrieval_method: string; vector_score: number | null; lexical_score: number | null; rrf_score: number | null; rerank_score: number | null; ranks: Record<string, number> }
export interface RetrievalTrace { original_query: string; rewritten_query: string; vector_results: RetrievalResult[]; bm25_results: RetrievalResult[]; rrf_results: RetrievalResult[]; reranked_results: RetrievalResult[]; timings_ms: Record<string, number> }
export interface Citation { id: number; document_id: string; chunk_id: string; source_type: string | null; title: string | null; filename: string | null; page: number | null; url: string | null; domain: string | null }
export interface ChatResponse { answer: string; citations: Citation[]; retrieval: { original_query: string; rewritten_query: string; results_count: number }; trace: { timings_ms: Record<string, number>; token_usage: Record<string, number | null>; invalid_citations: number[] } }
