import { useEffect, useState } from 'react'
import { getHealth } from '../api/health'

type SystemState = 'checking' | 'healthy' | 'offline'

const cards = [
  { label: 'Agents', value: '0', detail: 'Configured assistants', icon: '◇', accent: 'purple' },
  { label: 'Knowledge Bases', value: '0', detail: 'Connected sources', icon: '▱', accent: 'blue' },
  { label: 'Agent Runs', value: '0', detail: 'Runs this month', icon: '↗', accent: 'cyan' },
]

export function DashboardPage() {
  const [systemState, setSystemState] = useState<SystemState>('checking')

  useEffect(() => {
    const controller = new AbortController()
    getHealth(controller.signal)
      .then((health) => setSystemState(health.status === 'ok' ? 'healthy' : 'offline'))
      .catch(() => setSystemState('offline'))
    return () => controller.abort()
  }, [])

  return (
    <div className="page dashboard-page">
      <header className="topbar"><div className="eyebrow">OVERVIEW</div><button className="primary-button">＋ New Agent</button></header>
      <section className="hero">
        <div><h1>Good evening.</h1><p>Welcome to your enterprise AI workspace.</p></div>
        <div className="hero-orb" aria-hidden="true"><span>N</span></div>
      </section>
      <section className="stats-grid">
        {cards.map((card) => <article className="stat-card" key={card.label}><div className={`card-icon ${card.accent}`}>{card.icon}</div><div><span>{card.label}</span><strong>{card.value}</strong><small>{card.detail}</small></div></article>)}
        <article className="stat-card status-card"><div className={`status-indicator ${systemState}`}></div><div><span>System Status</span><strong className="status-text">{systemState === 'healthy' ? 'Healthy' : systemState === 'offline' ? 'Offline' : 'Checking'}</strong><small>{systemState === 'healthy' ? 'All systems operational' : systemState === 'offline' ? 'Backend unavailable' : 'Contacting backend'}</small></div></article>
      </section>
      <section className="content-grid">
        <article className="panel"><div className="panel-heading"><div><span className="section-kicker">ACTIVITY</span><h2>Recent agent runs</h2></div><button className="text-button">View all →</button></div><div className="empty-state"><div className="empty-symbol">↗</div><h3>No runs yet</h3><p>Your agent activity will appear here.</p><button className="secondary-button">Create your first agent</button></div></article>
        <article className="panel quick-start"><span className="section-kicker">GET STARTED</span><h2>Build your AI workspace</h2><p>Connect knowledge, configure an agent, and start working.</p><ol><li><span>1</span><div><strong>Create a knowledge base</strong><small>Add enterprise context</small></div></li><li><span>2</span><div><strong>Configure an agent</strong><small>Set behavior and model</small></div></li><li><span>3</span><div><strong>Launch and evaluate</strong><small>Test in your workspace</small></div></li></ol></article>
      </section>
    </div>
  )
}
