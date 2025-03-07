from fastapi import APIRouter, Query, HTTPException, status, Response
from typing import Optional, Dict, Any
from app.db.meilisearch import get_search_client
import logging
import requests
from app.core.config import settings

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)

def check_meilisearch_connection():
    """Check if MeiliSearch is running and accessible."""
    try:
        client = get_search_client()
        health = client.health()
        return True, client
    except requests.exceptions.ConnectionError:
        logger.error("MeiliSearch connection error: server might be down")
        return False, None
    except Exception as e:
        logger.error(f"MeiliSearch error: {str(e)}")
        return False, None

@router.get("/trades")
async def search_trades(
    response: Response,
    q: str = Query("", description="Search query string"),
    filters: Optional[str] = Query(None, description="Filter expression"),
    sort: Optional[str] = Query(None, description="Sort expression"),
    limit: int = Query(20, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """Search trades with optional filtering and sorting."""
    is_connected, client = check_meilisearch_connection()
    
    if not is_connected:
        # Return a graceful error response
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "error": "MeiliSearch service unavailable",
            "message": "The search engine is currently unavailable. Please try again later."
        }
    
    try:
        trades_index = client.index('trades_index')
        
        search_params = {
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            search_params["filter"] = filters
        
        if sort:
            search_params["sort"] = [sort]
        
        results = trades_index.search(q, search_params)
        return results
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 500
        error_msg = str(e)
        
        if status_code == 401 or status_code == 403:
            logger.error(f"Authentication error with MeiliSearch: {error_msg}")
            error_msg = "Search authentication failed. The API key might be invalid."
        
        raise HTTPException(status_code=status_code, detail=error_msg)
    except Exception as e:
        logger.exception(f"Error searching trades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search engine error: {str(e)}")

@router.get("/news")
async def search_news(
    response: Response,
    q: str = Query("", description="Search query string"),
    filters: Optional[str] = Query(None, description="Filter expression"),
    sort: Optional[str] = Query(None, description="Sort expression"),
    limit: int = Query(20, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """Search news with optional filtering and sorting."""
    is_connected, client = check_meilisearch_connection()
    
    if not is_connected:
        # Return a graceful error response
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "error": "MeiliSearch service unavailable",
            "message": "The search engine is currently unavailable. Please try again later."
        }
    
    try:
        news_index = client.index('news_index')
        
        search_params = {
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            search_params["filter"] = filters
        
        if sort:
            search_params["sort"] = [sort]
        
        results = news_index.search(q, search_params)
        return results
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 500
        error_msg = str(e)
        
        if status_code == 401 or status_code == 403:
            logger.error(f"Authentication error with MeiliSearch: {error_msg}")
            error_msg = "Search authentication failed. The API key might be invalid."
        
        raise HTTPException(status_code=status_code, detail=error_msg)
    except Exception as e:
        logger.exception(f"Error searching news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search engine error: {str(e)}")

@router.get("/health")
async def check_search_health():
    """Check the health of the search service."""
    try:
        client = get_search_client()
        
        # Check basic connection
        health = client.health()
        
        # List indexes to verify more complex operations
        indexes = client.get_indexes()
        
        index_names = []
        if isinstance(indexes, list):
            index_names = [idx.uid for idx in indexes if hasattr(idx, 'uid')]
        
        # Try to check if the search key has proper permissions
        has_search_permission = True
        error_msg = None
        
        if index_names:
            try:
                # Try to search in the first index
                test_index = client.index(index_names[0])
                test_results = test_index.search("")
            except Exception as e:
                has_search_permission = False
                error_msg = str(e)
        
        return {
            "status": "healthy" if has_search_permission else "degraded",
            "meilisearch_url": settings.MEILISEARCH_URL,
            "health": health,
            "indexes": index_names,
            "search_permission": has_search_permission,
            "error": error_msg
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "unavailable",
            "message": "Cannot connect to MeiliSearch server",
            "meilisearch_url": settings.MEILISEARCH_URL
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "meilisearch_url": settings.MEILISEARCH_URL
        } 