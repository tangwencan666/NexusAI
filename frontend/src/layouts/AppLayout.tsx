import { NavLink, Outlet } from 'react-router-dom'
import { Icon } from '../components/Icons'

const navigation = [
  { label: 'Dashboard', to: '/', icon: '⌂' },
  { label: 'Agents', to: '/agents', icon: '◇' },
  { label: 'Runs', to: '/agent-runs', icon: '↻' },
  { label: 'Tools', to: '/tools', icon: '⛓' },
  { label: 'Knowledge', to: '/knowledge', icon: '▱' },
  { label: 'Data', to: '/data', icon: '⌘' },
  { label: 'Customer Service', to: '/customer-service', icon: '☵' },
  { label: 'Documents', to: '/documents', icon: '□' },
  { label: 'Evaluation', to: '/evaluation', icon: '✓' },
  { label: 'Observability', to: '/observability', icon: '◉' },
]

export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">N</span><span>NexusAI</span></div>
        <nav className="nav-list">
          {navigation.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/'} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <Icon>{item.icon}</Icon>{item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <NavLink to="/settings" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <Icon>⚙</Icon>Settings
          </NavLink>
          <div className="profile"><span className="avatar">NA</span><div><strong>Nexus Admin</strong><small>Workspace Owner</small></div></div>
        </div>
      </aside>
      <main className="main-content"><Outlet /></main>
    </div>
  )
}
