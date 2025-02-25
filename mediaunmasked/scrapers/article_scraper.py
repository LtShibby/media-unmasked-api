from typing import Dict, Optional
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup, NavigableString

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

    def _process_element(self, element) -> str:
        """Process an HTML element while preserving structure and formatting."""
        if isinstance(element, NavigableString):
            return str(element)

        tag_name = element.name
        
        if tag_name in ['p', 'div']:
            return '\n\n' + ''.join(self._process_element(child) for child in element.children).strip()
        
        elif tag_name in ['ul', 'ol']:
            items = []
            for li in element.find_all('li', recursive=False):
                prefix = '• ' if tag_name == 'ul' else f"{len(items) + 1}. "
                items.append(prefix + ''.join(self._process_element(child) for child in li.children).strip())
            return '\n' + '\n'.join(items) + '\n'
        
        elif tag_name == 'br':
            return '\n'
        
        elif tag_name in ['strong', 'b']:
            return '**' + ''.join(self._process_element(child) for child in element.children) + '**'
        
        elif tag_name in ['em', 'i']:
            return '_' + ''.join(self._process_element(child) for child in element.children) + '_'
        
        elif tag_name == 'a':
            text = ''.join(self._process_element(child) for child in element.children)
            href = element.get('href', '')
            return f'[{text}]({href})'
        
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            prefix = '#' * (level + 1)  # Add one more # for clarity
            return f'\n\n{prefix} ' + ''.join(self._process_element(child) for child in element.children).strip() + '\n'
        
        return ''.join(self._process_element(child) for child in element.children)

    def _extract_content(self, container) -> str:
        """Extract and format content from a container element."""
        if not container:
            return ''
        
        for unwanted in container.find_all(['script', 'style', 'iframe', 'aside']):
            unwanted.decompose()
        
        content = self._process_element(container)
        
        content = '\n'.join(line.strip() for line in content.split('\n'))
        content = '\n'.join(filter(None, content.split('\n')))
        
        return content.strip()

    def _extract_politifact(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract content from PolitiFact articles."""
        try:
            headline = soup.find('h1', class_='article__title') or soup.find('h1')
            headline = headline.get_text(strip=True) if headline else "No headline found"
            
            self.logger.info(f"Found headline: {headline}")
            
            content_div = soup.find('article', class_='article') or soup.select_one('.article__text, .m-textblock')
            content = self._extract_content(content_div) if content_div else "No content found"
            
            return {"headline": headline, "content": content}
        
        except Exception as e:
            self.logger.error(f"Error extracting PolitiFact content: {str(e)}")
            return {"headline": "Error", "content": f"Failed to extract content: {str(e)}"}

    def _extract_generic(self, soup: BeautifulSoup, domain: str) -> Dict[str, str]:
        """Fallback extraction method for unknown domains."""
        headline = soup.find('h1')
        headline_text = headline.get_text().strip() if headline else "No headline found"
        
        content_div = None
        common_selectors = ['article', 'main', '.content', '.article-content']
        
        for selector in common_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                break
        
        content = self._extract_content(content_div) if content_div else "No content found"
        
        return {"headline": headline_text, "content": content}

    def scrape_article(self, url: str) -> Optional[Dict[str, str]]:
        """
        Main function to scrape articles while maintaining structure.
        Returns a dictionary with headline and content.
        """
        html_content = self._fetch_page(url)
        if not html_content:
            self.logger.error("Failed to fetch page content")
            return None

        soup = BeautifulSoup(html_content, 'html.parser')
        domain = self._get_domain(url)
        
        self.logger.info(f"Scraping article from domain: {domain}")
        
        if 'politifact.com' in domain:
            return self._extract_politifact(soup)
        
        return self._extract_generic(soup, domain)
