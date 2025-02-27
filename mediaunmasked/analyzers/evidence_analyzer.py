import logging
from typing import Dict, Any, List
from transformers import pipeline
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)

class EvidenceAnalyzer:
    def __init__(self, use_ai: bool = True):
        """
        Initialize evidence analyzer with LLM and traditional approaches.
        
        Args:
            use_ai: Boolean indicating whether to use AI-powered analysis (True) or traditional analysis (False)
        """
        self.use_ai = use_ai
        self.llm_available = False
        
        if use_ai:
            try:
                # Zero-shot classifier for evidence analysis
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1
                )
                self.llm_available = True
                logger.info("LLM pipeline initialized successfully for evidence analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM pipeline: {str(e)}")
                self.llm_available = False
        else:
            logger.info("Initializing evidence analyzer in traditional mode")
        
        # Traditional markers for fallback
        self.citation_markers = [
            "according to",
            "said",
            "reported",
            "stated",
            "shows",
            "found",
            "study",
            "research",
            "data",
            "evidence"
        ]
        
        self.vague_markers = [
            "some say",
            "many believe",
            "people think",
            "experts claim",
            "sources say",
            "it is believed",
            "reportedly",
            "allegedly"
        ]

    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """Analyze evidence using LLM."""
        try:
            # Clean the text of formatting markers
            cleaned_text = text.replace('$!/$', '').replace('##', '').replace('#', '')
            cleaned_text = '\n'.join(line for line in cleaned_text.split('\n') 
                                   if not line.startswith('[') and not line.startswith('More on'))
            
            # Download NLTK data if needed
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            
            # Split text into chunks
            chunks = [cleaned_text[i:i+2000] for i in range(0, len(cleaned_text), 2000)]
            
            # Categories for evidence classification
            evidence_categories = [
                "factual statement with source",
                "verifiable claim",
                "expert opinion",
                "data-backed claim",
                "unsubstantiated claim",
                "opinion statement"
            ]
            
            chunk_scores = []
            flagged_phrases = []
            
            for chunk in chunks:
                # Analyze each sentence in the chunk
                sentences = sent_tokenize(chunk)
                
                for sentence in sentences:
                    if len(sentence.strip()) > 10:
                        # Classify the type of evidence
                        result = self.classifier(
                            sentence.strip(),
                            evidence_categories,
                            multi_label=True
                        )
                        
                        # Calculate evidence score for the sentence
                        evidence_scores = {
                            label: score 
                            for label, score in zip(result['labels'], result['scores'])
                        }
                        
                        # Strong evidence indicators
                        strong_evidence = sum([
                            evidence_scores.get("factual statement with source", 0),
                            evidence_scores.get("data-backed claim", 0),
                            evidence_scores.get("expert opinion", 0)
                        ]) / 3  # Average the strong evidence scores
                        
                        # Weak or no evidence indicators
                        weak_evidence = sum([
                            evidence_scores.get("unsubstantiated claim", 0),
                            evidence_scores.get("opinion statement", 0)
                        ]) / 2  # Average the weak evidence scores
                        
                        # Store scores for overall calculation
                        chunk_scores.append({
                            'strong_evidence': strong_evidence,
                            'weak_evidence': weak_evidence
                        })
                        
                        # Flag high-quality evidence
                        if strong_evidence > 0.7 and not any(
                            marker in sentence.lower() 
                            for marker in ['more on this story', 'click here', 'read more']
                        ):
                            flagged_phrases.append({
                                'text': sentence.strip(),
                                'type': 'strong_evidence',
                                'score': strong_evidence
                            })
            
            # Calculate overall evidence score
            if chunk_scores:
                avg_strong = np.mean([s['strong_evidence'] for s in chunk_scores])
                avg_weak = np.mean([s['weak_evidence'] for s in chunk_scores])
                
                # Evidence score formula:
                # - Reward strong evidence (70% weight)
                # - Penalize weak/unsubstantiated claims (30% weight)
                # - Ensure score is between 0 and 100
                evidence_score = min(100, (
                    (avg_strong * 0.7) + 
                    ((1 - avg_weak) * 0.3)
                ) * 100)
            else:
                evidence_score = 0
            
            # Sort and select top evidence phrases
            sorted_phrases = sorted(
                flagged_phrases,
                key=lambda x: x['score'],
                reverse=True
            )
            # Filter out formatting text and duplicates
            unique_phrases = []
            seen = set()
            for phrase in sorted_phrases:
                clean_text = phrase['text'].strip()
                if clean_text not in seen and not any(
                    marker in clean_text.lower() 
                    for marker in ['more on this story', 'click here', 'read more']
                ):
                    unique_phrases.append(clean_text)
                    seen.add(clean_text)
                if len(unique_phrases) >= 5:
                    break
            
            return {
                "evidence_based_score": round(evidence_score, 1),
                "flagged_phrases": unique_phrases
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return None

    def _analyze_traditional(self, text: str) -> Dict[str, Any]:
        """Traditional evidence analysis as fallback."""
        try:
            text_lower = text.lower()
            
            # Find citations and evidence
            evidence_phrases = []
            for marker in self.citation_markers:
                index = text_lower.find(marker)
                while index != -1:
                    # Get the sentence containing the marker
                    start = max(0, text_lower.rfind('.', 0, index) + 1)
                    end = text_lower.find('.', index)
                    if end == -1:
                        end = len(text_lower)
                    
                    evidence_phrases.append(text[start:end].strip())
                    index = text_lower.find(marker, end)
            
            # Count vague references
            vague_count = sum(1 for marker in self.vague_markers if marker in text_lower)
            
            # Calculate score
            citation_count = len(evidence_phrases)
            base_score = min(citation_count * 20, 100)
            penalty = vague_count * 10
            
            evidence_score = max(0, base_score - penalty)
            
            return {
                "evidence_based_score": evidence_score,
                "flagged_phrases": list(set(evidence_phrases))[:5]  # Limit to top 5 unique phrases
            }
            
        except Exception as e:
            logger.error(f"Traditional analysis failed: {str(e)}")
            return {
                "evidence_based_score": 0,
                "flagged_phrases": []
            }

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze evidence using LLM with fallback to traditional method."""
        try:
            # Try LLM analysis if enabled and available
            if self.use_ai and self.llm_available:
                llm_result = self._analyze_with_llm(text)
                if llm_result:
                    return llm_result
            
            # Use traditional analysis
            logger.info("Using traditional evidence analysis")
            return self._analyze_traditional(text)
            
        except Exception as e:
            logger.error(f"Error in evidence analysis: {str(e)}")
            return {
                "evidence_based_score": 0,
                "flagged_phrases": []
            } 