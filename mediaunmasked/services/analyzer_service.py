from mediaunmasked.analyzers.headline_analyzer import HeadlineAnalyzer

class AnalyzerService:
    def __init__(self):
        self.headline_analyzer = HeadlineAnalyzer()

    async def analyze_content(self, headline: str, content: str):
        result = self.headline_analyzer.analyze(headline, content)
        return result 