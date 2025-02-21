from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Any, List
import logging
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mediaunmasked.scrapers.article_scraper import ArticleScraper
from mediaunmasked.analyzers.scoring import MediaScorer
from mediaunmasked.utils.logging_config import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI with dependencies
app = FastAPI()
scraper = ArticleScraper()
scorer = MediaScorer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/analyze", response_model=AnalysisResponse)
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
        
        # Ensure correct types in response
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
        
        # Log the final structure
        logger.info("Final response structure:")
        logger.info(response_dict)
        
        return AnalysisResponse.parse_obj(response_dict)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/api/debug")
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