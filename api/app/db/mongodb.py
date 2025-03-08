import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.core.config import settings
import asyncio
import urllib.parse

# This is a placeholder for MongoDB connection
# Will be implemented in the next phase
# For now it returns None to allow API to run without MongoDB

logger = logging.getLogger(__name__)

class MongoDB:
    client = None
    db = None
    is_connected = False
    connection_attempted = False

# Simplified connection function
async def connect_to_mongodb():
    if MongoDB.is_connected:
        return MongoDB.client
        
    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
    
    try:
        # Create client
        MongoDB.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        await MongoDB.client.admin.command('ping')
        
        # Use cryptov7 as database name regardless of what's in .env
        # to avoid hostname-as-database issues
        db_name = "cryptov7"
        
        MongoDB.db = MongoDB.client[db_name]
        MongoDB.is_connected = True
        logger.info(f"Connected to MongoDB: {settings.MONGODB_URI}")
        logger.info(f"Using database: {db_name}")
        
        # Don't create indexes at startup - can cause blocking
        return MongoDB.client
            
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        MongoDB.is_connected = False
        # Don't raise - let application continue
        return None

async def close_mongodb_connection():
    """Close MongoDB connection."""
    if MongoDB.client:
        logger.info("Closing MongoDB connection...")
        MongoDB.client.close()
        MongoDB.is_connected = False
        logger.info("MongoDB connection closed.")

async def create_indexes():
    """Create indexes for collections."""
    if not MongoDB.is_connected or not MongoDB.db:
        logger.warning("Cannot create indexes: MongoDB not connected")
        return
        
    try:
        # Order book & market data indexes
        await MongoDB.db.market_data.create_index([("symbol", 1), ("timestamp", -1)])
        await MongoDB.db.order_book.create_index([("symbol", 1), ("timestamp", -1)])
        
        # Trade signals indexes
        await MongoDB.db.trade_signals.create_index([("symbol", 1), ("timestamp", -1)])
        await MongoDB.db.trade_signals.create_index([("strategy", 1)])
        await MongoDB.db.trade_signals.create_index([("signal_type", 1)])
        
        # Whale transactions indexes
        await MongoDB.db.whale_transactions.create_index([("wallet_address", 1)])
        await MongoDB.db.whale_transactions.create_index([("transaction_hash", 1)])
        await MongoDB.db.whale_transactions.create_index([("token", 1), ("timestamp", -1)])
        
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")

def get_database():
    """Get MongoDB database instance."""
    if not MongoDB.is_connected or not MongoDB.db:
        # Don't raise error - this will stall the application startup
        return None
    return MongoDB.db 