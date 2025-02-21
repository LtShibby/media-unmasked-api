from fastapi import APIRouter, HTTPException
from mediaunmasked.schemas.requests import AnalyzeRequest
from mediaunmasked.schemas.responses import AnalyzeResponse
from mediaunmasked.services.analyzer_service import AnalyzerService
from mediaunmasked.scrapers.article_scraper import ArticleScraper # Assuming you have a scraper module
from mediaunmasked.analyzers.scoring import MediaScorer  # Assuming you have a scorer module
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

scraper = ArticleScraper()
scorer = MediaScorer()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest):
    try:
        # Scrape the article content from the provided URL
        article = scraper.scrape_article(request.url)
        if not article:
            raise HTTPException(
                status_code=400,
                detail="Failed to scrape article content"
            )

        # Perform the analysis (like your old code)
        analysis = scorer.calculate_media_score(
            article["headline"],
            article["content"]
        )

        # Construct the response
        response_dict = {
            "headline": str(article['headline']),
            "content": str(article['content']),
            "sentiment": str(analysis['details']['sentiment_analysis']['sentiment']),
            "bias": str(analysis['details']['bias_analysis']['bias']),
            "bias_score": float(analysis['details']['bias_analysis']['bias_score']),
            "bias_percentage": float(analysis['details']['bias_analysis']['bias_percentage']),
            "flagged_phrases": list(analysis['details']['sentiment_analysis']['flagged_phrases']),
            "media_score": {
                "media_unmasked_score": float(analysis['media_unmasked_score']),
                "rating": str(analysis['rating']),
                "details": {
                    "headline_analysis": {
                        "headline_vs_content_score": float(analysis['details']['headline_analysis']['headline_vs_content_score']),
                        "contradictory_phrases": analysis['details']['headline_analysis'].get('contradictory_phrases', [])
                    },
                    "sentiment_analysis": {
                        "sentiment": str(analysis['details']['sentiment_analysis']['sentiment']),
                        "manipulation_score": float(analysis['details']['sentiment_analysis']['manipulation_score']),
                        "flagged_phrases": list(analysis['details']['sentiment_analysis']['flagged_phrases'])
                    },
                    "bias_analysis": {
                        "bias": str(analysis['details']['bias_analysis']['bias']),
                        "bias_score": float(analysis['details']['bias_analysis']['bias_score']),
                        "bias_percentage": float(analysis['details']['bias_analysis']['bias_percentage'])
                    },
                    "evidence_analysis": {
                        "evidence_based_score": float(analysis['details']['evidence_analysis']['evidence_based_score'])
                    }
                }
            }
        }

        logger.info("Final response structure:")
        logger.info(response_dict)

        return AnalyzeResponse.parse_obj(response_dict)

    except Exception as e:
        logger.error(f"Analysis failed inside of analyze.py: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed inside of analyze.py: {str(e)}"
        )
