import uuid
from datetime import UTC,datetime
from decimal import Decimal
from pydantic import BaseModel,Field
from sqlalchemy import select

from app.agents.tools.base import BaseTool,RiskLevel,ToolContext,ToolResult
from app.db.models.business import CustomerOrder,CustomerProfile,RefundRequest,SupportTicket


def row(model)->dict:
    return {column.name:(str(value) if isinstance(value,(uuid.UUID,datetime,Decimal)) else value) for column in model.__table__.columns if (value:=getattr(model,column.name)) is not None}


class CustomerLookupInput(BaseModel):customer_code:str
class CustomerLookupTool(BaseTool):
    name="customer.lookup";description="Look up a customer profile by customer code.";input_schema=CustomerLookupInput
    async def execute(self,context:ToolContext,params:CustomerLookupInput)->ToolResult:
        item=(await context.session.scalars(select(CustomerProfile).where(CustomerProfile.customer_code==params.customer_code))).first()
        return ToolResult(bool(item),row(item) if item else None,None if item else "Customer not found")


class OrderLookupInput(BaseModel):customer_code:str;latest:bool=True;order_code:str|None=None
class OrderLookupTool(BaseTool):
    name="order.lookup";description="Read customer order and shipping/refund status.";input_schema=OrderLookupInput
    async def execute(self,context:ToolContext,params:OrderLookupInput)->ToolResult:
        query=select(CustomerOrder).join(CustomerProfile).where(CustomerProfile.customer_code==params.customer_code)
        if params.order_code:query=query.where(CustomerOrder.order_code==params.order_code)
        items=list((await context.session.scalars(query.order_by(CustomerOrder.ordered_at.desc()).limit(1 if params.latest else 20))).all())
        return ToolResult(bool(items),[row(item) for item in items],None if items else "Order not found")


class TicketListInput(BaseModel):customer_code:str
class TicketListTool(BaseTool):
    name="ticket.list";description="List support tickets for a customer.";input_schema=TicketListInput
    async def execute(self,context:ToolContext,params:TicketListInput)->ToolResult:
        items=list((await context.session.scalars(select(SupportTicket).join(CustomerProfile).where(CustomerProfile.customer_code==params.customer_code).order_by(SupportTicket.created_at.desc()))).all());return ToolResult(True,[row(x) for x in items])


class TicketCreateInput(BaseModel):customer_id:uuid.UUID;subject:str;description:str;priority:str="normal"
class TicketCreateTool(BaseTool):
    name="ticket.create";description="Create a support ticket after approval.";input_schema=TicketCreateInput;risk_level=RiskLevel.MEDIUM;requires_approval=True
    async def execute(self,context:ToolContext,params:TicketCreateInput)->ToolResult:
        item=SupportTicket(**params.model_dump());context.session.add(item);await context.session.flush();return ToolResult(True,row(item))


class RefundPrepareInput(BaseModel):order_code:str|None=None;customer_code:str|None=None;reason:str="Customer request"
class RefundPrepareTool(BaseTool):
    name="refund.prepare";description="Prepare a refund eligibility assessment without writing data.";input_schema=RefundPrepareInput
    async def execute(self,context:ToolContext,params:RefundPrepareInput)->ToolResult:
        query=select(CustomerOrder)
        if params.order_code:query=query.where(CustomerOrder.order_code==params.order_code)
        elif params.customer_code:query=query.join(CustomerProfile).where(CustomerProfile.customer_code==params.customer_code).order_by(CustomerOrder.ordered_at.desc())
        else:return ToolResult(False,error="order_code or customer_code is required")
        order=(await context.session.scalars(query.limit(1))).first()
        if not order:return ToolResult(False,error="Order not found")
        age=(datetime.now(UTC)-order.ordered_at).days;eligible=order.status=="delivered" and age<=30 and order.refund_status=="none"
        return ToolResult(True,{"order_id":str(order.id),"order_code":order.order_code,"customer_id":str(order.customer_id),"amount":float(order.amount),"age_days":age,"eligible":eligible,"reason":params.reason,"policy_assumption":"delivered within 30 days and not previously refunded"})


class RefundCreateInput(BaseModel):order_code:str;reason:str
class RefundCreateTool(BaseTool):
    name="refund.create";description="Create an approved refund request.";input_schema=RefundCreateInput;risk_level=RiskLevel.HIGH;requires_approval=True
    async def execute(self,context:ToolContext,params:RefundCreateInput)->ToolResult:
        order=(await context.session.scalars(select(CustomerOrder).where(CustomerOrder.order_code==params.order_code))).first()
        if not order:return ToolResult(False,error="Order not found")
        existing=(await context.session.scalars(select(RefundRequest).where(RefundRequest.order_id==order.id,RefundRequest.status=="pending"))).first()
        if existing:return ToolResult(True,{**row(existing),"idempotent":True})
        item=RefundRequest(customer_id=order.customer_id,order_id=order.id,amount=order.amount,reason=params.reason,status="pending");context.session.add(item);await context.session.flush();return ToolResult(True,{**row(item),"idempotent":False})
