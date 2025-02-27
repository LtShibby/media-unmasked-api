import logging
from typing import Dict, Any, List
from transformers import pipeline, AutoTokenizer
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)

class HeadlineAnalyzer:
    def __init__(self, use_ai: bool = True):
        """
        Initialize the analyzers for headline analysis.
        
        Args:
            use_ai: Boolean indicating whether to use AI-powered analysis (True) or traditional analysis (False)
        """
        self.use_ai = use_ai
        self.llm_available = False
        
        if use_ai:
            try:
                # NLI model for contradiction/entailment
                self.nli_pipeline = pipeline("text-classification", model="roberta-large-mnli")
                
                # Zero-shot classifier for clickbait and sensationalism
                self.zero_shot = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1
                )
                
                self.tokenizer = AutoTokenizer.from_pretrained("roberta-large-mnli")
                self.max_length = 512
                self.llm_available = True
                logger.info("LLM pipelines initialized successfully for headline analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM pipelines: {str(e)}")
                self.llm_available = False
        else:
            logger.info("Initializing headline analyzer in traditional mode")

    def _split_content(self, headline: str, content: str) -> List[str]:
        """Split content into sections that fit within token limit."""
        content_words = content.split()
        sections = []
        current_section = []
        
        # Account for headline and [SEP] token in the max length
        headline_tokens = len(self.tokenizer.encode(headline))
        sep_tokens = len(self.tokenizer.encode("[SEP]")) - 2
        max_content_tokens = self.max_length - headline_tokens - sep_tokens
        
        # Process words into sections
        for word in content_words:
            current_section.append(word)
            
            # Check if current section is approaching token limit
            current_text = " ".join(current_section)
            if len(self.tokenizer.encode(current_text)) >= max_content_tokens:
                current_section.pop()
                sections.append(" ".join(current_section))
                
                # Start new section with 20% overlap for context
                overlap_start = max(0, len(current_section) - int(len(current_section) * 0.2))
                current_section = current_section[overlap_start:]
                current_section.append(word)
        
        # Add any remaining content
        if current_section:
            sections.append(" ".join(current_section))
        
        return sections

    def _analyze_section(self, headline: str, section: str) -> Dict[str, Any]:
        """Analyze a single section for headline accuracy and sensationalism."""
        try:
            # Download NLTK data if needed
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            
            sentences = sent_tokenize(section)
            
            # Analyze headline against content for contradiction/entailment
            nli_scores = []
            flagged_phrases = []
            
            # Categories for sensationalism check
            sensationalism_categories = [
                "clickbait",
                "sensationalized",
                "misleading",
                "factual reporting",
                "accurate headline"
            ]
            
            # Check headline for sensationalism
            sensationalism_result = self.zero_shot(
                headline,
                sensationalism_categories,
                multi_label=True
            )
            
            sensationalism_scores = {
                label: score 
                for label, score in zip(sensationalism_result['labels'], sensationalism_result['scores'])
            }
            
            # Analyze each sentence for contradiction/support
            for sentence in sentences:
                if len(sentence.strip()) > 10:
                    # Check for contradiction/entailment
                    input_text = f"{headline} [SEP] {sentence}"
                    nli_result = self.nli_pipeline(input_text, top_k=None)
                    scores = {item['label']: item['score'] for item in nli_result}
                    nli_scores.append(scores)
                    
                    # Flag contradictory or highly sensationalized content
                    if scores.get('CONTRADICTION', 0) > 0.4:
                        flagged_phrases.append({
                            'text': sentence.strip(),
                            'type': 'contradiction',
                            'score': scores['CONTRADICTION']
                        })
            
            # Calculate aggregate scores
            avg_scores = {
                label: np.mean([score[label] for score in nli_scores]) 
                for label in ['ENTAILMENT', 'CONTRADICTION', 'NEUTRAL']
            }
            
            # Calculate headline accuracy score
            accuracy_components = {
                'entailment': avg_scores['ENTAILMENT'] * 0.4,
                'non_contradiction': (1 - avg_scores['CONTRADICTION']) * 0.3,
                'non_sensational': (
                    sensationalism_scores.get('factual reporting', 0) +
                    sensationalism_scores.get('accurate headline', 0)
                ) * 0.15,
                'non_clickbait': (
                    1 - sensationalism_scores.get('clickbait', 0) -
                    sensationalism_scores.get('sensationalized', 0)
                ) * 0.15
            }
            
            accuracy_score = sum(accuracy_components.values()) * 100
            
            # Sort and limit flagged phrases
            sorted_phrases = sorted(
                flagged_phrases,
                key=lambda x: x['score'],
                reverse=True
            )
            top_phrases = [phrase['text'] for phrase in sorted_phrases[:5]]
            
            return {
                "accuracy_score": accuracy_score,
                "flagged_phrases": top_phrases,
                "detailed_scores": {
                    "nli": avg_scores,
                    "sensationalism": sensationalism_scores
                }
            }
            
        except Exception as e:
            logger.error(f"Section analysis failed: {str(e)}")
            return {
                "accuracy_score": 0,
                "flagged_phrases": [],
                "detailed_scores": {}
            }

    def _analyze_traditional(self, headline: str, content: str) -> Dict[str, Any]:
        """Traditional headline analysis method."""
        try:
            # Download NLTK data if needed
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')

            # Basic metrics
            headline_words = set(headline.lower().split())
            content_words = set(content.lower().split())
            
            # Calculate word overlap
            overlap_words = headline_words.intersection(content_words)
            overlap_score = len(overlap_words) / len(headline_words) if headline_words else 0
            
            # Check for clickbait patterns
            clickbait_patterns = [
                "you won't believe",
                "shocking",
                "mind blowing",
                "amazing",
                "incredible",
                "unbelievable",
                "must see",
                "click here",
                "find out",
                "what happens next"
            ]
            
            clickbait_count = sum(1 for pattern in clickbait_patterns if pattern in headline.lower())
            clickbait_penalty = clickbait_count * 10  # 10% penalty per clickbait phrase
            
            # Calculate final score (0-100)
            base_score = overlap_score * 100
            final_score = max(0, min(100, base_score - clickbait_penalty))
            
            # Find potentially misleading phrases
            flagged_phrases = []
            sentences = sent_tokenize(content)
            
            for sentence in sentences:
                # Flag sentences that directly contradict headline words
                sentence_words = set(sentence.lower().split())
                if len(headline_words.intersection(sentence_words)) > 2:
                    flagged_phrases.append(sentence.strip())
                
                # Flag sentences with clickbait patterns
                if any(pattern in sentence.lower() for pattern in clickbait_patterns):
                    flagged_phrases.append(sentence.strip())
            
            return {
                "headline_vs_content_score": round(final_score, 1),
                "flagged_phrases": list(set(flagged_phrases))[:5]  # Limit to top 5 unique phrases
            }
            
        except Exception as e:
            logger.error(f"Traditional analysis failed: {str(e)}")
            return {
                "headline_vs_content_score": 0,
                "flagged_phrases": []
            }

    def analyze(self, headline: str, content: str) -> Dict[str, Any]:
        """Analyze how well the headline matches the content."""
        try:
            logger.info("\n" + "="*50)
            logger.info("HEADLINE ANALYSIS STARTED")
            logger.info("="*50)
            
            if not headline.strip() or not content.strip():
                logger.warning("Empty headline or content provided")
                return {
                    "headline_vs_content_score": 0,
                    "flagged_phrases": []
                }

            # Use LLM analysis if available and enabled
            if self.use_ai and self.llm_available:
                logger.info("Using LLM analysis for headline")
                # Split content if needed
                sections = self._split_content(headline, content)
                section_results = []
                
                # Analyze each section
                for section in sections:
                    result = self._analyze_section(headline, section)
                    section_results.append(result)
                
                # Aggregate results across sections
                accuracy_scores = [r['accuracy_score'] for r in section_results]
                final_score = np.mean(accuracy_scores)
                
                # Combine flagged phrases from all sections
                all_phrases = []
                for result in section_results:
                    all_phrases.extend(result['flagged_phrases'])
                
                # Remove duplicates and limit to top 5
                unique_phrases = list(dict.fromkeys(all_phrases))[:5]
                
                return {
                    "headline_vs_content_score": round(final_score, 1),
                    "flagged_phrases": unique_phrases
                }
            else:
                # Use traditional analysis
                logger.info("Using traditional headline analysis")
                return self._analyze_traditional(headline, content)
            
        except Exception as e:
            logger.error(f"Headline analysis failed: {str(e)}")
            return {
                "headline_vs_content_score": 0,
                "flagged_phrases": []
            } 