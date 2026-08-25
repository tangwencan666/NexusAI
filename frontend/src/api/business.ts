import{apiGet,apiRequest}from'./client'
export type DataSource={id:string;name:string;type:string;description:string|null;allowed_tables:string[];connection_config:Record<string,unknown>}
export type Analysis={sql:string;explanation:string;columns:string[];rows:Array<Record<string,unknown>>;row_count:number;truncated:boolean;chart:{type:string;title:string;x:string;y:string;series:string[]}|null;insights:string[];trace:Record<string,number>}
export const listDataSources=()=>apiGet<DataSource[]>('/api/v1/data-sources')
export const analyzeData=(id:string,question:string)=>apiRequest<Analysis>(`/api/v1/data-sources/${id}/analyze`,{method:'POST',body:JSON.stringify({question})})
export type Customer={id:string;customer_code:string;name:string;email:string;tier:string}
export const listCustomers=()=>apiGet<Customer[]>('/api/v1/customer-service/customers')
export const customerContext=(code:string)=>apiGet<Record<string,unknown>>(`/api/v1/customer-service/customers/${code}`)
export const customerAssist=(agent_id:string,message:string,knowledge_base_id:string)=>apiRequest<Record<string,unknown>>('/api/v1/customer-service/assist',{method:'POST',body:JSON.stringify({agent_id,message,knowledge_base_id:knowledge_base_id||null})})
export const analyzeDocument=(id:string,type?:string)=>apiRequest<Record<string,unknown>>(`/api/v1/documents/${id}/analyze`,{method:'POST',body:JSON.stringify({document_type:type||null})})
export const compareDocuments=(a:string,b:string)=>apiRequest<Record<string,unknown>>('/api/v1/documents/compare',{method:'POST',body:JSON.stringify({document_a_id:a,document_b_id:b})})
