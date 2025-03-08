import logging
from fastapi import FastAPI, Depends, BackgroundTasks
from app.routers import search, health, market, news, mongodb_test, sync
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection, MongoDB
from app.db.meilisearch import get_meilisearch_client, get_search_client, get_admin_client
from app.services.background_tasks import schedule_meilisearch_sync
from app.services.meilisearch_admin import meilisearch_admin
from app.core.config import settings
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

# Check if we're in safe mode
SAFE_MODE = os.environ.get("CRYPTOV7_SAFE_MODE", "false").lower() == "true"
if SAFE_MODE:
    logger.info("Running in SAFE MODE - will tolerate service failures")

app = FastAPI(
    title="CryptoV7 API",
    description="Cryptocurrency trading analytics and search API",
    version="0.1.0",
)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(mongodb_test.router, prefix="/api/mongodb")  # Change to /api/mongodb for clarity
app.include_router(sync.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting application...")
    
    # Connect to MongoDB without blocking if it fails
    try:
        await connect_to_mongodb()
        if MongoDB.is_connected:
            logger.info("MongoDB connection established")
        else:
            logger.warning("MongoDB connection failed, but application will continue")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        logger.warning("Application will continue without MongoDB functionality")
    
    # Configure MeiliSearch (skip if in safe mode)
    if not SAFE_MODE:
        try:
            # Test connection with master key
            logger.info("Testing MeiliSearch connection...")
            admin_client = get_admin_client()
            
            # Verify health
            health = admin_client.health()
            logger.info(f"MeiliSearch health: {health.get('status', 'unknown')}")
            
            # Check if search key exists and is valid
            if settings.MEILISEARCH_SEARCH_KEY:
                try:
                    # Test search key
                    search_client = get_search_client()
                    indexes = search_client.get_indexes()
                    logger.info(f"Search key is valid. Found {len(indexes.get('results', [])) if isinstance(indexes, dict) else 0} indexes")
                except Exception as e:
                    logger.warning(f"Search key validation failed: {str(e)}")
            else:
                logger.warning("No search key provided. Search functionality may be limited.")
            
            # No need to create or modify indexes here - they're already set up
            
        except Exception as e:
            logger.error(f"Error connecting to MeiliSearch: {str(e)}")
            logger.warning("Application will continue with limited search functionality")
    else:
        logger.info("Skipping MeiliSearch initialization in SAFE MODE")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application resources on shutdown."""
    # Close MongoDB connection
    await close_mongodb_connection()
    logger.info("Application shutdown complete")

@app.get("/")
async def root():
    """Root endpoint for quick API check."""
    return {
        "message": "Welcome to CryptoV7 API",
        "version": "0.1.0",
        "status": "online",
        "mode": "SAFE MODE" if SAFE_MODE else "NORMAL"
    } 