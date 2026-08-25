from datetime import date
from typing import Literal
from pydantic import BaseModel,Field

DocumentType=Literal["contract","policy","report","invoice","general"]

class ContractExtraction(BaseModel):
    parties:list[str]=Field(default_factory=list)
    effective_date:str|None=None
    expiration_date:str|None=None
    payment_terms:str|None=None
    termination_terms:str|None=None
    liability:str|None=None
    confidentiality:str|None=None
    governing_law:str|None=None
    renewal:str|None=None
    amount:str|None=None

class ExtractionResult(BaseModel):
    document_type:DocumentType
    fields:ContractExtraction

class DocumentRiskResult(BaseModel):
    rule_id:str;severity:Literal["low","medium","high"];title:str;description:str;evidence:str;page:int|None=None
