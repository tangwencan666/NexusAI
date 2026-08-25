import uuid
from pydantic import BaseModel,Field

class CustomerAssistRequest(BaseModel):
    agent_id:uuid.UUID
    message:str=Field(min_length=1,max_length=10000)
    knowledge_base_id:uuid.UUID|None=None

class TicketCreateRequest(BaseModel):
    agent_id:uuid.UUID
    customer_id:uuid.UUID
    subject:str
    description:str
    priority:str="normal"
