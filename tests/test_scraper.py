import unittest
from mediaunmasked.scrapers.article_scraper import ArticleScraper
import logging

class TestArticleScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = ArticleScraper()
        # Configure logging for tests
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def test_cna_article(self):
        """Test scraping a Channel News Asia article"""
        url = "https://www.channelnewsasia.com/singapore/singapore-mccy-sg-culture-pass-arts-culture-heritage-4951451"
        result = self.scraper.scrape_article(url)
        
        # Log the result
        self.logger.info("Scraping Result:")
        self.logger.info(f"Headline: {result.get('headline', 'No headline found')}")
        self.logger.info(f"Content Preview: {result.get('content', 'No content found')[:200]}...")
        
        # Basic assertions
        self.assertIsNotNone(result)
        self.assertIn('headline', result)
        self.assertIn('content', result)
        self.assertNotEqual(result['headline'], '')
        self.assertNotEqual(result['content'], '')
        
        # Print full result for manual inspection
        print("\nFull Scraping Result:")
        print(f"Headline: {result['headline']}")
        print(f"\nContent Preview (first 500 chars):\n{result['content'][:500]}...")

    def test_invalid_url(self):
        """Test scraping an invalid URL"""
        url = "https://invalid.url.that.doesnt.exist"
        result = self.scraper.scrape_article(url)
        self.assertIsNone(result)

    def test_empty_url(self):
        """Test scraping with empty URL"""
        url = ""
        result = self.scraper.scrape_article(url)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 