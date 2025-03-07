import meilisearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_meilisearch_client(use_search_key=False):
    """
    Get configured MeiliSearch client instance.
    
    Args:
        use_search_key: If True, use the search key instead of master key.
                       Search key has more limited permissions and should be used
                       for read operations like searches.
    """
    api_key = settings.MEILISEARCH_SEARCH_KEY if use_search_key else settings.MEILISEARCH_MASTER_KEY
    
    # Fallback to master key if search key is not set
    if use_search_key and not api_key:
        logger.warning("Search key not set, falling back to master key")
        api_key = settings.MEILISEARCH_MASTER_KEY
        
    return meilisearch.Client(
        settings.MEILISEARCH_URL,
        api_key
    )

def get_search_client():
    """Get MeiliSearch client with search key for read-only operations."""
    return get_meilisearch_client(use_search_key=True) 