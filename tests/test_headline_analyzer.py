import unittest
from mediaunmasked.analyzers.headline_analyzer import HeadlineAnalyzer
import logging

class TestHeadlineAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = HeadlineAnalyzer()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def test_matching_headline(self):
        """Test when headline matches content"""
        headline = "Climate Change Impact on Global Weather Patterns"
        content = "Scientists have discovered significant changes in global weather patterns due to climate change. The study shows increasing temperatures are affecting weather systems worldwide."
        
        result = self.analyzer.analyze(headline, content)
        
        self.assertIsNotNone(result)
        self.assertIn('headline_vs_content_score', result)
        self.assertGreater(result['headline_vs_content_score'], 70)  # Should have high score
        
        self.logger.info(f"Matching headline score: {result['headline_vs_content_score']}")

    def test_misleading_headline(self):
        """Test when headline is misleading compared to content"""
        headline = "Shocking New Diet Guarantees Weight Loss"
        content = "While some dietary changes may contribute to weight loss, there is no guaranteed method. Studies show sustainable weight loss requires lifestyle changes."
        
        result = self.analyzer.analyze(headline, content)
        
        self.assertIsNotNone(result)
        self.assertIn('headline_vs_content_score', result)
        self.assertLess(result['headline_vs_content_score'], 50)  # Should have low score
        
        self.logger.info(f"Misleading headline score: {result['headline_vs_content_score']}")

    def test_empty_inputs(self):
        """Test handling of empty inputs"""
        result = self.analyzer.analyze("", "")
        self.assertIsNotNone(result)
        self.assertIn('headline_vs_content_score', result) 

    def test_matching_headline(analyzer):
        headline = "New Study Shows Coffee Reduces Heart Disease Risk"
        content = "Recent research suggests that coffee may have cardiovascular benefits."
        
        result = analyzer.analyze(headline, content)
        
        assert result["headline_vs_content_score"] > 30
        assert result["contradiction_score"] < 0.3

    def test_contradictory_headline(analyzer):
        headline = "Coffee Increases Heart Disease Risk"
        content = "Studies show coffee decreases cardiovascular disease risk."
        
        result = analyzer.analyze(headline, content)
        
        assert result["headline_vs_content_score"] < 30
        assert result["contradiction_score"] > 0.3 