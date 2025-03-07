from app.db.meilisearch import get_meilisearch_client

class TradesRepository:
    """Repository for trade data access operations."""
    
    async def get_recent_trades(self, limit=1000):
        """
        Get recent trades from the database.
        
        This is a placeholder implementation. In a real application, 
        this would fetch data from MongoDB.
        """
        # Placeholder for demonstration
        return [
            {
                "_id": f"trade_{i}",
                "symbol": "BTC/USDT",
                "side": "buy" if i % 2 == 0 else "sell",
                "price": 50000 + (i * 10),
                "quantity": 0.1,
                "timestamp": "2025-03-07T00:00:00Z",
                "pnl": i * 5.0,
                "strategy": "dca" if i % 3 == 0 else "trend_following"
            }
            for i in range(10)  # Just 10 dummy trades for example
        ]
    
    async def sync_trades_to_meilisearch(self, limit=1000):
        """Synchronize recent trades to MeiliSearch."""
        trades = await self.get_recent_trades(limit=limit)
        client = get_meilisearch_client()
        trades_index = client.index('trades_index')
        
        processed_trades = [
            {
                "id": str(trade["_id"]),
                "symbol": trade["symbol"],
                "side": trade["side"],
                "price": trade["price"],
                "quantity": trade["quantity"],
                "timestamp": trade["timestamp"],
                "pnl": trade["pnl"],
                "strategy": trade["strategy"]
            }
            for trade in trades
        ]
        
        # Add documents to MeiliSearch
        trades_index.add_documents(processed_trades) 