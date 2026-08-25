import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { addUrl, crawlWebsite, deleteDocument, listDocuments, listKnowledgeBases, uploadDocument } from '../api/knowledge'
import type { CrawlJob, KnowledgeBase, KnowledgeDocument } from '../types/api'

type Modal = 'upload' | 'url' | 'crawl' | null

export function KnowledgePage() {
  const [bases, setBases] = useState<KnowledgeBase[]>([])
  const [selected, setSelected] = useState('')
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [modal, setModal] = useState<Modal>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [crawl, setCrawl] = useState<CrawlJob | null>(null)

  useEffect(() => { listKnowledgeBases().then(items => { setBases(items); if (items[0]) setSelected(items[0].id) }).catch(err => setError(err.message)) }, [])
  const refresh = () => selected && listDocuments(selected).then(setDocuments).catch(err => setError(err.message))
  useEffect(() => { refresh() }, [selected])
  const run = async (action: () => Promise<unknown>) => { setBusy(true); setError(''); try { await action(); setModal(null); refresh() } catch (err) { setError(err instanceof Error ? err.message : 'Request failed') } finally { setBusy(false) } }

  return <div className="page knowledge-page">
    <header className="resource-header"><div><span className="section-kicker">KNOWLEDGE</span><h1>Knowledge Base</h1><p>Ingest files and websites into retrieval-ready enterprise context.</p></div><select className="field select" value={selected} onChange={event => setSelected(event.target.value)}><option value="">Select a knowledge base</option>{bases.map(base => <option key={base.id} value={base.id}>{base.name}</option>)}</select></header>
    {error && <div className="error-banner">{error}</div>}
    {!selected ? <div className="panel empty-resource"><div className="empty-symbol">▱</div><h2>No knowledge base selected</h2><p>Create one through the API, then return here to add sources.</p></div> : <>
      <div className="knowledge-tabs"><button className="tab active">Documents</button><Link className="tab" to={`/knowledge/${selected}/search`}>Search</Link><Link className="tab" to={`/knowledge/${selected}/chat`}>Chat</Link><button className="tab">Settings</button></div>
      <div className="action-row"><button className="primary-button" onClick={() => setModal('upload')}>↑ Upload File</button><button className="secondary-button" onClick={() => setModal('url')}>＋ Add URL</button><button className="secondary-button" onClick={() => setModal('crawl')}>◎ Crawl Website</button></div>
      {crawl && <div className="crawl-summary">Crawl {crawl.status}: {crawl.pages_processed}/{crawl.pages_discovered} pages processed</div>}
      <div className="panel document-table"><div className="table-row table-head"><span>Name</span><span>Source</span><span>Status</span><span>Chunks</span><span>Created</span><span></span></div>{documents.length === 0 ? <div className="table-empty">No documents yet. Add a source to begin ingestion.</div> : documents.map(doc => <div className="table-row" key={doc.id}><span className="doc-name">{doc.original_filename ?? doc.title ?? doc.url ?? 'Untitled'}<small>{doc.error_message}</small></span><span>{doc.source_type}</span><span><i className={`status-badge ${doc.status}`}>{doc.status}</i></span><span>{doc.chunk_count}</span><span>{new Date(doc.created_at).toLocaleDateString()}</span><button className="delete-button" onClick={() => run(() => deleteDocument(doc.id))}>×</button></div>)}</div>
    </>}
    {modal === 'upload' && <ModalShell title="Upload document" close={() => setModal(null)}><form onSubmit={event => { event.preventDefault(); const file = new FormData(event.currentTarget).get('file'); if (file instanceof File && file.size) run(() => uploadDocument(selected, file)) }}><label className="drop-zone">Drop or choose PDF, DOCX, TXT, MD<input name="file" type="file" accept=".pdf,.docx,.txt,.md" required /></label><button disabled={busy} className="primary-button">{busy ? 'Processing…' : 'Upload & process'}</button></form></ModalShell>}
    {modal === 'url' && <ModalShell title="Add webpage URL" close={() => setModal(null)}><form onSubmit={event => { event.preventDefault(); const url = String(new FormData(event.currentTarget).get('url')); run(() => addUrl(selected, url)) }}><input className="field" name="url" type="url" placeholder="https://example.com/article" required /><button disabled={busy} className="primary-button">{busy ? 'Processing…' : 'Add URL'}</button></form></ModalShell>}
    {modal === 'crawl' && <ModalShell title="Crawl website" close={() => setModal(null)}><form onSubmit={event => { event.preventDefault(); const data = new FormData(event.currentTarget); run(async () => setCrawl(await crawlWebsite(selected, String(data.get('url')), Number(data.get('pages')), Number(data.get('depth'))))) }}><input className="field" name="url" type="url" placeholder="https://example.com" required /><div className="form-grid"><label>Max pages<input className="field" name="pages" type="number" min="1" max="100" defaultValue="20" /></label><label>Max depth<input className="field" name="depth" type="number" min="0" max="5" defaultValue="2" /></label></div><button disabled={busy} className="primary-button">{busy ? 'Crawling…' : 'Start crawl'}</button></form></ModalShell>}
  </div>
}

function ModalShell({ title, close, children }: { title: string; close: () => void; children: React.ReactNode }) { return <div className="modal-backdrop" onMouseDown={close}><div className="modal" onMouseDown={event => event.stopPropagation()}><div className="modal-title"><h2>{title}</h2><button onClick={close}>×</button></div>{children}</div></div> }
