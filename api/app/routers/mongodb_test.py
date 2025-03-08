from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random
import logging
import time
from app.models.market_data import MarketData
from app.models.trade_signals import TradeSignal, SignalType, SignalSource
from app.models.whale_tracking import WhaleTransaction, BlockchainNetwork, TransactionType
from app.db.mongodb import MongoDB, connect_to_mongodb

router = APIRouter(tags=["mongodb"])
logger = logging.getLogger(__name__)

# Initialize repositories lazily to avoid circular imports
_market_data_repo = None
_trade_signal_repo = None
_whale_transaction_repo = None

def get_market_data_repo():
    global _market_data_repo
    if _market_data_repo is None:
        from app.db.repositories.market_data_repository import MarketDataRepository
        _market_data_repo = MarketDataRepository()
    return _market_data_repo

def get_trade_signal_repo():
    global _trade_signal_repo
    if _trade_signal_repo is None:
        from app.db.repositories.trade_signals_repository import TradeSignalRepository
        _trade_signal_repo = TradeSignalRepository()
    return _trade_signal_repo

def get_whale_transaction_repo():
    global _whale_transaction_repo
    if _whale_transaction_repo is None:
        from app.db.repositories.whale_tracking_repository import WhaleTransactionRepository
        _whale_transaction_repo = WhaleTransactionRepository()
    return _whale_transaction_repo

@router.get("/status")
async def check_mongodb_status() -> Dict[str, Any]:
    """Check the MongoDB connection status."""
    if MongoDB.is_connected and MongoDB.db:
        try:
            # Test the connection with a ping
            await MongoDB.client.admin.command('ping')
            
            # Get server information
            server_info = await MongoDB.client.server_info()
            version = server_info.get("version", "Unknown")
            
            # Get database statistics
            db_stats = await MongoDB.db.command("dbStats")
            
            return {
                "status": "connected",
                "database": MongoDB.db.name,
                "mongodb_version": version,
                "collections": db_stats.get("collections", 0),
                "documents": db_stats.get("objects", 0),
                "storage_size_mb": round(db_stats.get("storageSize", 0) / (1024 * 1024), 2),
                "indexes": db_stats.get("indexes", 0)
            }
        except Exception as e:
            # Try to reconnect
            try:
                await connect_to_mongodb()
                return {
                    "status": "reconnected",
                    "message": "Connection was lost but has been restored",
                    "database": MongoDB.db.name if MongoDB.db else "unknown"
                }
            except Exception as reconnect_error:
                return {
                    "status": "error",
                    "message": f"Connection error: {str(e)}",
                    "reconnect_error": str(reconnect_error)
                }
    else:
        # Try to establish a connection
        try:
            client = await connect_to_mongodb()
            if client:
                return {
                    "status": "connected",
                    "message": "Connection established successfully",
                    "database": MongoDB.db.name
                }
            else:
                return {
                    "status": "error",
                    "message": "Could not establish MongoDB connection",
                    "details": "Check server logs for more information"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to MongoDB: {str(e)}",
                "details": "Check MongoDB Atlas configuration and network access"
            }

@router.post("/market-data/sample")
async def create_sample_market_data() -> Dict[str, Any]:
    """Create sample market data for testing."""
    try:
        # Generate 10 sample candles for BTC/USDT and ETH/USDT
        samples = []
        
        for symbol in ["BTC/USDT", "ETH/USDT"]:
            # Create candles for the last 10 periods
            base_time = datetime.utcnow() - timedelta(minutes=10)
            base_price = 50000.0 if symbol == "BTC/USDT" else 3000.0
            
            for i in range(10):
                timestamp = base_time + timedelta(minutes=i)
                price_change = random.uniform(-100, 100)  # Price change in this period
                price = base_price + price_change
                
                candle = MarketData(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=price - random.uniform(10, 50),
                    high=price + random.uniform(10, 100),
                    low=price - random.uniform(10, 100),
                    close=price,
                    volume=random.uniform(1, 100),
                    trades=random.randint(10, 1000),
                    interval="1m",
                    source="test"
                )
                samples.append(candle)
        
        # Insert the samples
        ids = await get_market_data_repo().insert_many(samples)
        
        return {
            "success": True,
            "message": f"Created {len(ids)} sample market data documents",
            "document_ids": ids
        }
    except Exception as e:
        logger.error(f"Error creating sample market data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sample market data: {str(e)}"
        )

@router.post("/trade-signals/sample")
async def create_sample_trade_signals() -> Dict[str, Any]:
    """Create sample trade signals for testing."""
    try:
        # Generate 10 sample trade signals
        samples = []
        
        strategies = ["RSI-Crossover", "MACD-Signal", "Bollinger-Breakout", "EMA-Cross", "Fibonacci-Retracement"]
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "DOT/USDT"]
        
        for _ in range(10):
            timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 100))
            strategy = random.choice(strategies)
            symbol = random.choice(symbols)
            
            # Random price based on symbol
            if "BTC" in symbol:
                price = random.uniform(40000, 60000)
            elif "ETH" in symbol:
                price = random.uniform(2500, 4000)
            else:
                price = random.uniform(10, 500)
                
            signal = TradeSignal(
                symbol=symbol,
                timestamp=timestamp,
                signal_type=random.choice(list(SignalType)),
                source=random.choice(list(SignalSource)),
                strategy=strategy,
                price=price,
                confidence=random.uniform(0.5, 1.0),
                indicators={
                    "rsi": random.uniform(10, 90),
                    "macd": random.uniform(-20, 20),
                    "volume": random.uniform(100, 10000)
                },
                timeframe=random.choice(["1m", "5m", "15m", "1h", "4h", "1d"]),
                tags=random.sample(["trend", "reversal", "breakout", "support", "resistance"], k=random.randint(1, 3))
            )
            samples.append(signal)
        
        # Insert the samples
        ids = await get_trade_signal_repo().insert_many(samples)
        
        return {
            "success": True,
            "message": f"Created {len(ids)} sample trade signals",
            "document_ids": ids
        }
    except Exception as e:
        logger.error(f"Error creating sample trade signals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sample trade signals: {str(e)}"
        )

@router.post("/whale-transactions/sample")
async def create_sample_whale_transactions() -> Dict[str, Any]:
    """Create sample whale transactions for testing."""
    try:
        # Generate 10 sample whale transactions
        samples = []
        
        tokens = ["BTC", "ETH", "USDT", "SOL", "ADA", "DOT", "AVAX", "MATIC"]
        whale_addresses = [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xabcdef1234567890abcdef1234567890abcdef12",
            "0x7890abcdef1234567890abcdef1234567890abcd",
            "0xdef1234567890abcdef1234567890abcdef12345",
            "0x567890abcdef1234567890abcdef1234567890ab"
        ]
        
        for _ in range(10):
            timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            token = random.choice(tokens)
            address = random.choice(whale_addresses)
            
            # Different value ranges for different tokens
            if token == "BTC":
                amount = random.uniform(5, 100)
                usd_value = amount * random.uniform(40000, 60000)
            elif token == "ETH":
                amount = random.uniform(10, 1000)
                usd_value = amount * random.uniform(2500, 4000)
            else:
                amount = random.uniform(10000, 1000000)
                usd_value = amount * random.uniform(0.1, 100)
                
            tx = WhaleTransaction(
                wallet_address=address,
                transaction_hash=f"0x{random.randbytes(32).hex()}",
                network=random.choice(list(BlockchainNetwork)),
                timestamp=timestamp,
                transaction_type=random.choice(list(TransactionType)),
                token=token,
                amount=amount,
                usd_value=usd_value,
                to_address=random.choice(whale_addresses + [None]),
                gas_fee=random.uniform(0.001, 0.1),
                block_number=random.randint(10000000, 20000000),
                significant=random.random() > 0.7,
                tags=random.sample(["high_value", "exchange_deposit", "exchange_withdrawal", "new_wallet"], k=random.randint(0, 2))
            )
            samples.append(tx)
        
        # Insert the samples
        ids = await get_whale_transaction_repo().insert_many(samples)
        
        return {
            "success": True,
            "message": f"Created {len(ids)} sample whale transactions",
            "document_ids": ids
        }
    except Exception as e:
        logger.error(f"Error creating sample whale transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sample whale transactions: {str(e)}"
        )

@router.get("/market-data/latest")
async def get_latest_market_data(
    symbol: str = Query(..., description="Market symbol (e.g., BTC/USDT)"),
    interval: str = Query("1m", description="Candle interval")
) -> Dict[str, Any]:
    """Get the latest market data for a symbol."""
    try:
        # Get the latest candle
        candle = await get_market_data_repo().get_latest_candle(symbol, interval)
        
        if not candle:
            return {
                "success": False,
                "message": f"No market data found for {symbol} with interval {interval}"
            }
            
        return {
            "success": True,
            "data": candle,
            "symbol": symbol,
            "interval": interval
        }
    except Exception as e:
        logger.error(f"Error getting latest market data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting latest market data: {str(e)}"
        )

@router.get("/trade-signals/strategy")
async def get_strategy_signals(
    strategy: str = Query(..., description="Strategy name"),
    symbol: Optional[str] = Query(None, description="Optional symbol filter"),
    limit: int = Query(10, description="Number of signals to return")
) -> Dict[str, Any]:
    """Get trade signals for a specific strategy."""
    try:
        # Get signals for the strategy
        signals = await get_trade_signal_repo().get_signals_by_strategy(
            strategy=strategy,
            symbol=symbol,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(signals),
            "strategy": strategy,
            "symbol": symbol,
            "signals": signals
        }
    except Exception as e:
        logger.error(f"Error getting strategy signals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting strategy signals: {str(e)}"
        )

@router.get("/whale-transactions/recent")
async def get_recent_whale_transactions(
    token: Optional[str] = Query(None, description="Token filter"),
    limit: int = Query(10, description="Number of transactions to return")
) -> Dict[str, Any]:
    """Get recent whale transactions, optionally filtered by token."""
    try:
        # Get recent transactions
        transactions = await get_whale_transaction_repo().get_recent_transactions(
            token=token,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(transactions),
            "token": token,
            "transactions": transactions
        }
    except Exception as e:
        logger.error(f"Error getting recent whale transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recent whale transactions: {str(e)}"
        ) 