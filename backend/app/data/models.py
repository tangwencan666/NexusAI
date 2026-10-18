from typing import Any,Literal
from pydantic import BaseModel,Field


class TextToSQLResult(BaseModel):
    sql:str
    explanation:str
    tables_used:list[str]


class DataResult(BaseModel):
    columns:list[str]
    rows:list[dict[str,Any]]
    row_count:int
    truncated:bool
    execution_ms:float


class ChartSpec(BaseModel):
    type:Literal["bar","line","pie","area"]
    title:str
    x:str
    y:str
    series:list[str]=Field(default_factory=list)


class DataAnalysisResponse(BaseModel):
    sql:str
    explanation:str
    columns:list[str]
    rows:list[dict[str,Any]]
    row_count:int
    truncated:bool
    chart:ChartSpec|None
    insights:list[str]
    trace:dict[str,Any]
