import streamlit as st
from ..analyzers.bias_analyzer import BiasAnalyzer
from ..scrapers.article_scraper import ArticleScraper
from ..utils.logging_config import setup_logging
import plotly.graph_objects as go

def create_sentiment_gauge(score: float) -> go.Figure:
    """Create a gauge chart for sentiment visualization."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score * 100,
        title = {'text': "Sentiment Score"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "lightgray"},
                {'range': [33, 66], 'color': "gray"},
                {'range': [66, 100], 'color': "darkgray"}
            ],
        }
    ))
    return fig

def main():
    # Set up logging
    setup_logging()
    
    # Initialize components
    scraper = ArticleScraper()
    analyzer = BiasAnalyzer()
    
    # Set up the Streamlit interface
    st.title("Media Bias Analyzer")
    st.write("Analyze bias and sentiment in news articles")
    
    # URL input
    url = st.text_input("Enter article URL:", "https://www.snopes.com/articles/469232/musk-son-told-trump-shut-up/")
    
    if st.button("Analyze"):
        with st.spinner("Analyzing article..."):
            # Scrape the article
            article = scraper.scrape_article(url)
            
            if article:
                # Show article details
                st.subheader("Article Details")
                st.write(f"**Headline:** {article['headline']}")
                
                with st.expander("Show Article Content"):
                    st.write(article['content'])
                
                # Analyze content
                result = analyzer.analyze(article['content'])
                
                # Display results in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Sentiment Analysis")
                    st.write(f"**Overall Sentiment:** {result.sentiment}")
                    fig = create_sentiment_gauge(result.bias_score / 100)
                    st.plotly_chart(fig)
                
                with col2:
                    st.subheader("Bias Analysis")
                    st.write(f"**Detected Bias:** {result.bias}")
                    st.write(f"**Confidence Score:** {result.bias_score:.1f}%")
                
                # Show flagged phrases
                if result.flagged_phrases:
                    st.subheader("Potentially Biased Phrases")
                    for phrase in result.flagged_phrases:
                        st.warning(phrase)
                else:
                    st.info("No potentially biased phrases detected")
                    
            else:
                st.error("Failed to fetch article. Please check the URL and try again.")

if __name__ == "__main__":
    main() 