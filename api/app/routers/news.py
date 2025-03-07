from fastapi import APIRouter, Query, HTTPException, Path
from typing import Optional, List, Dict, Any
from app.services.news_service import news_service
import logging

router = APIRouter(prefix="/news", tags=["news"])
logger = logging.getLogger(__name__)

@router.get("/crypto")
async def get_crypto_news(
    query: str = Query("cryptocurrency", description="Search query"),
    page_size: int = Query(10, ge=1, le=100, description="Number of results to return"),
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Get cryptocurrency news articles.
    
    This endpoint fetches news articles related to cryptocurrencies from NewsAPI
    and enriches them with sentiment analysis.
    """
    try:
        news_data = news_service.get_crypto_news(query=query, page_size=page_size, page=page)
        
        if news_data.get("status") == "error":
            error_message = news_data.get("message", "Unknown error")
            if "apiKey" in error_message:
                raise HTTPException(status_code=401, detail="News API key is invalid or not configured")
            else:
                raise HTTPException(status_code=400, detail=error_message)
        
        # Add some metadata to the response
        if "articles" in news_data:
            news_data["query"] = query
            
            # Check for sentiment analysis errors
            sentiment_errors = 0
            for article in news_data["articles"]:
                if article.get("sentiment", {}).get("error"):
                    sentiment_errors += 1
            
            if sentiment_errors > 0:
                news_data["sentiment_analysis_errors"] = sentiment_errors
                news_data["sentiment_analysis_status"] = "partial" if sentiment_errors < len(news_data["articles"]) else "failed"
            else:
                news_data["sentiment_analysis_status"] = "success"
        
        return news_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting crypto news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbol/{symbol}")
async def get_news_by_symbol(
    symbol: str = Path(..., description="Cryptocurrency symbol (e.g., BTC, ETH)"),
    page_size: int = Query(5, ge=1, le=100, description="Number of results to return")
):
    """
    Get news for a specific cryptocurrency symbol.
    
    This endpoint fetches news articles specific to a cryptocurrency
    identified by its symbol (e.g., BTC for Bitcoin).
    """
    try:
        symbol = symbol.upper()  # Normalize to uppercase
        news_data = news_service.get_news_by_symbol(symbol=symbol, page_size=page_size)
        
        if news_data.get("status") == "error":
            error_message = news_data.get("message", "Unknown error")
            if "apiKey" in error_message:
                raise HTTPException(status_code=401, detail="News API key is invalid or not configured")
            else:
                raise HTTPException(status_code=400, detail=error_message)
        
        # Add some metadata to the response
        if "articles" in news_data:
            news_data["symbol"] = symbol
            
            # Check for sentiment analysis errors
            sentiment_errors = 0
            for article in news_data["articles"]:
                if article.get("sentiment", {}).get("error"):
                    sentiment_errors += 1
            
            if sentiment_errors > 0:
                news_data["sentiment_analysis_errors"] = sentiment_errors
                news_data["sentiment_analysis_status"] = "partial" if sentiment_errors < len(news_data["articles"]) else "failed"
            else:
                news_data["sentiment_analysis_status"] = "success"
        
        return news_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting news for symbol {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def check_news_api_health():
    """
    Check the health of the News API integration.
    
    This endpoint tests the connection to News API and verifies that
    the API key is working correctly.
    """
    try:
        # Try to fetch a single article to check if the API is working
        result = news_service.get_crypto_news(page_size=1)
        
        if result.get("status") == "ok":
            return {
                "status": "healthy",
                "message": "News API is working correctly",
                "api_key_valid": True
            }
        else:
            error_message = result.get("message", "Unknown error")
            if "apiKey" in error_message:
                return {
                    "status": "error",
                    "message": "News API key is invalid or not configured",
                    "api_key_valid": False
                }
            else:
                return {
                    "status": "error",
                    "message": error_message,
                    "api_key_valid": True  # Key is valid but there's another issue
                }
    except Exception as e:
        logger.error(f"Error checking News API health: {e}")
        return {
            "status": "error",
            "message": str(e),
            "api_key_valid": None  # Unknown
        } 