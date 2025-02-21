from typing import Dict, Any
import logging

from .headline_analyzer import HeadlineAnalyzer
from .sentiment_analyzer import SentimentAnalyzer
from .bias_analyzer import BiasAnalyzer
from .evidence_analyzer import EvidenceAnalyzer

logger = logging.getLogger(__name__)

class MediaScorer:
    def __init__(self):
        """Initialize the MediaScorer with required analyzers."""
        self.headline_analyzer = HeadlineAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.bias_analyzer = BiasAnalyzer()
        self.evidence_analyzer = EvidenceAnalyzer()

    def calculate_media_score(self, headline: str, content: str) -> Dict[str, Any]:
        """Calculate final media credibility score."""
        try:
            headline_analysis = self.headline_analyzer.analyze(headline, content)
            sentiment_analysis = self.sentiment_analyzer.analyze(content)
            bias_analysis = self.bias_analyzer.analyze(content)
            evidence_analysis = self.evidence_analyzer.analyze(content)
            
            # Log intermediate results
            logger.info("\n=== Raw Analysis Results ===")
            logger.info(f"Headline Analysis: {headline_analysis}")
            logger.info(f"Sentiment Analysis: {sentiment_analysis}")
            logger.info(f"""Bias Analysis: 
                Raw: {bias_analysis}
                Label: {bias_analysis['bias']}
                Score: {bias_analysis['bias_score']}
                Percentage: {bias_analysis['bias_percentage']}%
            """)
            logger.info(f"Evidence Analysis: {evidence_analysis}")
            
            # Calculate component scores
            # For headline: 20% contradiction = 20% score (don't invert)
            headline_score = headline_analysis["headline_vs_content_score"] / 100
            
            # For manipulation: 0% = good (use directly), 100% = bad
            manipulation_score = (100 - sentiment_analysis["manipulation_score"]) / 100
            
            # For bias: 0% = good (use directly), 100% = bad
            bias_score = (100 - bias_analysis["bias_percentage"]) / 100
            
            evidence_score = evidence_analysis["evidence_based_score"] / 100  # Higher is better
            
            logger.info(f"""Component Scores:
                Headline: {headline_score * 100:.1f}% (from {headline_analysis["headline_vs_content_score"]}%)
                Evidence: {evidence_score * 100:.1f}%
                Manipulation: {manipulation_score * 100:.1f}% (100 - {sentiment_analysis["manipulation_score"]}%)
                Bias: {bias_score * 100:.1f}% (100 - {bias_analysis["bias_percentage"]}%)
            """)
            
            # Calculate final score
            final_score = (
                (headline_score * 0.25) +
                (manipulation_score * 0.25) +
                (bias_score * 0.25) +
                (evidence_score * 0.25)
            ) * 100
            
            # Determine rating
            if final_score >= 80:
                rating = "Trustworthy"
            elif final_score >= 50:
                rating = "Bias Present"
            else:
                rating = "Misleading"
            
            result = {
                "media_unmasked_score": round(final_score, 1),
                "rating": rating,
                "details": {
                    "headline_analysis": headline_analysis,
                    "sentiment_analysis": sentiment_analysis,
                    "bias_analysis": bias_analysis,
                    "evidence_analysis": evidence_analysis
                }
            }
            
            logger.info("\n=== Final Score Result ===")
            logger.info(f"Result: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating media score: {str(e)}")
            return {
                "media_unmasked_score": 0,
                "rating": "Error",
                "details": {
                    "headline_analysis": {"headline_vs_content_score": 0, "contradictory_phrases": []},
                    "sentiment_analysis": {"sentiment": "Error", "manipulation_score": 0, "flagged_phrases": []},
                    "bias_analysis": {"bias": "Error", "bias_score": 0.0, "bias_percentage": 0},
                    "evidence_analysis": {"evidence_based_score": 0}
                }
            } 