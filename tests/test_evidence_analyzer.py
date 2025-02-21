import unittest
from mediaunmasked.analyzers.evidence_analyzer import EvidenceAnalyzer
import logging

class TestEvidenceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = EvidenceAnalyzer()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def test_well_supported_content(self):
        """Test content with strong evidence"""
        text = """According to the WHO study, vaccination rates have increased by 25%. 
        Research published in Nature shows significant results. The data from multiple 
        studies indicates a clear trend, as reported in the scientific journal."""
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['evidence_based_score'], 70)
        self.logger.info(f"Well-supported content score: {result}")

    def test_poorly_supported_content(self):
        """Test content with weak evidence"""
        text = """Some people say this treatment works wonders. Many believe it's the 
        best solution available. Sources claim it could be revolutionary."""
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertLess(result['evidence_based_score'], 50)
        self.logger.info(f"Poorly-supported content score: {result}")

    def test_mixed_evidence_content(self):
        """Test content with mixed evidence quality"""
        text = """According to recent studies, the treatment shows promise. Some experts 
        claim it could be effective, while research published in medical journals 
        indicates more testing is needed."""
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['evidence_based_score'], 30)
        self.assertLess(result['evidence_based_score'], 80)
        self.logger.info(f"Mixed evidence content score: {result}") 