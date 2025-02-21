import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BiasAnalyzer:
    def __init__(self):
        self.resources_dir = os.path.join(os.path.dirname(__file__), '..', 'resources')
        self.left_keywords = self._load_keywords('left_bias_words.txt')
        self.right_keywords = self._load_keywords('right_bias_words.txt')

    def _load_keywords(self, filename: str) -> List[str]:
        """Load keywords from file."""
        try:
            filepath = os.path.join(self.resources_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            logger.error(f"Error loading {filename}: {str(e)}")
            return []

    def analyze(self, text: str) -> Dict[str, Any]:
        """Detect bias using keyword analysis."""
        try:
            text_lower = text.lower()
            
            # Count matches
            left_count = sum(1 for word in self.left_keywords if word in text_lower)
            right_count = sum(1 for word in self.right_keywords if word in text_lower)
            
            total_words = left_count + right_count
            if total_words == 0:
                return {
                    "bias": "Neutral",
                    "bias_score": 0.0,  # True neutral
                    "bias_percentage": 0  # Neutral percentage
                }
            
            # New bias score formula (-1.0 left, 0.0 neutral, 1.0 right)
            bias_score = (right_count - left_count) / total_words
            
            # Convert bias_score to percentage (-100% to +100%)
            bias_percentage = bias_score * 100
            logger.info(f"Bias score: {bias_score:.2f}, Bias percentage: {bias_percentage:.1f}%")
            
            # Determine bias label
            if bias_score < -0.8:
                bias = "Strongly Left"
            elif bias_score < -0.5:
                bias = "Moderately Left"
            elif bias_score < -0.2:
                bias = "Leaning Left"
            elif bias_score > 0.8:
                bias = "Strongly Right"
            elif bias_score > 0.5:
                bias = "Moderately Right"
            elif bias_score > 0.2:
                bias = "Leaning Right"
            else:
                bias = "Neutral"
            
            return {
                "bias": bias,
                "bias_score": round(bias_score, 2),  # Keep 2 decimal places
                "bias_percentage": abs(round(bias_percentage, 1))
            }
            
        except Exception as e:
            logger.error(f"Error in bias analysis: {str(e)}")
            return {
                "bias": "Error",
                "bias_score": 0.0,
                "bias_percentage": 0
            }
