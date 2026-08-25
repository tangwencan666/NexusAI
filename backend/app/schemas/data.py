import uuid
from datetime import datetime
from typing import Any,Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from app.data.models import DataAnalysisResponse


class DataSourceCreate(BaseModel):
    workspace_id:uuid.UUID
    name:str=Field(min_length=1,max_length=200)
    type:Literal["postgresql","mysql","demo"]="postgresql"
    description:str|None=None
    connection_config:dict[str,Any]=Field(default_factory=lambda:{"connection":"application_database"})
    allowed_schemas:list[str]=Field(default_factory=lambda:["public"])
    allowed_tables:list[str]=Field(default_factory=list)
    is_active:bool=True

    @model_validator(mode="after")
    def credentials_must_be_references(self):
        for key,value in self.connection_config.items():
            if key.lower() in {"password","secret","token","api_key"} and not (isinstance(value,str) and value.startswith("env:")):
                raise ValueError(f"{key} must be an env:VARIABLE reference, not a plaintext credential")
        return self


class DataSourceRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:uuid.UUID;workspace_id:uuid.UUID;name:str;type:str;description:str|None;connection_config:dict[str,Any];allowed_schemas:list[str];allowed_tables:list[str];is_active:bool;created_at:datetime;updated_at:datetime


class AnalyzeRequest(BaseModel):question:str=Field(min_length=2,max_length=5000)

__all__=["DataSourceCreate","DataSourceRead","AnalyzeRequest","DataAnalysisResponse"]
