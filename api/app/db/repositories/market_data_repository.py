from datetime import datetime
from typing import Dict, List, Optional, Any
from app.db.repositories.base_repository import BaseRepository
from app.models.market_data import MarketData, OrderBook, LiquidityZone
import logging

logger = logging.getLogger(__name__)

class MarketDataRepository(BaseRepository[MarketData]):
    """Repository for market data."""
    
    def __init__(self):
        super().__init__("market_data", MarketData)
    
    async def get_latest_candle(self, symbol: str, interval: str = "1m") -> Optional[MarketData]:
        """Get the latest candle for a symbol and interval."""
        query = {"symbol": symbol, "interval": interval}
        sort = [("timestamp", -1)]  # Sort by timestamp descending
        
        result = await self.collection.find_one(query, sort=sort)
        if result:
            if '_id' in result and result['_id']:
                result['_id'] = str(result['_id'])
            return MarketData(**result)
        return None
    
    async def get_candles(
        self, 
        symbol: str, 
        interval: str = "1m",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MarketData]:
        """Get candles for a symbol in a time range."""
        query = {"symbol": symbol, "interval": interval}
        
        if start_time or end_time:
            time_query = {}
            if start_time:
                time_query["$gte"] = start_time
            if end_time:
                time_query["$lte"] = end_time
            query["timestamp"] = time_query
        
        sort = [("timestamp", 1)]  # Sort by timestamp ascending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def get_symbols(self) -> List[str]:
        """Get all available symbols."""
        result = await self.collection.distinct("symbol")
        return result
    
    async def sync_to_meilisearch(self, search_client, limit: int = 1000) -> int:
        """Sync recent market data to MeiliSearch."""
        try:
            # Get the most recent candles
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$group": {"_id": {"symbol": "$symbol", "interval": "$interval"}, "doc": {"$first": "$$ROOT"}}},
                {"$replaceRoot": {"newRoot": "$doc"}},
                {"$limit": limit}
            ]
            
            results = await self.aggregate(pipeline)
            
            if not results:
                logger.info("No market data to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for doc in results:
                if '_id' in doc and doc['_id']:
                    doc['id'] = str(doc['_id'])
                    del doc['_id']
                
                # Convert datetime to ISO string
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('market_data_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} market data documents to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing market data to MeiliSearch: {str(e)}")
            raise


class OrderBookRepository(BaseRepository[OrderBook]):
    """Repository for order book data."""
    
    def __init__(self):
        super().__init__("order_book", OrderBook)
    
    async def get_latest_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get the latest order book for a symbol."""
        query = {"symbol": symbol}
        sort = [("timestamp", -1)]  # Sort by timestamp descending
        
        result = await self.collection.find_one(query, sort=sort)
        if result:
            if '_id' in result and result['_id']:
                result['_id'] = str(result['_id'])
            return OrderBook(**result)
        return None
    
    async def sync_to_meilisearch(self, search_client, limit: int = 100) -> int:
        """Sync recent order books to MeiliSearch."""
        try:
            # Get the most recent order books for each symbol
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$group": {"_id": "$symbol", "doc": {"$first": "$$ROOT"}}},
                {"$replaceRoot": {"newRoot": "$doc"}},
                {"$limit": limit}
            ]
            
            results = await self.aggregate(pipeline)
            
            if not results:
                logger.info("No order book data to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for doc in results:
                if '_id' in doc and doc['_id']:
                    doc['id'] = str(doc['_id'])
                    del doc['_id']
                
                # Convert datetime to ISO string
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                
                # Flatten bids and asks for searching
                doc['bid_prices'] = [bid['price'] for bid in doc.get('bids', [])]
                doc['ask_prices'] = [ask['price'] for ask in doc.get('asks', [])]
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('order_book_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} order book documents to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing order books to MeiliSearch: {str(e)}")
            raise


class LiquidityZoneRepository(BaseRepository[LiquidityZone]):
    """Repository for liquidity zones."""
    
    def __init__(self):
        super().__init__("liquidity_zones", LiquidityZone)
    
    async def find_active_zones(
        self, 
        symbol: str, 
        current_price: float,
        buffer_percentage: float = 0.05  # Default 5% buffer
    ) -> List[LiquidityZone]:
        """Find active liquidity zones for a symbol near the current price."""
        buffer = current_price * buffer_percentage
        
        query = {
            "symbol": symbol,
            "price_low": {"$lte": current_price + buffer},
            "price_high": {"$gte": current_price - buffer}
        }
        
        sort = [("strength", -1)]  # Sort by strength descending
        
        return await self.find_many(query, sort=sort)
    
    async def sync_to_meilisearch(self, search_client) -> int:
        """Sync all liquidity zones to MeiliSearch."""
        try:
            # Get all liquidity zones
            liquidity_zones = await self.find_many({})
            
            if not liquidity_zones:
                logger.info("No liquidity zones to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for zone in liquidity_zones:
                doc = zone.model_dump()
                
                if '_id' in doc and doc['_id']:
                    doc['id'] = doc['_id']
                    del doc['_id']
                
                # Convert datetime objects to ISO strings
                if 'start_time' in doc and isinstance(doc['start_time'], datetime):
                    doc['start_time'] = doc['start_time'].isoformat()
                
                if 'end_time' in doc and isinstance(doc['end_time'], datetime):
                    doc['end_time'] = doc['end_time'].isoformat()
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('liquidity_zones_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} liquidity zones to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing liquidity zones to MeiliSearch: {str(e)}")
            raise 