import unittest
from mediaunmasked.analyzers.scoring import MediaScorer
import logging

class TestMediaScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = MediaScorer()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def test_high_quality_article(self):
        """Test scoring of high-quality article"""
        headline = "New Study Shows Link Between Exercise and Mental Health"
        content = """According to research published in the Journal of Medicine, regular 
        exercise significantly improves mental health outcomes. The study, conducted over 
        two years with 1000 participants, found a 30% reduction in anxiety symptoms among 
        those who exercised regularly. Dr. Smith, lead researcher, stated that the findings 
        demonstrate a clear correlation between physical activity and mental wellbeing."""
        
        result = self.scorer.calculate_media_score(headline, content)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['media_unmasked_score'], 80)
        self.assertEqual(result['rating'], 'Trustworthy')
        self.logger.info(f"High quality article score: {result}")

    def test_biased_article(self):
        """Test scoring of biased article"""
        headline = "Government Policies Destroying Our Way of Life"
        content = """Experts say the radical new policies are ruining everything! 
        Sources claim this is the worst decision ever made. Many believe this will 
        lead to disaster. The socialist agenda is clearly destroying our values."""
        
        result = self.scorer.calculate_media_score(headline, content)
        
        self.assertIsNotNone(result)
        self.assertLess(result['media_unmasked_score'], 60)
        self.assertEqual(result['rating'], 'Bias Present')
        self.logger.info(f"Biased article score: {result}")

    def test_misleading_article(self):
        """Test scoring of misleading article"""
        headline = "Miracle Cure Found for All Diseases!"
        content = """Some people say this amazing discovery cures everything! 
        You won't believe the shocking results. Everyone knows this is the 
        breakthrough we've been waiting for!"""
        
        result = self.scorer.calculate_media_score(headline, content)
        
        self.assertIsNotNone(result)
        self.assertLess(result['media_unmasked_score'], 50)
        self.assertEqual(result['rating'], 'Misleading')
        self.logger.info(f"Misleading article score: {result}") 