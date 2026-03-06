from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class IngestRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = Field(default="upload", max_length=256)
    metadata: Optional[dict] = None


class GreenAIResponse(BaseModel):
    final_answer: str
    risk_score: str  # Low | Medium | High
    sources_used: List[dict] = Field(default_factory=list)
    retrieval_time: str
    generation_time: str
    token_usage_note: Optional[str] = None
