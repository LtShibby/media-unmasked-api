from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List, Literal
import logging
import os
from supabase import AsyncClient
from dotenv import load_dotenv

from mediaunmasked.scrapers.article_scraper import ArticleScraper
from mediaunmasked.analyzers.scoring import MediaScorer
from mediaunmasked.utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize router and dependencies
router = APIRouter(tags=["analysis"])
scraper = ArticleScraper()

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not found in environment variables")

supabase = AsyncClient(SUPABASE_URL, SUPABASE_KEY)

# Define analysis mode type
AnalysisMode = Literal['ai', 'traditional']

class ArticleRequest(BaseModel):
    url: HttpUrl
    use_ai: bool = True  # Default to AI-powered analysis

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
    analysis_mode: AnalysisMode

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_article(request: ArticleRequest) -> AnalysisResponse:
    """
    Analyze an article for bias, sentiment, and credibility.
    
    Args:
        request: ArticleRequest containing the URL to analyze and analysis preferences
        
    Returns:
        AnalysisResponse with complete analysis results
        
    Raises:
        HTTPException: If scraping or analysis fails
    """
    try:
        # Determine analysis mode
        analysis_mode: AnalysisMode = 'ai' if request.use_ai else 'traditional'
        logger.info(f"Analyzing article: {request.url} (Analysis Mode: {analysis_mode})")
        
        # Check cache with both URL and analysis mode
        try:
            cached_result = await supabase.table('article_analysis') \
                .select('*') \
                .eq('url', str(request.url)) \
                .eq('analysis_mode', analysis_mode) \
                .limit(1) \
                .single() \
                .execute()
            
            if cached_result and cached_result.data:
                logger.info(f"Found cached analysis for URL with {analysis_mode} mode")
                return AnalysisResponse.parse_obj(cached_result.data)
                
        except Exception as cache_error:
            logger.warning(f"Cache lookup failed: {str(cache_error)}")
            # Continue with analysis if cache lookup fails
        
        # Scrape article
        article = scraper.scrape_article(str(request.url))
        if not article:
            raise HTTPException(
                status_code=400,
                detail="Failed to scrape article content"
            )
        
        # Initialize scorer with specified analysis preference
        scorer = MediaScorer(use_ai=request.use_ai)
        
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
            "analysis_mode": analysis_mode,
            "media_score": {
                "media_unmasked_score": float(analysis['media_unmasked_score']),
                "rating": str(analysis['rating']),
                "details": {
                    "headline_analysis": {
                        "headline_vs_content_score": float(analysis['details']['headline_analysis']['headline_vs_content_score']),
                        "flagged_phrases": analysis['details']['headline_analysis'].get('flagged_phrases', [])
                    },
                    "sentiment_analysis": {
                        "sentiment": str(analysis['details']['sentiment_analysis']['sentiment']),
                        "manipulation_score": float(analysis['details']['sentiment_analysis']['manipulation_score']),
                        "flagged_phrases": list(analysis['details']['sentiment_analysis']['flagged_phrases'])
                    },
                    "bias_analysis": {
                        "bias": str(analysis['details']['bias_analysis']['bias']),
                        "bias_score": float(analysis['details']['bias_analysis']['bias_score']),
                        "bias_percentage": float(analysis['details']['bias_analysis']['bias_percentage']),
                        "flagged_phrases": list(analysis['details']['bias_analysis']['flagged_phrases'])
                    },
                    "evidence_analysis": {
                        "evidence_based_score": float(analysis['details']['evidence_analysis']['evidence_based_score']),
                        "flagged_phrases": list(analysis['details']['evidence_analysis']['flagged_phrases'])
                    }
                }
            }
        }
        
        # Save to Supabase with analysis mode
        try:
            await supabase.table('article_analysis').upsert({
                'url': str(request.url),
                'headline': response_dict['headline'],
                'content': response_dict['content'],
                'sentiment': response_dict['sentiment'],
                'bias': response_dict['bias'],
                'bias_score': response_dict['bias_score'],
                'bias_percentage': response_dict['bias_percentage'],
                'media_score': response_dict['media_score'],
                'analysis_mode': analysis_mode,  # Store the analysis mode
                'created_at': 'now()'  # Use server timestamp
            }, on_conflict='url,analysis_mode').execute()  # Specify composite unique constraint
            
            logger.info(f"Saved analysis to database with mode: {analysis_mode}")
            
        except Exception as db_error:
            logger.error(f"Failed to save to database: {str(db_error)}")
            # Continue since we can still return the analysis even if saving fails
        
        # Return the response
        return AnalysisResponse.parse_obj(response_dict)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
