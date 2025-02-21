from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List
import logging
import os
from supabase import create_client

from mediaunmasked.scrapers.article_scraper import ArticleScraper
from mediaunmasked.analyzers.scoring import MediaScorer
from mediaunmasked.utils.logging_config import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize router and dependencies
router = APIRouter(tags=["analysis"])
scraper = ArticleScraper()
scorer = MediaScorer()

# Initialize Supabase connection (works for async environments)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)  # This works for async

class ArticleRequest(BaseModel):
    url: HttpUrl

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
    flagged_phrases: List[str]
    media_score: MediaScore

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_article(request: ArticleRequest) -> AnalysisResponse:
    """
    Analyze an article for bias, sentiment, and credibility.
    
    Args:
        request: ArticleRequest containing the URL to analyze
        
    Returns:
        AnalysisResponse with complete analysis results
        
    Raises:
        HTTPException: If scraping or analysis fails
    """
    try:
        logger.info(f"Analyzing article: {request.url}")
        
        # Check if the article has already been analyzed
        existing_article = await supabase.table('article_analysis').select('*').eq('url', str(request.url)).execute()
        
        if existing_article.status_code == 200 and existing_article.data:
            logger.info("Article already analyzed. Returning cached data.")
            # Return the existing analysis result if it exists
            cached_data = existing_article.data[0]
            return AnalysisResponse.parse_obj(cached_data)
        
        # Scrape article
        article = scraper.scrape_article(str(request.url))
        if not article:
            raise HTTPException(
                status_code=400,
                detail="Failed to scrape article content"
            )
        
        # Analyze content
        analysis = scorer.calculate_media_score(
            article["headline"],
            article["content"]
        )
        
        # Log raw values for debugging
        logger.info("Raw values:")
        logger.info(f"media_unmasked_score type: {type(analysis['media_unmasked_score'])}")
        logger.info(f"media_unmasked_score value: {analysis['media_unmasked_score']}")
        
        # Prepare response data
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
        
        # Save the new analysis to Supabase
        await supabase.table('article_analysis').upsert({
            'url': str(request.url),
            'headline': response_dict['headline'],
            'content': response_dict['content'],
            'sentiment': response_dict['sentiment'],
            'bias': response_dict['bias'],
            'bias_score': response_dict['bias_score'],
            'bias_percentage': response_dict['bias_percentage'],
            'flagged_phrases': response_dict['flagged_phrases'],
            'media_score': response_dict['media_score']
        }).execute()
        
        # Return the response
        return AnalysisResponse.parse_obj(response_dict)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/debug")
async def debug_response():
    mock_analysis = {
        "headline": "Test Headline",
        "content": "Test content",
        "sentiment": "Neutral",
        "bias": "Neutral",
        "bias_score": 0.75,  # Note: 0-1 scale
        "bias_percentage": 0,
        "flagged_phrases": ["test phrase"],
        "media_score": {
            "media_unmasked_score": 75.5,
            "rating": "Some Bias Present",
            "details": {
                "headline_analysis": {
                    "headline_vs_content_score": 20,
                    "contradictory_phrases": ["Sample contradiction"]
                },
                "sentiment_analysis": {
                    "sentiment": "Neutral",
                    "manipulation_score": 30,
                    "flagged_phrases": ["Sample manipulative phrase"]
                },
                "bias_analysis": {
                    "bias": "Neutral",
                    "bias_score": 0.75,
                    "bias_percentage": 0
                },
                "evidence_analysis": {
                    "evidence_based_score": 80
                }
            }
        }
    }
    return AnalysisResponse.parse_obj(mock_analysis)
