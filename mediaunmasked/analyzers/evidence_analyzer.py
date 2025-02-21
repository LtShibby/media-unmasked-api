import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EvidenceAnalyzer:
    def __init__(self):
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

    def analyze(self, text: str) -> Dict[str, Any]:
        """Check for evidence-based reporting."""
        try:
            text_lower = text.lower()
            
            citation_count = sum(1 for marker in self.citation_markers if marker in text_lower)
            vague_count = sum(1 for marker in self.vague_markers if marker in text_lower)
            
            base_score = min(citation_count * 20, 100)
            penalty = vague_count * 10
            
            evidence_score = max(0, base_score - penalty)
            
            return {
                "evidence_based_score": evidence_score
            }
            
        except Exception as e:
            logger.error(f"Error in evidence analysis: {str(e)}")
            return {
                "evidence_based_score": 0
            } 