from pydantic import BaseModel

class AnalyzeResponse(BaseModel):
    headline_vs_content_score: float
    entailment_score: float
    contradiction_score: float 