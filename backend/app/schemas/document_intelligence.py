import uuid
from typing import Literal
from pydantic import BaseModel

class DocumentAnalyzeRequest(BaseModel):document_type:Literal["contract","policy","report","invoice","general"]|None=None
class DocumentCompareRequest(BaseModel):document_a_id:uuid.UUID;document_b_id:uuid.UUID
