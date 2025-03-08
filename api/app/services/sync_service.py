import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.db.meilisearch import get_search_client
from app.db.repositories.market_data_repository import MarketDataRepository, OrderBookRepository, LiquidityZoneRepository
from app.db.repositories.trade_signals_repository import TradeSignalRepository, StrategyPerformanceRepository
from app.db.repositories.whale_tracking_repository import WhaleTransactionRepository, WhaleWalletRepository, TokenHoldingRepository
from app.db.mongodb import MongoDB
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class SyncService:
    """Service to synchronize data between MongoDB and MeiliSearch."""

    def __init__(self):
        # Initialize repositories lazily to avoid startup connection errors
        self._market_data_repo = None
        self._order_book_repo = None
        self._liquidity_zone_repo = None
        self._trade_signal_repo = None
        self._strategy_performance_repo = None
        self._whale_transaction_repo = None
        self._whale_wallet_repo = None
        self._token_holding_repo = None

    @property
    def market_data_repo(self):
        if self._market_data_repo is None:
            from app.db.repositories.market_data_repository import MarketDataRepository
            self._market_data_repo = MarketDataRepository()
        return self._market_data_repo
        
    @property
    def order_book_repo(self):
        if self._order_book_repo is None:
            from app.db.repositories.market_data_repository import OrderBookRepository
            self._order_book_repo = OrderBookRepository()
        return self._order_book_repo
        
    @property
    def liquidity_zone_repo(self):
        if self._liquidity_zone_repo is None:
            from app.db.repositories.market_data_repository import LiquidityZoneRepository
            self._liquidity_zone_repo = LiquidityZoneRepository()
        return self._liquidity_zone_repo
        
    @property
    def trade_signal_repo(self):
        if self._trade_signal_repo is None:
            from app.db.repositories.trade_signals_repository import TradeSignalRepository
            self._trade_signal_repo = TradeSignalRepository()
        return self._trade_signal_repo
        
    @property
    def strategy_performance_repo(self):
        if self._strategy_performance_repo is None:
            from app.db.repositories.trade_signals_repository import StrategyPerformanceRepository
            self._strategy_performance_repo = StrategyPerformanceRepository()
        return self._strategy_performance_repo
        
    @property
    def whale_transaction_repo(self):
        if self._whale_transaction_repo is None:
            from app.db.repositories.whale_tracking_repository import WhaleTransactionRepository
            self._whale_transaction_repo = WhaleTransactionRepository()
        return self._whale_transaction_repo
        
    @property
    def whale_wallet_repo(self):
        if self._whale_wallet_repo is None:
            from app.db.repositories.whale_tracking_repository import WhaleWalletRepository
            self._whale_wallet_repo = WhaleWalletRepository()
        return self._whale_wallet_repo
        
    @property
    def token_holding_repo(self):
        if self._token_holding_repo is None:
            from app.db.repositories.whale_tracking_repository import TokenHoldingRepository
            self._token_holding_repo = TokenHoldingRepository()
        return self._token_holding_repo

    async def sync_all(self) -> Dict[str, Any]:
        """Synchronize all data from MongoDB to MeiliSearch."""
        if not MongoDB.is_connected:
            logger.warning("Cannot sync data: MongoDB not connected")
            return {
                "success": False,
                "error": "MongoDB not connected",
                "synced_data": {}
            }

        try:
            search_client = get_search_client()
            result = {
                "success": True,
                "synced_data": {}
            }
            
            # Sync all data types
            try:
                result["synced_data"]["market_data"] = await self.market_data_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing market data: {e}")
                result["synced_data"]["market_data"] = {"error": str(e)}
            
            try:
                result["synced_data"]["order_books"] = await self.order_book_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing order books: {e}")
                result["synced_data"]["order_books"] = {"error": str(e)}
            
            try:
                result["synced_data"]["liquidity_zones"] = await self.liquidity_zone_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing liquidity zones: {e}")
                result["synced_data"]["liquidity_zones"] = {"error": str(e)}
            
            try:
                result["synced_data"]["trade_signals"] = await self.trade_signal_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing trade signals: {e}")
                result["synced_data"]["trade_signals"] = {"error": str(e)}
            
            try:
                result["synced_data"]["strategy_performance"] = await self.strategy_performance_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing strategy performance: {e}")
                result["synced_data"]["strategy_performance"] = {"error": str(e)}
            
            try:
                result["synced_data"]["whale_transactions"] = await self.whale_transaction_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing whale transactions: {e}")
                result["synced_data"]["whale_transactions"] = {"error": str(e)}
            
            try:
                result["synced_data"]["whale_wallets"] = await self.whale_wallet_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing whale wallets: {e}")
                result["synced_data"]["whale_wallets"] = {"error": str(e)}
            
            try:
                result["synced_data"]["token_holdings"] = await self.token_holding_repo.sync_to_meilisearch(search_client)
            except Exception as e:
                logger.error(f"Error syncing token holdings: {e}")
                result["synced_data"]["token_holdings"] = {"error": str(e)}
            
            return result
            
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error during sync: {e}")
            return {
                "success": False,
                "error": f"MongoDB connection error: {str(e)}",
                "synced_data": {}
            }
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return {
                "success": False,
                "error": str(e),
                "synced_data": {}
            }
    
    async def sync_specific(self, data_types: List[str]) -> Dict[str, Any]:
        """Synchronize specific data types from MongoDB to MeiliSearch."""
        if not MongoDB.is_connected:
            logger.warning("Cannot sync data: MongoDB not connected")
            return {
                "success": False,
                "error": "MongoDB not connected",
                "synced_data": {}
            }
            
        valid_types = [
            "market_data", "order_books", "liquidity_zones", 
            "trade_signals", "strategy_performance", 
            "whale_transactions", "whale_wallets", "token_holdings"
        ]
        
        invalid_types = [t for t in data_types if t not in valid_types]
        if invalid_types:
            return {
                "success": False,
                "error": f"Invalid data types: {', '.join(invalid_types)}",
                "valid_types": valid_types
            }
        
        try:
            search_client = get_search_client()
            result = {
                "success": True,
                "synced_data": {}
            }
            
            sync_map = {
                "market_data": self.market_data_repo,
                "order_books": self.order_book_repo,
                "liquidity_zones": self.liquidity_zone_repo,
                "trade_signals": self.trade_signal_repo,
                "strategy_performance": self.strategy_performance_repo,
                "whale_transactions": self.whale_transaction_repo,
                "whale_wallets": self.whale_wallet_repo,
                "token_holdings": self.token_holding_repo
            }
            
            for data_type in data_types:
                try:
                    result["synced_data"][data_type] = await sync_map[data_type].sync_to_meilisearch(search_client)
                except Exception as e:
                    logger.error(f"Error syncing {data_type}: {e}")
                    result["synced_data"][data_type] = {"error": str(e)}
            
            return result
            
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error during specific sync: {e}")
            return {
                "success": False,
                "error": f"MongoDB connection error: {str(e)}",
                "synced_data": {}
            }
        except Exception as e:
            logger.error(f"Error during specific sync: {e}")
            return {
                "success": False,
                "error": str(e),
                "synced_data": {}
            }

async def get_sync_service() -> SyncService:
    """Get a synchronized service instance."""
    return SyncService() 