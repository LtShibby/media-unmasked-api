import unittest
from bs4 import BeautifulSoup
from mediaunmasked.scrapers.article_scraper import ArticleScraper

class TestArticleScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = ArticleScraper()

    def test_process_element_formatting(self):
        """Test that _process_element preserves various HTML formatting."""
        # Test complex nested HTML with multiple formatting elements
        html = """
        <div>
            <h1>Main Title</h1>
            <p>This is a <strong>bold</strong> and <em>italic</em> text.</p>
            <p>This is a <a href="https://example.com">link</a> in a paragraph.</p>
            <ul>
                <li>First <strong>important</strong> item</li>
                <li>Second item with <em>emphasis</em></li>
            </ul>
            <ol>
                <li>Numbered item <a href="test.com">with link</a></li>
                <li>Another numbered item</li>
            </ol>
            <div>
                Nested <br/>content with<br />line breaks
            </div>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        formatted_content = self.scraper._process_element(soup.div)

        expected_output = """
## Main Title

This is a **bold** and _italic_ text.

This is a [link](https://example.com) in a paragraph.

• First **important** item
• Second item with _emphasis_

1. Numbered item [with link](test.com)
2. Another numbered item

Nested
content with
line breaks""".strip()

        # Normalize whitespace for comparison
        formatted_content = '\n'.join(line.strip() for line in formatted_content.split('\n') if line.strip())
        expected_output = '\n'.join(line.strip() for line in expected_output.split('\n') if line.strip())
        
        self.assertEqual(formatted_content, expected_output)

    def test_extract_snopes_article(self):
        """Test extraction of a Snopes-style article with formatting."""
        html = """
        <html>
            <body>
                <header>
                    <h1>Fact Check: Test Claim</h1>
                </header>
                <article>
                    <h2>The Claim</h2>
                    <p>This is the <strong>main claim</strong> being tested.</p>
                    <h2>The Facts</h2>
                    <ul>
                        <li>First important fact with <em>emphasis</em></li>
                        <li>Second fact with a <a href="source.com">source</a></li>
                    </ul>
                    <p>Additional <strong>important</strong> context.</p>
                </article>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.scraper._extract_article(soup, 'snopes.com')

        expected_content = """
## The Claim

This is the **main claim** being tested.

## The Facts

• First important fact with _emphasis_
• Second fact with a [source](source.com)

Additional **important** context.""".strip()

        self.assertEqual(result['headline'], 'Fact Check: Test Claim')
        # Normalize whitespace for comparison
        actual_content = '\n'.join(line.strip() for line in result['content'].split('\n') if line.strip())
        expected_content = '\n'.join(line.strip() for line in expected_content.split('\n') if line.strip())
        self.assertEqual(actual_content, expected_content)

    def test_extract_politifact_article(self):
        """Test extraction of a PolitiFact-style article with formatting."""
        html = """
        <html>
            <body>
                <h1 class="article__title">Test Political Claim</h1>
                <article class="article">
                    <div class="article__text">
                        <p>Here's a claim with <strong>bold text</strong> and <em>italics</em>.</p>
                        <h3>Our Analysis</h3>
                        <ul>
                            <li>Evidence point 1</li>
                            <li>Evidence point 2 with <a href="proof.com">proof</a></li>
                        </ul>
                        <p>Final assessment with <strong>key points</strong>.</p>
                    </div>
                </article>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.scraper._extract_article(soup, 'politifact.com')

        expected_content = """
Here's a claim with **bold text** and _italics_.

### Our Analysis

• Evidence point 1
• Evidence point 2 with [proof](proof.com)

Final assessment with **key points**.""".strip()

        self.assertEqual(result['headline'], 'Test Political Claim')
        # Normalize whitespace for comparison
        actual_content = '\n'.join(line.strip() for line in result['content'].split('\n') if line.strip())
        expected_content = '\n'.join(line.strip() for line in expected_content.split('\n') if line.strip())
        self.assertEqual(actual_content, expected_content)

    def test_extract_generic_article(self):
        """Test extraction of a generic article with formatting."""
        html = """
        <html>
            <body>
                <h1>Generic Article Title</h1>
                <main>
                    <p>Opening paragraph with <strong>bold</strong> text.</p>
                    <div class="content">
                        <h2>Section Title</h2>
                        <p>Content with <em>italic</em> text and <a href="ref.com">reference</a>.</p>
                        <ul>
                            <li>Point <strong>one</strong></li>
                            <li>Point <em>two</em></li>
                        </ul>
                    </div>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.scraper._extract_article(soup, 'generic.com')

        expected_content = """
Opening paragraph with **bold** text.

## Section Title

Content with _italic_ text and [reference](ref.com).

• Point **one**
• Point _two_""".strip()

        self.assertEqual(result['headline'], 'Generic Article Title')
        # Normalize whitespace for comparison
        actual_content = '\n'.join(line.strip() for line in result['content'].split('\n') if line.strip())
        expected_content = '\n'.join(line.strip() for line in expected_content.split('\n') if line.strip())
        self.assertEqual(actual_content, expected_content)

if __name__ == '__main__':
    unittest.main() 