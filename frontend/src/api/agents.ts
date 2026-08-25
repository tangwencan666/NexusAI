import { apiGet, apiRequest } from './client'
export type Agent = { id:string; workspace_id:string; name:string; model_provider:string; model_name:string; max_steps:number; enabled_tools:string[] }
export type AgentRun = { id:string; agent_id:string|null; workspace_id:string; status:string; input:string; final_answer:string|null; error:string|null; step_count:number; total_duration_ms:number|null; state:Record<string,unknown>; created_at:string }
export type Tool = { name:string; description:string; risk_level:string; requires_approval:boolean; timeout_seconds:number }
export const listAgents=()=>apiGet<Agent[]>('/api/v1/agents')
export const runAgent=(id:string,message:string,knowledgeBaseId?:string)=>apiRequest<AgentRun>(`/api/v1/agents/${id}/runs`,{method:'POST',body:JSON.stringify({message,knowledge_base_id:knowledgeBaseId||null,debug:true})})
export const listRuns=()=>apiGet<AgentRun[]>('/api/v1/agent-runs')
export const decideApproval=(id:string,approved:boolean)=>apiRequest(`/api/v1/agent-approvals/${id}/${approved?'approve':'reject'}`,{method:'POST',body:'{}'})
export const resumeRun=(id:string)=>apiRequest<AgentRun>(`/api/v1/agent-runs/${id}/resume`,{method:'POST',body:'{}'})
export const listTools=()=>apiGet<Tool[]>('/api/v1/tools')
