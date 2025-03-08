from datetime import datetime
from typing import Dict, List, Optional, Any
from app.db.repositories.base_repository import BaseRepository
from app.models.trade_signals import TradeSignal, StrategyPerformance, SignalType
import logging

logger = logging.getLogger(__name__)

class TradeSignalRepository(BaseRepository[TradeSignal]):
    """Repository for trade signals."""
    
    def __init__(self):
        super().__init__("trade_signals", TradeSignal)
    
    async def get_signals_by_strategy(
        self, 
        strategy: str,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TradeSignal]:
        """Get signals for a specific strategy."""
        query = {"strategy": strategy}
        
        if symbol:
            query["symbol"] = symbol
            
        if start_time or end_time:
            time_query = {}
            if start_time:
                time_query["$gte"] = start_time
            if end_time:
                time_query["$lte"] = end_time
            query["timestamp"] = time_query
        
        sort = [("timestamp", -1)]  # Sort by timestamp descending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def get_signals_by_symbol(
        self, 
        symbol: str,
        signal_type: Optional[SignalType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TradeSignal]:
        """Get signals for a specific symbol."""
        query = {"symbol": symbol}
        
        if signal_type:
            query["signal_type"] = signal_type
            
        if start_time or end_time:
            time_query = {}
            if start_time:
                time_query["$gte"] = start_time
            if end_time:
                time_query["$lte"] = end_time
            query["timestamp"] = time_query
        
        sort = [("timestamp", -1)]  # Sort by timestamp descending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def calculate_strategy_performance(
        self,
        strategy: str,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        timeframe: str = "all"
    ) -> Optional[StrategyPerformance]:
        """Calculate performance metrics for a strategy."""
        # Build the match query
        match_query = {"strategy": strategy}
        
        if symbol:
            match_query["symbol"] = symbol
            
        if start_time or end_time:
            time_query = {}
            if start_time:
                time_query["$gte"] = start_time
            if end_time:
                time_query["$lte"] = end_time
            match_query["timestamp"] = time_query
        
        # Pipeline to calculate performance metrics
        pipeline = [
            {"$match": match_query},
            {"$sort": {"timestamp": 1}},
            {"$group": {
                "_id": {"strategy": "$strategy", "symbol": "$symbol" if symbol else None},
                "signals": {"$push": "$$ROOT"},
                "total_signals": {"$sum": 1},
                "start_date": {"$first": "$timestamp"},
                "end_date": {"$last": "$timestamp"}
            }}
        ]
        
        results = await self.aggregate(pipeline)
        
        if not results or len(results) == 0:
            logger.info(f"No signals found for strategy {strategy}")
            return None
        
        # Process the results and calculate additional metrics
        result = results[0]
        signals = result.get("signals", [])
        
        # Calculate win/loss metrics based on position outcomes
        # This is simplified and would need to be customized based on how you determine successful trades
        win_count = 0
        loss_count = 0
        total_profit = 0
        total_loss = 0
        
        for i in range(len(signals) - 1):
            current_signal = signals[i]
            next_signal = signals[i + 1]
            
            # Skip if not a buy-sell pair
            if current_signal.get("signal_type") != "buy" or next_signal.get("signal_type") != "sell":
                continue
                
            entry_price = current_signal.get("price", 0)
            exit_price = next_signal.get("price", 0)
            
            if exit_price > entry_price:  # Profit
                win_count += 1
                total_profit += (exit_price - entry_price) / entry_price
            else:  # Loss
                loss_count += 1
                total_loss += (entry_price - exit_price) / entry_price
        
        # Calculate metrics
        avg_win = total_profit / win_count if win_count > 0 else 0
        avg_loss = total_loss / loss_count if loss_count > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Create StrategyPerformance object
        performance = StrategyPerformance(
            strategy=strategy,
            symbol=symbol,
            start_date=result.get("start_date"),
            end_date=result.get("end_date"),
            total_signals=result.get("total_signals", 0),
            win_count=win_count,
            loss_count=loss_count,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_drawdown=0.0,  # Would need more complex calculation
            timeframe=timeframe
        )
        
        return performance
    
    async def sync_to_meilisearch(self, search_client, limit: int = 1000) -> int:
        """Sync recent trade signals to MeiliSearch."""
        try:
            # Get recent trade signals
            signals = await self.find_many({}, limit=limit, sort=[("timestamp", -1)])
            
            if not signals:
                logger.info("No trade signals to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for signal in signals:
                doc = signal.model_dump()
                
                if '_id' in doc and doc['_id']:
                    doc['id'] = doc['_id']
                    del doc['_id']
                
                # Convert datetime to ISO string
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                
                # Convert indicator data to searchable format
                if 'indicators' in doc and isinstance(doc['indicators'], dict):
                    for key, value in doc['indicators'].items():
                        # Flatten first level indicators for searching
                        if isinstance(value, (int, float, str, bool)):
                            doc[f"indicator_{key}"] = value
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('trade_signals_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} trade signals to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing trade signals to MeiliSearch: {str(e)}")
            raise


class StrategyPerformanceRepository(BaseRepository[StrategyPerformance]):
    """Repository for strategy performance metrics."""
    
    def __init__(self):
        super().__init__("strategy_performance", StrategyPerformance)
    
    async def get_best_strategies(
        self, 
        top_n: int = 5,
        min_trades: int = 10
    ) -> List[StrategyPerformance]:
        """Get the best performing strategies based on profit factor."""
        query = {"total_signals": {"$gte": min_trades}}
        sort = [("profit_factor", -1)]  # Sort by profit factor descending
        
        return await self.find_many(query, limit=top_n, sort=sort)
    
    async def sync_to_meilisearch(self, search_client) -> int:
        """Sync all strategy performance metrics to MeiliSearch."""
        try:
            # Get all performance records
            performance_records = await self.find_many({})
            
            if not performance_records:
                logger.info("No strategy performance records to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for record in performance_records:
                doc = record.model_dump()
                
                if '_id' in doc and doc['_id']:
                    doc['id'] = doc['_id']
                    del doc['_id']
                
                # Convert datetime objects to ISO strings
                if 'start_date' in doc and isinstance(doc['start_date'], datetime):
                    doc['start_date'] = doc['start_date'].isoformat()
                
                if 'end_date' in doc and isinstance(doc['end_date'], datetime):
                    doc['end_date'] = doc['end_date'].isoformat()
                
                # Add calculated win_rate field for searching
                if 'win_count' in doc and 'total_signals' in doc:
                    if doc['total_signals'] > 0:
                        doc['win_rate'] = doc['win_count'] / doc['total_signals']
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('strategy_performance_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} strategy performance records to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing strategy performance to MeiliSearch: {str(e)}")
            raise 