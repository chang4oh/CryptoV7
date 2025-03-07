from fastapi import FastAPI, Depends, BackgroundTasks
from app.routers import search, health, market, news
from app.db.meilisearch import get_meilisearch_client, get_search_client
from app.services.background_tasks import schedule_meilisearch_sync
from app.services.meilisearch_admin import meilisearch_admin
from app.core.config import settings
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="CryptoV7 API",
    description="Trading and analytics platform with MeiliSearch integration",
    version="0.1.0",
)

# Include routers
app.include_router(search.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(news.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting application...")
    
    # Set up MeiliSearch indexes and keys
    try:
        # Setup indexes first
        setup_result = meilisearch_admin.setup_indexes()
        if "error" in setup_result:
            logger.error(f"Error setting up MeiliSearch indexes: {setup_result['error']}")
        
        # Check if search key exists and is valid
        search_key = settings.MEILISEARCH_SEARCH_KEY
        
        # If no search key is set in env vars, or it's not valid, create a new one
        if not search_key or not meilisearch_admin.verify_key_permissions(search_key):
            logger.warning("Search key is missing or invalid. Creating a new one...")
            search_key = meilisearch_admin.setup_search_key()
            
            if search_key:
                logger.info("Search key created successfully")
                
                # Try writing to .env file to update the search key for future runs
                try:
                    env_path = os.path.join(os.getcwd(), '.env')
                    
                    if os.path.exists(env_path):
                        with open(env_path, 'r') as file:
                            env_lines = file.readlines()
                        
                        # Update or add the search key
                        search_key_found = False
                        for i, line in enumerate(env_lines):
                            if line.startswith('MEILISEARCH_SEARCH_KEY='):
                                env_lines[i] = f'MEILISEARCH_SEARCH_KEY={search_key}\n'
                                search_key_found = True
                                break
                        
                        if not search_key_found:
                            env_lines.append(f'\nMEILISEARCH_SEARCH_KEY={search_key}\n')
                        
                        with open(env_path, 'w') as file:
                            file.writelines(env_lines)
                            
                        logger.info("Search key updated in .env file")
                    else:
                        logger.warning(".env file not found, couldn't save search key")
                except Exception as e:
                    logger.error(f"Error updating .env file: {e}")
            else:
                logger.error("Failed to create search key")
        else:
            # Verify the existing key has the right permissions
            logger.info("Using existing search key")
    
    except Exception as e:
        logger.error(f"Error setting up MeiliSearch: {e}")
        # Allow application to continue running without MeiliSearch

@app.get("/")
async def root():
    """Root endpoint to check API health."""
    return {"message": "Welcome to CryptoV7 API", "status": "healthy"}

@app.get("/api/sync", tags=["admin"])
async def sync_meilisearch(background_tasks: BackgroundTasks):
    """Trigger MeiliSearch synchronization."""
    await schedule_meilisearch_sync(background_tasks)
    return {"message": "Synchronization scheduled"} 