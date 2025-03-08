from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Query
from typing import Dict, List, Any, Optional
from app.services.sync_service import SyncService, get_sync_service
import logging
from app.db.mongodb import MongoDB

router = APIRouter(prefix="/sync", tags=["sync"])
logger = logging.getLogger(__name__)

@router.post("/all")
async def sync_all_data(
    background_tasks: BackgroundTasks,
    sync_service: SyncService = Depends(get_sync_service)
) -> Dict[str, Any]:
    """
    Synchronize all data from MongoDB to MeiliSearch.
    
    This operation runs in the background and may take some time.
    """
    # Check MongoDB connection first
    if not MongoDB.is_connected:
        return {
            "success": False,
            "message": "MongoDB not connected - cannot sync data",
            "details": "Please check MongoDB connection before attempting to sync"
        }
    
    # Run in background to avoid blocking
    background_tasks.add_task(sync_service.sync_all)
    
    return {
        "success": True,
        "message": "Data synchronization started in background",
        "details": "Check server logs for progress updates"
    }

@router.post("/specific")
async def sync_specific_data(
    background_tasks: BackgroundTasks,
    data_types: List[str] = Query(..., description="Data types to sync, e.g., market_data, trade_signals"),
    sync_service: SyncService = Depends(get_sync_service)
) -> Dict[str, Any]:
    """
    Synchronize specific data types from MongoDB to MeiliSearch.
    
    Available data types:
    - market_data
    - order_books
    - liquidity_zones
    - trade_signals
    - strategy_performance
    - whale_transactions
    - whale_wallets
    - token_holdings
    
    This operation runs in the background and may take some time.
    """
    # Check MongoDB connection first
    if not MongoDB.is_connected:
        return {
            "success": False,
            "message": "MongoDB not connected - cannot sync data",
            "details": "Please check MongoDB connection before attempting to sync"
        }
    
    # Validate data types
    valid_types = [
        "market_data", "order_books", "liquidity_zones", 
        "trade_signals", "strategy_performance", 
        "whale_transactions", "whale_wallets", "token_holdings"
    ]
    
    invalid_types = [t for t in data_types if t not in valid_types]
    if invalid_types:
        return {
            "success": False,
            "message": f"Invalid data types: {', '.join(invalid_types)}",
            "valid_types": valid_types
        }
    
    # Run in background to avoid blocking
    background_tasks.add_task(sync_service.sync_specific, data_types)
    
    return {
        "success": True,
        "message": f"Synchronization of {', '.join(data_types)} started in background",
        "details": "Check server logs for progress updates"
    } 