import requests
import logging
import time
from app.core.config import settings
from app.services.huggingface_service import huggingface_service
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class NewsService:
    """Service for fetching and processing news from News API."""
    
    def __init__(self):
        self.api_key = settings.NEWS_API_KEY
        self.base_url = settings.NEWS_API_BASE_URL
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_ttl = 300  # 5 minutes in seconds
    
    def _should_refresh_cache(self, cache_key: str) -> bool:
        """Check if the cache for a given key needs refreshing."""
        if cache_key not in self._cache_timestamp:
            return True
            
        current_time = time.time()
        return current_time - self._cache_timestamp[cache_key] > self._cache_ttl
    
    def get_crypto_news(self, query: str = "cryptocurrency", page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """
        Get crypto news articles.
        
        Args:
            query: Search query term
            page_size: Number of results per page
            page: Page number
            
        Returns:
            Dictionary with news articles and metadata
        """
        # Check API key
        if not self.api_key:
            logger.warning("News API key not configured")
            return {
                "status": "error", 
                "message": "News API key not configured",
                "articles": []
            }
        
        # Create cache key
        cache_key = f"{query}_{page_size}_{page}"
        
        # Return cached data if available and not expired
        if cache_key in self._cache and not self._should_refresh_cache(cache_key):
            logger.info(f"Using cached news data for query: {query}")
            return self._cache[cache_key]
        
        # Prepare API request
        endpoint = "/everything"
        url = f"{self.base_url}{endpoint}"
        
        params = {
            "q": query,
            "apiKey": self.api_key,
            "pageSize": page_size,
            "page": page,
            "language": "en",
            "sortBy": "publishedAt"
        }
        
        try:
            logger.info(f"Fetching news for query: {query}")
            response = requests.get(url, params=params, timeout=10)
            
            # Check for API errors
            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"News API error: {error_data.get('message', 'Unknown error')}")
                return {
                    "status": "error",
                    "code": response.status_code,
                    "message": error_data.get("message", "Unknown error"),
                    "articles": []
                }
            
            # Process successful response
            data = response.json()
            
            # Analyze sentiment of news titles if articles exist
            if "articles" in data and data["articles"]:
                titles = [article["title"] for article in data["articles"]]
                
                # Try sentiment analysis, but don't fail if it errors
                try:
                    sentiments = huggingface_service.analyze_crypto_news(titles)
                    
                    # Add sentiment to each article
                    for i, article in enumerate(data["articles"]):
                        if i < len(sentiments):
                            article["sentiment"] = sentiments[i]
                except Exception as e:
                    logger.error(f"Error during sentiment analysis: {e}")
                    # Add dummy sentiment with error info
                    for article in data["articles"]:
                        article["sentiment"] = {
                            "label": "ERROR",
                            "score": 0.0,
                            "error": f"Sentiment analysis failed: {str(e)}",
                            "interpretation": "Neutral"
                        }
            
            # Cache the result
            self._cache[cache_key] = data
            self._cache_timestamp[cache_key] = time.time()
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching news: {e}")
            return {
                "status": "error",
                "message": f"Request error: {str(e)}",
                "articles": []
            }
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
            return {
                "status": "error",
                "message": str(e),
                "articles": []
            }
    
    def get_news_by_symbol(self, symbol: str = "BTC", page_size: int = 5) -> Dict[str, Any]:
        """
        Get news specific to a cryptocurrency symbol.
        
        Args:
            symbol: Cryptocurrency symbol
            page_size: Number of results to return
            
        Returns:
            Dictionary with news articles and metadata
        """
        symbols_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOT": "polkadot",
            "DOGE": "dogecoin",
            "SHIB": "shiba inu",
            "MATIC": "polygon",
            "LINK": "chainlink"
        }
        
        # Map symbol to coin name or use the symbol itself
        query = symbols_map.get(symbol.upper(), symbol)
        
        return self.get_crypto_news(query=f"cryptocurrency {query}", page_size=page_size)

# Create a singleton instance
news_service = NewsService() 