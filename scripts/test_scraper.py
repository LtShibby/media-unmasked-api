from mediaunmasked.scrapers.article_scraper import ArticleScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scraper():
    scraper = ArticleScraper()
    url = "https://www.channelnewsasia.com/singapore/singapore-mccy-sg-culture-pass-arts-culture-heritage-4951451"
    
    logger.info(f"Testing scraper with URL: {url}")
    
    try:
        result = scraper.scrape_article(url)
        
        if result:
            print("\nScraping Successful!")
            print("-" * 50)
            print(f"Headline: {result['headline']}")
            print("-" * 50)
            print("Content Preview (first 500 chars):")
            print(result['content'][:500])
            print("...")
            print("-" * 50)
            print(f"Total content length: {len(result['content'])} characters")
        else:
            print("Scraping failed - no result returned")
            
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_scraper() 