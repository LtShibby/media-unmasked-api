from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    headline: str
    content: str 