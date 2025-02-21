from typing import Dict, Optional
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from ..utils.logging_config import setup_logging

class ArticleScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        setup_logging()
        self.logger = logging.getLogger(__name__)

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content with error handling."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def _extract_snopes(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract content from Snopes articles."""
        # Get headline from any h1 tag since it doesn't have a specific class
        headline_elem = soup.find('h1')
        headline = headline_elem.get_text().strip() if headline_elem else ''
        self.logger.info(f"Found headline: {headline}")
        
        # Try to find the article content
        article = soup.find('article')
        if article:
            self.logger.info("Found article tag")
            # Remove unwanted elements
            for unwanted in article.find_all(['script', 'style', 'iframe', 'aside']):
                unwanted.decompose()
            
            # Get all paragraphs from the article
            paragraphs = article.find_all('p')
            if paragraphs:
                content = ' '.join(p.get_text().strip() for p in paragraphs)
            else:
                content = article.get_text().strip()
        else:
            self.logger.warning("No article tag found")
            content = ''
            
        return {"headline": headline, "content": content}

    def _extract_politifact(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract content from PolitiFact articles."""
        try:
            headline = soup.find('h1', class_='article__title')
            if headline:
                headline = headline.get_text().strip()
            else:
                headline = soup.find('h1')
                headline = headline.get_text().strip() if headline else "No headline found"
            
            self.logger.info(f"Found headline: {headline}")
            
            content_div = soup.find('article', class_='article')
            if content_div:
                # Remove unwanted elements
                for unwanted in content_div.find_all(['script', 'style', 'iframe', 'aside']):
                    unwanted.decompose()
                content = ' '.join(p.get_text().strip() for p in content_div.find_all('p'))
            else:
                # Try alternative content selectors
                content_selectors = ['.article__text', '.m-textblock']
                content = ''
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        content = ' '.join(p.get_text().strip() for p in content_elem.find_all('p'))
                        break
                    
            if not content:
                self.logger.warning("No content found in article")
                content = "No content found"
            
            return {"headline": headline, "content": content}
            
        except Exception as e:
            self.logger.error(f"Error extracting PolitiFact content: {str(e)}")
            return {"headline": "Error", "content": f"Failed to extract content: {str(e)}"}

    def scrape_article(self, url: str) -> Optional[Dict[str, str]]:
        """
        Main function to scrape fact-checking articles.
        Returns a dictionary with headline and content.
        """
        html_content = self._fetch_page(url)
        if not html_content:
            self.logger.error("Failed to fetch page content")
            return None

        soup = BeautifulSoup(html_content, 'html.parser')
        domain = self._get_domain(url)
        
        self.logger.info(f"Scraping article from domain: {domain}")

        # Select appropriate extractor based on domain
        if 'snopes.com' in domain:
            result = self._extract_snopes(soup)
            if not result['headline'] or not result['content']:
                self.logger.warning("Failed to extract content from Snopes article")
                self.logger.debug(f"HTML content: {html_content[:500]}...")
            return result
        elif 'politifact.com' in domain:
            return self._extract_politifact(soup)
        else:
            # Generic extraction fallback
            headline = soup.find('h1').get_text().strip() if soup.find('h1') else ''
            
            # Try common content selectors
            content_selectors = ['article', 'main', '.content', '.article-content']
            content = ''
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.find_all(['script', 'style', 'iframe', 'aside']):
                        unwanted.decompose()
                    content = ' '.join(p.get_text().strip() for p in content_div.find_all('p'))
                    break

            return {"headline": headline, "content": content} 