from fastapi import APIRouter, HTTPException
import requests
import os
from app.db.meilisearch import get_meilisearch_client, get_search_client
from app.services.binance_service import binance_service
from app.services.news_service import news_service
from app.services.huggingface_service import huggingface_service
from app.services.meilisearch_admin import meilisearch_admin
from app.core.config import settings
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

@router.get("/health/meilisearch")
async def test_meilisearch():
    """Test MeiliSearch connection."""
    try:
        # Test with master key
        admin_client = get_meilisearch_client(use_search_key=False)
        health = admin_client.health()
        
        # Test with search key for reading operations
        search_client = get_search_client()
        
        # Get indexes using the admin client as it has the permission
        indexes = admin_client.get_indexes()
        index_list = []
        
        if isinstance(indexes, list):
            for index in indexes:
                if hasattr(index, 'uid'):
                    index_list.append({"uid": index.uid, "primary_key": index.primary_key})
        
        # Try a simple search with the search client to verify it works
        search_test_passed = True
        search_error = None
        if index_list:
            try:
                test_index = search_client.index(index_list[0]['uid'])
                test_search = test_index.search('')
                logger.info(f"Search test passed on index {index_list[0]['uid']}")
            except Exception as e:
                search_test_passed = False
                search_error = str(e)
                logger.error(f"Search test failed: {e}")
                
        # Check if search key is registered in MeiliSearch
        search_key = settings.MEILISEARCH_SEARCH_KEY
        is_valid_key = meilisearch_admin.verify_key_permissions(search_key) if search_key else False
        
        # If search failed but the health check works, it might be an API key issue
        key_diagnostics = {
            "search_key_exists": bool(search_key),
            "search_key_registered": is_valid_key,
            "search_key_working": search_test_passed
        }
        
        # Provide action item if there's an issue
        action_item = None
        if not search_test_passed:
            if not search_key:
                action_item = "Missing search key. Set MEILISEARCH_SEARCH_KEY in .env or run the application to generate one."
            elif not is_valid_key:
                action_item = "Search key is not registered with MeiliSearch. Run test_meilisearch_admin.py to create a valid key."
            else:
                action_item = "Search key exists but is not working. Try generating a new key with test_meilisearch_admin.py."
        
        return {
            "status": "connected",
            "health": health,
            "indexes": index_list,
            "key_diagnostics": key_diagnostics,
            "action_item": action_item,
            "search_error": search_error
        }
    except Exception as e:
        logger.error(f"MeiliSearch health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"MeiliSearch connection error: {str(e)}")

@router.get("/health/news-api")
async def test_news_api():
    """Test News API connection."""
    try:
        # Use our news service
        result = news_service.get_crypto_news(page_size=1)
        
        if "status" in result and result["status"] == "ok":
            return {
                "status": "connected",
                "total_results": result.get("totalResults", 0),
                "sample_data": result.get("articles", [])[:1]
            }
        elif "status" in result and result["status"] == "error":
            return {
                "status": "error",
                "message": result.get("message", "Unknown error")
            }
        else:
            return {
                "status": "error",
                "message": "Unexpected response format"
            }
    except Exception as e:
        logger.error(f"News API health check failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/health/binance-api")
async def test_binance_api():
    """Test Binance API connection."""
    try:
        # Use our binance service
        ticker_response = binance_service.get_ticker_price("BTCUSDT")
        exchange_info = binance_service.get_exchange_info()
        
        if "error" not in ticker_response and "error" not in exchange_info:
            return {
                "status": "connected",
                "btc_price": ticker_response.get("price"),
                "exchange_status": "available"
            }
        else:
            errors = []
            if "error" in ticker_response:
                errors.append(f"Ticker error: {ticker_response['error']}")
            if "error" in exchange_info:
                errors.append(f"Exchange info error: {exchange_info['error']}")
                
            return {
                "status": "error",
                "errors": errors
            }
    except Exception as e:
        logger.error(f"Binance API health check failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/health/huggingface-model")
async def test_huggingface_model():
    """Test Hugging Face model."""
    try:
        # Test with a simple sentiment analysis
        sample_texts = [
            "Bitcoin is showing strong bullish signals",
            "The crypto market is crashing badly"
        ]
        
        results = huggingface_service.analyze_sentiment(sample_texts)
        
        if results and isinstance(results, list) and len(results) == 2:
            # Check if we have the NumPy error
            if any("error" in r and "Numpy is not available" in r.get("error", "") for r in results):
                return {
                    "status": "error",
                    "message": "NumPy is not installed correctly. Please run: pip install numpy",
                    "sample_result": results
                }
            
            return {
                "status": "connected",
                "model": huggingface_service.model_name,
                "sample_result": results
            }
        else:
            return {
                "status": "error",
                "message": "Unexpected response format",
                "response": results
            }
    except Exception as e:
        logger.error(f"Hugging Face model check failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/health/keys")
async def test_keys():
    """Test API keys and permissions."""
    results = {}
    
    # Check MeiliSearch master key
    if settings.MEILISEARCH_MASTER_KEY:
        admin_client = get_meilisearch_client(use_search_key=False)
        try:
            health = admin_client.health()
            if health.get("status") == "available":
                results["master_key"] = {
                    "status": "valid",
                    "masked_key": settings.MEILISEARCH_MASTER_KEY[:8] + "..." if settings.MEILISEARCH_MASTER_KEY else None
                }
            else:
                results["master_key"] = {"status": "error", "message": "MeiliSearch not available"}
        except Exception as e:
            results["master_key"] = {"status": "invalid", "error": str(e)}
    else:
        results["master_key"] = {"status": "missing"}
    
    # Check MeiliSearch search key
    if settings.MEILISEARCH_SEARCH_KEY:
        is_registered = meilisearch_admin.verify_key_permissions(settings.MEILISEARCH_SEARCH_KEY)
        results["search_key"] = {
            "status": "registered" if is_registered else "unregistered",
            "masked_key": settings.MEILISEARCH_SEARCH_KEY[:8] + "..." if settings.MEILISEARCH_SEARCH_KEY else None
        }
        
        # Test search with this key
        search_client = get_search_client()
        try:
            # Get indexes to search in
            admin_client = get_meilisearch_client(use_search_key=False)
            indexes = admin_client.get_indexes()
            index_list = []
            
            if isinstance(indexes, list):
                for index in indexes:
                    if hasattr(index, 'uid'):
                        index_list.append({"uid": index.uid, "primary_key": index.primary_key})
            
            # Try to search with the search key
            if index_list:
                try:
                    test_index = search_client.index(index_list[0]['uid'])
                    test_search = test_index.search('')
                    results["search_key"]["search_test"] = "passed"
                except Exception as e:
                    results["search_key"]["search_test"] = "failed"
                    results["search_key"]["search_error"] = str(e)
        except Exception as e:
            results["search_key"]["status_check_error"] = str(e)
    else:
        results["search_key"] = {"status": "missing"}
    
    # Check Binance API keys
    if settings.BINANCE_TESTNET_API_KEY and settings.BINANCE_TESTNET_SECRET_KEY:
        try:
            # Test ticker price (public endpoint)
            ticker = binance_service.get_ticker_price("BTCUSDT")
            if "error" not in ticker:
                results["binance_keys"] = {
                    "status": "valid",
                    "masked_api_key": settings.BINANCE_TESTNET_API_KEY[:8] + "..." if settings.BINANCE_TESTNET_API_KEY else None
                }
                
                # Test account info (authenticated endpoint)
                account = binance_service.get_account_info()
                if "error" in account:
                    results["binance_keys"]["auth_status"] = "invalid"
                    results["binance_keys"]["auth_error"] = account["error"]
                else:
                    results["binance_keys"]["auth_status"] = "valid"
            else:
                results["binance_keys"] = {"status": "error", "error": ticker["error"]}
        except Exception as e:
            results["binance_keys"] = {"status": "error", "error": str(e)}
    else:
        results["binance_keys"] = {"status": "incomplete"}
    
    # Check News API key
    if settings.NEWS_API_KEY:
        try:
            result = news_service.get_crypto_news(page_size=1)
            if "status" in result and result["status"] == "ok":
                results["news_api_key"] = {
                    "status": "valid",
                    "masked_key": settings.NEWS_API_KEY[:8] + "..." if settings.NEWS_API_KEY else None
                }
            else:
                results["news_api_key"] = {"status": "invalid", "error": result.get("message", "Unknown error")}
        except Exception as e:
            results["news_api_key"] = {"status": "error", "error": str(e)}
    else:
        results["news_api_key"] = {"status": "missing"}
    
    return results

@router.get("/health/all")
async def test_all_apis():
    """Test all external API connections."""
    results = {
        "meilisearch": await test_meilisearch(),
        "news_api": await test_news_api(),
        "binance_api": await test_binance_api(),
        "huggingface_model": await test_huggingface_model()
    }
    
    # Add key diagnostics
    results["keys"] = await test_keys()
    
    # Determine overall status
    all_connected = all(
        result.get("status") == "connected" 
        for result in results.values() 
        if isinstance(result, dict) and "status" in result and result.get("status") != "not_configured"
    )
    
    results["overall_status"] = "healthy" if all_connected else "degraded"
    
    return results 