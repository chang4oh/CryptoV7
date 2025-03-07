import meilisearch
import logging
from app.core.config import settings
import time

logger = logging.getLogger(__name__)

class MeiliSearchAdminService:
    """Service for managing MeiliSearch administration tasks."""
    
    def __init__(self):
        """Initialize with master key (required for admin operations)."""
        self.admin_client = meilisearch.Client(
            settings.MEILISEARCH_URL,
            settings.MEILISEARCH_MASTER_KEY
        )
    
    def create_search_key(self, key_name="search_key", expires_at=None):
        """
        Create a search-only API key in MeiliSearch.
        
        Args:
            key_name: A descriptive name for this key
            expires_at: Optional timestamp when the key should expire
                        (None means it won't expire)
        
        Returns:
            The created key information dict, including the key itself
        """
        # Define search-only permissions
        actions = ["search", "documents.get", "indexes.get", "stats.get"]
        indexes = ["*"]  # All indexes
        
        try:
            # First check if a key with this description already exists
            keys = self.admin_client.get_keys()
            
            if isinstance(keys, dict) and 'results' in keys:
                existing_keys = keys['results']
            else:
                existing_keys = keys
                
            for key in existing_keys:
                if isinstance(key, dict) and key.get('description') == key_name:
                    logger.info(f"Key '{key_name}' already exists")
                    return key
            
            # Create a new key if it doesn't exist
            key_info = self.admin_client.create_key({
                "description": key_name,
                "actions": actions,
                "indexes": indexes,
                "expiresAt": expires_at
            })
            
            logger.info(f"Created new search key: {key_name}")
            return key_info
        except Exception as e:
            logger.error(f"Error creating search key: {e}")
            return {"error": str(e)}
    
    def delete_key(self, key):
        """Delete an API key."""
        try:
            self.admin_client.delete_key(key)
            logger.info(f"Deleted key: {key}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting key: {e}")
            return {"error": str(e)}
    
    def setup_search_key(self):
        """
        Setup a search key if needed and return it.
        
        This will create a search key if it doesn't exist and return the key value.
        """
        # Try to create a new search key (will return existing one if it already exists)
        key_info = self.create_search_key()
        
        if "error" in key_info:
            logger.error(f"Failed to create search key: {key_info['error']}")
            return None
        
        # Return the key value
        return key_info.get("key")
    
    def verify_key_permissions(self, key):
        """Verify that a key has the necessary permissions."""
        try:
            keys = self.admin_client.get_keys()
            
            if isinstance(keys, dict) and 'results' in keys:
                key_list = keys['results']
            else:
                key_list = keys
                
            for k in key_list:
                if isinstance(k, dict) and k.get('key') == key:
                    # Key found, check permissions
                    actions = k.get('actions', [])
                    if "search" in actions:
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error verifying key permissions: {e}")
            return False
    
    def setup_indexes(self):
        """Setup required indexes and their settings."""
        try:
            # Create trades index
            trades_index = self.admin_client.index('trades_index')
            trades_index.update_settings({
                "searchableAttributes": [
                    "symbol",
                    "side",
                    "strategy"
                ],
                "filterableAttributes": [
                    "symbol",
                    "side",
                    "timestamp",
                    "pnl",
                    "strategy"
                ],
                "sortableAttributes": [
                    "timestamp",
                    "price",
                    "quantity",
                    "pnl"
                ]
            })
            logger.info("Trades index configured")
            
            # Create news index
            news_index = self.admin_client.index('news_index')
            news_index.update_settings({
                "searchableAttributes": [
                    "title",
                    "content",
                    "source"
                ],
                "filterableAttributes": [
                    "publication_date",
                    "source",
                    "sentiment_score"
                ],
                "sortableAttributes": [
                    "publication_date",
                    "sentiment_score"
                ]
            })
            logger.info("News index configured")
            
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error setting up indexes: {e}")
            return {"error": str(e)}

# Create a singleton instance
meilisearch_admin = MeiliSearchAdminService() 