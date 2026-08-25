interface ResourcePageProps { title: string; description: string; action?: string }

export function ResourcePage({ title, description, action }: ResourcePageProps) {
  return <div className="page"><header className="resource-header"><div><span className="section-kicker">NEXUSAI</span><h1>{title}</h1><p>{description}</p></div>{action && <button className="primary-button">＋ {action}</button>}</header><div className="panel empty-resource"><div className="empty-symbol">◇</div><h2>Nothing here yet</h2><p>This foundation is ready for the next phase.</p></div></div>
}
