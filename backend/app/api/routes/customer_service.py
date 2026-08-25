import uuid
from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.runtime.executor import AgentRuntime
from app.agents.tools.factory import build_tool_registry
from app.core.exceptions import ApplicationError
from app.db.models.agent import Agent
from app.db.models.agent_runtime import AgentRun
from app.db.models.business import CustomerOrder,CustomerProfile,RefundRequest,SupportTicket
from app.db.session import get_db
from app.schemas.customer import CustomerAssistRequest
from app.agents.tools.customer import row

router=APIRouter(prefix="/customer-service",tags=["customer-service"])

@router.get("/customers")
async def customers(db:AsyncSession=Depends(get_db))->list[dict]:return [row(x) for x in (await db.scalars(select(CustomerProfile).order_by(CustomerProfile.customer_code))).all()]

@router.get("/customers/{customer_code}")
async def customer_context(customer_code:str,db:AsyncSession=Depends(get_db))->dict:
    customer=(await db.scalars(select(CustomerProfile).where(CustomerProfile.customer_code==customer_code))).first()
    if not customer:raise ApplicationError("CUSTOMER_NOT_FOUND","Customer not found",404)
    orders=list((await db.scalars(select(CustomerOrder).where(CustomerOrder.customer_id==customer.id).order_by(CustomerOrder.ordered_at.desc()))).all())
    tickets=list((await db.scalars(select(SupportTicket).where(SupportTicket.customer_id==customer.id).order_by(SupportTicket.created_at.desc()))).all())
    refunds=list((await db.scalars(select(RefundRequest).where(RefundRequest.customer_id==customer.id).order_by(RefundRequest.created_at.desc()))).all())
    return {"customer":row(customer),"orders":[row(x) for x in orders],"tickets":[row(x) for x in tickets],"refund_requests":[row(x) for x in refunds]}

@router.post("/assist")
async def assist(payload:CustomerAssistRequest,db:AsyncSession=Depends(get_db))->dict:
    agent=await db.get(Agent,payload.agent_id)
    if not agent:raise ApplicationError("AGENT_NOT_FOUND","Customer Service Agent not found",404)
    run=AgentRun(agent_id=agent.id,workspace_id=agent.workspace_id,input=payload.message,model_provider=agent.model_provider,model_name=agent.model_name);db.add(run);await db.flush()
    state=await AgentRuntime(db,build_tool_registry()).execute(run,agent.enabled_tools,str(payload.knowledge_base_id) if payload.knowledge_base_id else None)
    return {"run_id":run.id,"status":state["status"],"answer":state.get("final_answer"),"citations":state.get("citations",[]),"approval_request_id":state.get("approval_request_id"),"tool_results":state.get("tool_results",[]),"trace":{"steps":state.get("step_count"),"duration_ms":run.total_duration_ms}}
