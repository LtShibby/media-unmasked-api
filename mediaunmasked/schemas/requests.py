from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List

class AnalyzeRequest(BaseModel):
    url: HttpUrl
    
    def get_url_str(self) -> str:
        # Convert HttpUrl to string safely
        return str(self.url)

class MediaScoreDetails(BaseModel):
    headline_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    bias_analysis: Dict[str, Any]
    evidence_analysis: Dict[str, Any]

class MediaScore(BaseModel):
    media_unmasked_score: float
    rating: str
    details: MediaScoreDetails

class AnalysisResponse(BaseModel):
    headline: str
    content: str
    sentiment: str
    bias: str
    bias_score: float
    bias_percentage: float
    media_score: MediaScore