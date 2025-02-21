from mediaunmasked.analyzers.headline_analyzer import HeadlineAnalyzer
from mediaunmasked.schemas.requests import AnalyzeRequest, AnalysisResponse
from fastapi import HTTPException
from mediaunmasked.scrapers.article_scraper import ArticleScraper
from mediaunmasked.analyzers.scoring import MediaScorer
import logging

logger = logging.getLogger(__name__)
scraper = ArticleScraper()
scorer = MediaScorer()

class AnalyzerService:
    def __init__(self):
        self.headline_analyzer = HeadlineAnalyzer()

    async def analyze_content(self, headline: str, content: str):
        result = self.headline_analyzer.analyze(headline, content)
        return result 

    async def analyze_url(self, request: AnalyzeRequest) -> AnalysisResponse:
        """
        Analyze an article for bias, sentiment, and credibility.
        """
        try:
            logger.info(f"Analyzing article: {request.url}")
            
            # Scrape article (now synchronous)
            article = scraper.scrape_article(request.get_url_str())
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
            
            # Construct response
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
            
            return AnalysisResponse.parse_obj(response_dict)
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            ) 