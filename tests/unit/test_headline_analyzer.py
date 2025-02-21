import pytest
from src.mediaunmasked.analyzers.headline_analyzer import HeadlineAnalyzer

@pytest.fixture
def analyzer():
    return HeadlineAnalyzer()

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