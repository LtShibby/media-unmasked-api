import unittest
from mediaunmasked.analyzers.bias_analyzer import BiasAnalyzer
import logging

class TestBiasAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = BiasAnalyzer()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def test_left_bias(self):
        """Test detection of left-leaning bias"""
        text = "Progressive policies have shown success in addressing income inequality and social justice issues. The government's intervention has helped protect workers' rights."
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertIn('bias', result)
        self.assertLess(result['bias_score'], 0)  # Negative score indicates left bias
        self.logger.info(f"Left bias result: {result}")

    def test_right_bias(self):
        """Test detection of right-leaning bias"""
        text = "Free market solutions and deregulation have driven economic growth. Individual responsibility and traditional values remain crucial for society."
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertIn('bias', result)
        self.assertGreater(result['bias_score'], 0)  # Positive score indicates right bias
        self.logger.info(f"Right bias result: {result}")

    def test_neutral_content(self):
        """Test detection of neutral content"""
        text = "The study examined various economic policies and their outcomes. Researchers analyzed data from multiple sources to draw conclusions."
        
        result = self.analyzer.analyze(text)
        
        self.assertIsNotNone(result)
        self.assertIn('bias', result)
        self.assertAlmostEqual(result['bias_score'], 0, delta=0.2)  # Should be close to neutral
        self.logger.info(f"Neutral content result: {result}") 