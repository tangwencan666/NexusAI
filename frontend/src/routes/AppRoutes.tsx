import { Route, Routes } from 'react-router-dom'
import { AppLayout } from '../layouts/AppLayout'
import { ComingSoonPage } from '../pages/ComingSoonPage'
import { DashboardPage } from '../pages/DashboardPage'
import { ResourcePage } from '../pages/ResourcePage'
import { KnowledgePage } from '../pages/KnowledgePage'
import { KnowledgeSearchPage } from '../pages/KnowledgeSearchPage'
import { KnowledgeChatPage } from '../pages/KnowledgeChatPage'
import { AgentsPage } from '../pages/AgentsPage'
import { AgentPlaygroundPage } from '../pages/AgentPlaygroundPage'
import { AgentRunsPage } from '../pages/AgentRunsPage'
import { ToolsPage } from '../pages/ToolsPage'
import { DataAnalystPage } from '../pages/DataAnalystPage'
import { CustomerServicePage } from '../pages/CustomerServicePage'
import { DocumentIntelligencePage } from '../pages/DocumentIntelligencePage'

export function AppRoutes() {
  return <Routes><Route element={<AppLayout />}><Route index element={<DashboardPage />} /><Route path="agents" element={<AgentsPage />} /><Route path="agents/:id/playground" element={<AgentPlaygroundPage />} /><Route path="agent-runs" element={<AgentRunsPage />} /><Route path="tools" element={<ToolsPage />} /><Route path="data" element={<DataAnalystPage />} /><Route path="customer-service" element={<CustomerServicePage />} /><Route path="documents" element={<DocumentIntelligencePage />} /><Route path="documents/intelligence" element={<DocumentIntelligencePage />} /><Route path="knowledge" element={<KnowledgePage />} /><Route path="knowledge/:id/search" element={<KnowledgeSearchPage />} /><Route path="knowledge/:id/chat" element={<KnowledgeChatPage />} /><Route path="settings" element={<ResourcePage title="Settings" description="Manage workspace preferences and platform configuration." />} />{['evaluation', 'observability'].map((path) => <Route key={path} path={path} element={<ComingSoonPage title={path[0].toUpperCase() + path.slice(1)} />} />)}<Route path="*" element={<ComingSoonPage title="Page not found" />} /></Route></Routes>
}
