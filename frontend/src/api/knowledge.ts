import { apiGet, apiRequest } from './client'
import type { ChatResponse, CrawlJob, KnowledgeBase, KnowledgeDocument, RetrievalTrace, SearchResponse } from '../types/api'

export const listKnowledgeBases = () => apiGet<KnowledgeBase[]>('/api/v1/knowledge-bases')
export const listDocuments = (id: string) => apiGet<KnowledgeDocument[]>(`/api/v1/knowledge-bases/${id}/documents`)
export const uploadDocument = (id: string, file: File) => {
  const body = new FormData(); body.append('file', file)
  return apiRequest<KnowledgeDocument>(`/api/v1/knowledge-bases/${id}/documents/upload`, { method: 'POST', body })
}
export const addUrl = (id: string, url: string) => apiRequest<KnowledgeDocument>(`/api/v1/knowledge-bases/${id}/documents/url`, { method: 'POST', body: JSON.stringify({ url }) })
export const crawlWebsite = (id: string, root_url: string, max_pages: number, max_depth: number) => apiRequest<CrawlJob>(`/api/v1/knowledge-bases/${id}/website-crawls`, { method: 'POST', body: JSON.stringify({ root_url, max_pages, max_depth }) })
export const searchKnowledge = (id: string, query: string, top_k: number) => apiRequest<SearchResponse>(`/api/v1/knowledge-bases/${id}/search`, { method: 'POST', body: JSON.stringify({ query, top_k }) })
export const deleteDocument = (id: string) => apiRequest<void>(`/api/v1/documents/${id}`, { method: 'DELETE' })
export const debugRetrieval = (id: string, query: string, mode: string, top_k: number) => apiRequest<RetrievalTrace>(`/api/v1/knowledge-bases/${id}/retrieve`, { method: 'POST', body: JSON.stringify({ query, mode, top_k }) })
export const chatKnowledge = (id: string, message: string, recent_messages: string[] = []) => apiRequest<ChatResponse>(`/api/v1/knowledge-bases/${id}/chat`, { method: 'POST', body: JSON.stringify({ message, recent_messages }) })
