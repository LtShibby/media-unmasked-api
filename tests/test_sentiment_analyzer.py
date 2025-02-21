import unittest
from mediaunmasked.analyzers.sentiment_analyzer import SentimentAnalyzer
import logging

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def test_positive_sentiment(self):
        """Test detection of positive sentiment"""
        text = "The breakthrough research shows promising results in cancer treatment, bringing hope to millions of patients worldwide."
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['sentiment'], 'Positive')
        self.logger.info(f"Positive sentiment result: {result}")

    def test_negative_sentiment(self):
        """Test detection of negative sentiment"""
        text = "The devastating impact of the disaster has left thousands homeless and caused widespread damage to infrastructure."
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['sentiment'], 'Negative')
        self.logger.info(f"Negative sentiment result: {result}")

    def test_manipulative_content(self):
        """Test detection of manipulative language"""
        text = "Experts say this shocking new discovery will change everything! Sources claim it's the biggest breakthrough ever, and everyone knows it's true!"
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['manipulation_score'], 20)
        self.assertGreater(len(result['flagged_phrases']), 0)
        self.logger.info(f"Manipulative content result: {result}") 