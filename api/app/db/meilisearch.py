import logging
import os
import meilisearch
from app.core.config import settings

logger = logging.getLogger(__name__)

SAFE_MODE = os.environ.get("CRYPTOV7_SAFE_MODE", "false").lower() == "true"

# Attempt to import meilisearch, but don't fail if it's not installed
try:
    import meilisearch
    MEILISEARCH_AVAILABLE = True
except ImportError:
    logger.warning("Meilisearch module not available. Search functionality will be limited.")
    MEILISEARCH_AVAILABLE = False

# Only import settings if meilisearch is available
if MEILISEARCH_AVAILABLE:
    try:
        from app.core.config import settings
    except Exception as e:
        logger.error(f"Failed to import settings: {str(e)}")
        MEILISEARCH_AVAILABLE = False

class DummyClient:
    """Placeholder client for when meilisearch is not available."""
    def __init__(self, *args, **kwargs):
        pass
        
    def index(self, *args, **kwargs):
        return DummyIndex()

class DummyIndex:
    """Placeholder index for when meilisearch is not available."""
    def search(self, *args, **kwargs):
        return {"hits": [], "processingTimeMs": 0, "query": "", "limit": 0, "offset": 0, "estimatedTotalHits": 0}
    
    def add_documents(self, *args, **kwargs):
        return {"taskUid": 0}

def get_meilisearch_client(use_search_key=False):
    """
    Get configured MeiliSearch client instance.
    
    Args:
        use_search_key: If True, use the search key instead of master key.
                       Search key has more limited permissions and should be used
                       for read operations like searches.
    """
    # If use_search_key is True, use search key, otherwise use master key
    api_key = settings.MEILISEARCH_SEARCH_KEY if use_search_key else settings.MEILISEARCH_MASTER_KEY
    
    if not api_key:
        logger.warning(f"No {'search' if use_search_key else 'master'} key provided.")
    
    return meilisearch.Client(
        settings.MEILISEARCH_URL,
        api_key
    )

def get_search_client():
    """Get MeiliSearch client with search key for read-only operations."""
    return get_meilisearch_client(use_search_key=True)

def get_admin_client():
    """Get MeiliSearch client with master key for admin operations."""
    return get_meilisearch_client(use_search_key=False) 