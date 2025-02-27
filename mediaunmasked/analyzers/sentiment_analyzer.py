import logging
from typing import Dict, Any, List
from textblob import TextBlob
from transformers import pipeline
import numpy as np

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, use_ai: bool = True):
        """
        Initialize sentiment analyzer with both traditional and LLM-based approaches.
        
        Args:
            use_ai: Boolean indicating whether to use AI-powered analysis (True) or traditional analysis (False)
        """
        self.use_ai = use_ai
        self.llm_available = False
        
        # Traditional manipulation patterns
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
        
        if use_ai:
            try:
                # Initialize LLM pipelines
                self.sentiment_pipeline = pipeline(
                    "text-classification",
                    model="SamLowe/roberta-base-go_emotions",
                    top_k=None
                )
                self.toxicity_pipeline = pipeline(
                    "text-classification",
                    model="martin-ha/toxic-comment-model",
                    top_k=None
                )
                self.manipulation_pipeline = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1
                )
                self.llm_available = True
                logger.info("LLM pipelines initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM pipelines: {str(e)}")
                self.llm_available = False
        else:
            logger.info("Initializing sentiment analyzer in traditional mode")

    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """Perform sentiment analysis using LLM models."""
        try:
            logger.info("Starting LLM sentiment analysis")
            
            # Clean the text of formatting markers
            cleaned_text = text.replace('$!/$', '').replace('##', '').replace('#', '')
            cleaned_text = '\n'.join(line for line in cleaned_text.split('\n') 
                                   if not line.startswith('[') and not line.startswith('More on'))
            
            logger.info("Text cleaned and prepared for analysis")
            
            # Split text into chunks of 512 tokens (approximate)
            chunks = [cleaned_text[i:i+2000] for i in range(0, len(cleaned_text), 2000)]
            logger.info(f"Text split into {len(chunks)} chunks for processing")
            
            # Initialize aggregation variables
            sentiment_scores = []
            toxicity_scores = []
            manipulation_scores = []
            flagged_phrases = []
            
            manipulation_categories = [
                "emotional manipulation",
                "fear mongering",
                "propaganda",
                "factual reporting",
                "balanced perspective"
            ]
            
            # Process each chunk
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"Processing chunk {i}/{len(chunks)}")
                
                try:
                    # Get emotion scores with detailed logging
                    logger.debug(f"Analyzing emotions for chunk {i}")
                    emotions = self.sentiment_pipeline(chunk)
                    logger.debug(f"Raw emotion response: {emotions}")
                    
                    # Handle different response formats
                    if isinstance(emotions, list):
                        # Multiple results format
                        for emotion in emotions:
                            if isinstance(emotion, dict) and 'label' in emotion and 'score' in emotion:
                                sentiment_scores.append(emotion)
                    elif isinstance(emotions, dict) and 'label' in emotions and 'score' in emotions:
                        # Single result format
                        sentiment_scores.append(emotions)
                    logger.debug(f"Processed emotion scores: {sentiment_scores}")
                    
                    # Get toxicity scores
                    logger.debug(f"Analyzing toxicity for chunk {i}")
                    toxicity = self.toxicity_pipeline(chunk)
                    if isinstance(toxicity, list):
                        toxicity_scores.extend(toxicity)
                    else:
                        toxicity_scores.append(toxicity)
                    logger.debug(f"Processed toxicity scores: {toxicity_scores}")
                    
                    # Get manipulation scores
                    logger.debug(f"Analyzing manipulation for chunk {i}")
                    manipulation = self.manipulation_pipeline(
                        chunk,
                        manipulation_categories,
                        multi_label=True
                    )
                    
                    if isinstance(manipulation, dict) and 'labels' in manipulation and 'scores' in manipulation:
                        manipulation_scores.append({
                            label: score 
                            for label, score in zip(manipulation['labels'], manipulation['scores'])
                        })
                    logger.debug(f"Processed manipulation scores: {manipulation_scores}")
                    
                    # Analyze sentences for manipulation
                    sentences = chunk.split('.')
                    for sentence in sentences:
                        if len(sentence.strip()) > 10:
                            sent_result = self.manipulation_pipeline(
                                sentence.strip(),
                                manipulation_categories,
                                multi_label=False
                            )
                            if (sent_result['labels'][0] in ["emotional manipulation", "fear mongering", "propaganda"] 
                                and sent_result['scores'][0] > 0.7):
                                flagged_phrases.append({
                                    'text': sentence.strip(),
                                    'type': sent_result['labels'][0],
                                    'score': sent_result['scores'][0]
                                })
                
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i}: {str(chunk_error)}")
                    continue
            
            logger.info("All chunks processed, aggregating scores")
            
            # Aggregate scores with error handling
            def aggregate_scores(scores_list, score_type: str):
                try:
                    all_scores = {}
                    for scores in scores_list:
                        if isinstance(scores, dict):
                            if 'label' in scores and 'score' in scores:
                                label = scores['label']
                                score = scores['score']
                            else:
                                # Handle direct label-score mapping
                                for label, score in scores.items():
                                    if label not in all_scores:
                                        all_scores[label] = []
                                    if isinstance(score, (int, float)):
                                        all_scores[label].append(score)
                                continue
                        else:
                            logger.warning(f"Unexpected score format in {score_type}: {scores}")
                            continue
                            
                        if isinstance(label, (str, bytes)):
                            if label not in all_scores:
                                all_scores[label] = []
                            if isinstance(score, (int, float)):
                                all_scores[label].append(score)
                                
                    return {k: np.mean(v) for k, v in all_scores.items() if v}
                except Exception as agg_error:
                    logger.error(f"Error aggregating {score_type} scores: {str(agg_error)}")
                    return {}
            
            emotion_scores = aggregate_scores(sentiment_scores, "emotion")
            toxicity_scores = aggregate_scores(toxicity_scores, "toxicity")
            logger.debug(f"Aggregated emotion scores: {emotion_scores}")
            logger.debug(f"Aggregated toxicity scores: {toxicity_scores}")
            
            # Aggregate manipulation scores
            manipulation_agg = {
                category: np.mean([
                    scores.get(category, 0) 
                    for scores in manipulation_scores
                ]) 
                for category in manipulation_categories
            }
            logger.debug(f"Aggregated manipulation scores: {manipulation_agg}")
            
            # Calculate manipulation score based on multiple factors
            manipulation_indicators = {
                'emotional manipulation': 0.4,
                'fear mongering': 0.3,
                'propaganda': 0.3,
                'toxic': 0.2,
                'severe_toxic': 0.3,
                'threat': 0.2
            }
            
            # Combine toxicity and manipulation scores
            combined_scores = {**toxicity_scores, **manipulation_agg}
            manipulation_score = min(100, sum(
                combined_scores.get(k, 0) * weight 
                for k, weight in manipulation_indicators.items()
            ) * 100)
            
            logger.info(f"Final manipulation score: {manipulation_score}")
            
            # Determine overall sentiment
            positive_emotions = ['admiration', 'joy', 'amusement', 'approval']
            negative_emotions = ['disgust', 'anger', 'disappointment', 'fear']
            neutral_emotions = ['neutral', 'confusion', 'realization']
            
            pos_score = sum(emotion_scores.get(emotion, 0) for emotion in positive_emotions)
            neg_score = sum(emotion_scores.get(emotion, 0) for emotion in negative_emotions)
            neu_score = sum(emotion_scores.get(emotion, 0) for emotion in neutral_emotions)
            
            logger.debug(f"Sentiment scores - Positive: {pos_score}, Negative: {neg_score}, Neutral: {neu_score}")
            
            # Determine sentiment based on highest score
            max_score = max(pos_score, neg_score, neu_score)
            if max_score == pos_score and pos_score > 0.3:
                sentiment = "Positive"
            elif max_score == neg_score and neg_score > 0.3:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
            
            logger.info(f"Final sentiment determination: {sentiment}")
            
            # Sort and limit flagged phrases by manipulation score
            sorted_phrases = sorted(flagged_phrases, key=lambda x: x['score'], reverse=True)
            unique_phrases = []
            seen = set()
            for phrase in sorted_phrases:
                clean_text = phrase['text'].strip()
                if clean_text not in seen:
                    unique_phrases.append(clean_text)
                    seen.add(clean_text)
                if len(unique_phrases) >= 5:
                    break
            
            logger.info("LLM analysis completed successfully")
            
            return {
                "sentiment": sentiment,
                "manipulation_score": manipulation_score,
                "flagged_phrases": unique_phrases,
                "detailed_scores": {
                    "emotions": emotion_scores,
                    "manipulation": manipulation_agg,
                    "toxicity": toxicity_scores
                }
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}", exc_info=True)
            return None

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using LLM with fallback to traditional methods.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dict containing sentiment analysis results
        """
        try:
            # Try LLM analysis if enabled and available
            if self.use_ai and self.llm_available:
                llm_result = self._analyze_with_llm(text)
                if llm_result:
                    return llm_result
            
            # Use traditional analysis
            logger.info("Using traditional sentiment analysis")
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
            
            return {
                "sentiment": sentiment,
                "manipulation_score": min(manipulation_score, 100),
                "flagged_phrases": manipulative_phrases[:5]  # Limit to top 5 phrases
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