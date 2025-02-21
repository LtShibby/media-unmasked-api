from fastapi import APIRouter, HTTPException
from mediaunmasked.schemas.requests import AnalyzeRequest
from mediaunmasked.schemas.responses import AnalyzeResponse
from mediaunmasked.services.analyzer_service import AnalyzerService

router = APIRouter(tags=["analysis"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest):
    try:
        analyzer_service = AnalyzerService()
        result = await analyzer_service.analyze_content(
            headline=request.headline,
            content=request.content
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 