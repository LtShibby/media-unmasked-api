import logging
from typing import Dict, Any, List
from transformers import pipeline
from transformers import AutoTokenizer
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)

class HeadlineAnalyzer:
    def __init__(self):
        """Initialize the NLI model for contradiction detection."""
        self.nli_pipeline = pipeline("text-classification", model="roberta-large-mnli")
        self.tokenizer = AutoTokenizer.from_pretrained("roberta-large-mnli")
        self.max_length = 512
        
    def _split_content(self, headline: str, content: str) -> List[str]:
        """Split content into sections that fit within token limit."""
        content_words = content.split()
        sections = []
        current_section = []
        
        # Account for headline and [SEP] token in the max length
        headline_tokens = len(self.tokenizer.encode(headline))
        sep_tokens = len(self.tokenizer.encode("[SEP]")) - 2  # -2 because encode adds special tokens
        max_content_tokens = self.max_length - headline_tokens - sep_tokens
        
        # Process words into sections
        for word in content_words:
            current_section.append(word)
            
            # Check if current section is approaching token limit
            current_text = " ".join(current_section)
            if len(self.tokenizer.encode(current_text)) >= max_content_tokens:
                # Remove last word (it might make us go over limit)
                current_section.pop()
                sections.append(" ".join(current_section))
                
                # Start new section with 20% overlap for context
                overlap_start = max(0, len(current_section) - int(len(current_section) * 0.2))
                current_section = current_section[overlap_start:]
                current_section.append(word)
        
        # Add any remaining content as the last section
        if current_section:
            sections.append(" ".join(current_section))
        
        logger.info(f"""Content Splitting:
            - Original content length: {len(content_words)} words
            - Split into {len(sections)} sections
            - Headline uses {headline_tokens} tokens
            - Available tokens per section: {max_content_tokens}
        """)
        return sections

    def _analyze_section(self, headline: str, section: str) -> Dict[str, float]:
        """Analyze a single section of content."""
        # Use a more robust method for sentence splitting
        nltk.download('punkt')
        sentences = sent_tokenize(section)

        flagged_phrases = []
        for sentence in sentences:
            input_text = f"{headline} [SEP] {sentence}"
            result = self.nli_pipeline(input_text, top_k=None)
            scores = {item['label']: item['score'] for item in result}
            
            # Log the model output for debugging
            logger.info(f"Sentence: {sentence}")
            logger.info(f"Scores: {scores}")
            
            # Set the threshold for contradiction to anything higher than 0.1
            if scores.get('CONTRADICTION', 0) > 0.1:  # Threshold set to > 0.1
                flagged_phrases.append(sentence)
                
        # Adjust the headline_vs_content_score based on contradictions
        contradiction_penalty = len(flagged_phrases) * 0.1  # Example penalty per contradiction
        adjusted_score = max(0, scores.get('ENTAILMENT', 0) - contradiction_penalty)

        logger.info("\nSection Analysis:")
        logger.info("-"*30)
        logger.info(f"Section preview: {section[:100]}...")
        for label, score in scores.items():
            logger.info(f"Label: {label:<12} Score: {score:.3f}")
            
        return {"scores": scores, "flagged_phrases": flagged_phrases, "adjusted_score": adjusted_score}

    def analyze(self, headline: str, content: str) -> Dict[str, Any]:
        """Analyze how well the headline matches the content using an AI model."""
        try:
            logger.info("\n" + "="*50)
            logger.info("HEADLINE ANALYSIS STARTED")
            logger.info("="*50)
            
            # Handle empty inputs
            if not headline.strip() or not content.strip():
                logger.warning("Empty headline or content provided")
                return {
                    "headline_vs_content_score": 0,
                    "entailment_score": 0,
                    "contradiction_score": 0,
                    "contradictory_phrases": []
                }

            # Split content if too long
            content_tokens = len(self.tokenizer.encode(content))
            if content_tokens > self.max_length:
                logger.warning(f"""
                    Content Length Warning:
                    - Total tokens: {content_tokens}
                    - Max allowed: {self.max_length}
                    - Splitting into sections...
                """)
                sections = self._split_content(headline, content)
                
                # Analyze each section
                section_scores = []
                for i, section in enumerate(sections, 1):
                    logger.info(f"\nAnalyzing section {i}/{len(sections)}")
                    scores = self._analyze_section(headline, section)
                    section_scores.append(scores)
                
                # Aggregate scores across sections
                # Use max contradiction (if any section strongly contradicts, that's important)
                # Use mean entailment (overall support across sections)
                # Use mean neutral (general neutral tone across sections)
                entailment_score = np.mean([s.get('ENTAILMENT', 0) for s in section_scores])
                contradiction_score = np.max([s.get('CONTRADICTION', 0) for s in section_scores])
                neutral_score = np.mean([s.get('NEUTRAL', 0) for s in section_scores])
                
                logger.info("\nAggregated Scores Across Sections:")
                logger.info("-"*30)
                logger.info(f"Mean Entailment: {entailment_score:.3f}")
                logger.info(f"Max Contradiction: {contradiction_score:.3f}")
                logger.info(f"Mean Neutral: {neutral_score:.3f}")
            else:
                # Single section analysis
                scores = self._analyze_section(headline, content)
                entailment_score = scores.get('ENTAILMENT', 0)
                contradiction_score = scores.get('CONTRADICTION', 0)
                neutral_score = scores.get('NEUTRAL', 0)
            
            # Compute final consistency score
            final_score = (
                (entailment_score * 0.6) +      # Base score from entailment
                (neutral_score * 0.3) +         # Neutral is acceptable
                ((1 - contradiction_score) * 0.1)  # Small penalty for contradiction
            ) * 100
            
            # Log final results
            logger.info("\nFinal Analysis Results:")
            logger.info("-"*30)
            logger.info(f"Headline: {headline}")
            logger.info(f"Content Length: {content_tokens} tokens")
            logger.info("\nFinal Scores:")
            logger.info(f"{'Entailment:':<15} {entailment_score:.3f}")
            logger.info(f"{'Neutral:':<15} {neutral_score:.3f}")
            logger.info(f"{'Contradiction:':<15} {contradiction_score:.3f}")
            logger.info(f"\nFinal Score: {final_score:.1f}%")
            logger.info("="*50 + "\n")
            
            return {
                "headline_vs_content_score": round(final_score, 1),
                "entailment_score": round(entailment_score, 2),
                "contradiction_score": round(contradiction_score, 2),
                "contradictory_phrases": scores.get('flagged_phrases', [])
            }
            
        except Exception as e:
            logger.error("\nHEADLINE ANALYSIS ERROR")
            logger.error("-"*30)
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            logger.error("Stack Trace:", exc_info=True)
            logger.error("="*50 + "\n")
            return {
                "headline_vs_content_score": 0,
                "entailment_score": 0,
                "contradiction_score": 0,
                "contradictory_phrases": []
            } 