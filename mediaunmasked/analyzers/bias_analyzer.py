import logging
import os
from typing import Dict, Any, List
from transformers import pipeline
import numpy as np

logger = logging.getLogger(__name__)

class BiasAnalyzer:
    def __init__(self, use_ai: bool = True):
        """
        Initialize bias analyzer with both LLM and traditional approaches.
        
        Args:
            use_ai: Boolean indicating whether to use AI-powered analysis (True) or traditional analysis (False)
        """
        self.use_ai = use_ai
        self.llm_available = False
        
        # Load traditional keywords
        self.resources_dir = os.path.join(os.path.dirname(__file__), '..', 'resources')
        self.left_keywords = self._load_keywords('left_bias_words.txt')
        self.right_keywords = self._load_keywords('right_bias_words.txt')
        
        if use_ai:
            try:
                # Initialize LLM pipeline for zero-shot classification
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1  # Use CPU, change to specific GPU index if available
                )
                self.llm_available = True
                logger.info("LLM pipeline initialized successfully for bias analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM pipeline: {str(e)}")
                self.llm_available = False
        else:
            logger.info("Initializing bias analyzer in traditional mode")

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze bias using LLM with fallback to traditional method.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dict containing bias analysis results
        """
        try:
            # Try LLM analysis if enabled and available
            if self.use_ai and self.llm_available:
                llm_result = self._analyze_with_llm(text)
                if llm_result:
                    return llm_result
            
            # Use traditional analysis
            logger.info("Using traditional bias analysis")
            return self._analyze_traditional(text)
            
        except Exception as e:
            logger.error(f"Error in bias analysis: {str(e)}")
            return {
                "bias": "Error",
                "bias_score": 0.0,
                "bias_percentage": 0,
                "flagged_phrases": []
            }

    def _load_keywords(self, filename: str) -> List[str]:
        """Load keywords from file."""
        try:
            filepath = os.path.join(self.resources_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            logger.error(f"Error loading {filename}: {str(e)}")
            return []

    def _analyze_traditional(self, text: str) -> Dict[str, Any]:
        """Traditional keyword-based bias analysis."""
        text_lower = text.lower()
        
        # Count matches and collect flagged phrases
        left_matches = [word for word in self.left_keywords if word in text_lower]
        right_matches = [word for word in self.right_keywords if word in text_lower]
        
        left_count = len(left_matches)
        right_count = len(right_matches)
        total_count = left_count + right_count
        
        if total_count == 0:
            return {
                "bias": "Neutral",
                "bias_score": 0.0,
                "bias_percentage": 0,
                "flagged_phrases": []
            }
        
        # Calculate bias score (-1 to 1)
        bias_score = (right_count - left_count) / total_count
        
        # Calculate bias percentage
        bias_percentage = abs(bias_score * 100)
        
        # Determine bias label
        if bias_score < -0.6:
            bias = "Strongly Left"
        elif bias_score < -0.3:
            bias = "Moderately Left"
        elif bias_score < -0.1:
            bias = "Leaning Left"
        elif bias_score > 0.6:
            bias = "Strongly Right"
        elif bias_score > 0.3:
            bias = "Moderately Right"
        elif bias_score > 0.1:
            bias = "Leaning Right"
        else:
            bias = "Neutral"
        
        return {
            "bias": bias,
            "bias_score": round(bias_score, 2),
            "bias_percentage": round(bias_percentage, 1),
            "flagged_phrases": list(set(left_matches + right_matches))[:5]  # Limit to top 5 unique phrases
        }

    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """Analyze bias using LLM zero-shot classification."""
        try:
            # Define bias categories to check against
            bias_categories = [
                "left-wing bias",
                "right-wing bias",
                "neutral/balanced perspective"
            ]
            
            # Split text into manageable chunks (2000 chars each)
            chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
            
            # Analyze each chunk
            chunk_scores = []
            flagged_phrases = []
            
            for chunk in chunks:
                # Perform zero-shot classification
                result = self.classifier(
                    chunk,
                    bias_categories,
                    multi_label=True
                )
                
                chunk_scores.append({
                    label: score 
                    for label, score in zip(result['labels'], result['scores'])
                })
                
                # Identify strongly biased phrases
                sentences = chunk.split('.')
                for sentence in sentences:
                    if len(sentence.strip()) > 10:  # Ignore very short sentences
                        sentence_result = self.classifier(
                            sentence.strip(),
                            bias_categories,
                            multi_label=False
                        )
                        max_score = max(sentence_result['scores'])
                        if max_score > 0.8 and sentence_result['labels'][0] != "neutral/balanced perspective":
                            flagged_phrases.append(sentence.strip())

            # Aggregate scores across chunks
            aggregated_scores = {
                category: np.mean([
                    scores[category] 
                    for scores in chunk_scores
                ]) 
                for category in bias_categories
            }

            # Calculate bias metrics
            left_score = aggregated_scores["left-wing bias"]
            right_score = aggregated_scores["right-wing bias"]
            neutral_score = aggregated_scores["neutral/balanced perspective"]
            
            # Calculate bias score (-1 to 1, where negative is left and positive is right)
            bias_score = (right_score - left_score) / max(right_score + left_score, 0.0001)
            
            # Determine bias label
            if bias_score < -0.6:
                bias = "Strongly Left"
            elif bias_score < -0.3:
                bias = "Moderately Left"
            elif bias_score < -0.1:
                bias = "Leaning Left"
            elif bias_score > 0.6:
                bias = "Strongly Right"
            elif bias_score > 0.3:
                bias = "Moderately Right"
            elif bias_score > 0.1:
                bias = "Leaning Right"
            else:
                bias = "Neutral"
            
            # Calculate bias percentage (0-100)
            bias_percentage = min(100, abs(bias_score * 100))
            
            return {
                "bias": bias,
                "bias_score": round(bias_score, 2),
                "bias_percentage": round(bias_percentage, 1),
                "flagged_phrases": list(set(flagged_phrases))[:5],  # Limit to top 5 unique phrases
                "detailed_scores": {
                    "left_bias": round(left_score * 100, 1),
                    "right_bias": round(right_score * 100, 1),
                    "neutral": round(neutral_score * 100, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return None
