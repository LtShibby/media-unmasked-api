import logging
from typing import Dict, Any, List
from textblob import TextBlob

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.manipulative_patterns = [
            "experts say",
            "sources claim",
            "many believe",
            "some say",
            "everyone knows",
            "clearly",
            "obviously",
            "without doubt",
            "certainly"
        ]

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob."""
        try:
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity
            
            manipulative_phrases = self._detect_manipulative_phrases(text)
            manipulation_score = len(manipulative_phrases) * 10
            
            if sentiment_score > 0.2:
                sentiment = "Positive"
            elif sentiment_score < -0.2:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
            
            if manipulation_score > 50:
                sentiment = "Manipulative"
            
            return {
                "sentiment": sentiment,
                "manipulation_score": min(manipulation_score, 100),
                "flagged_phrases": manipulative_phrases
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {
                "sentiment": "Error",
                "manipulation_score": 0,
                "flagged_phrases": []
            }

    def _detect_manipulative_phrases(self, text: str) -> List[str]:
        """Detect potentially manipulative phrases."""
        found_phrases = []
        text_lower = text.lower()
        
        for pattern in self.manipulative_patterns:
            if pattern in text_lower:
                start = text_lower.find(pattern)
                context = text[max(0, start-20):min(len(text), start+len(pattern)+20)]
                found_phrases.append(context.strip())
        
        return found_phrases 