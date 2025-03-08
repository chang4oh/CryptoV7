#!/usr/bin/env python
"""
MeiliSearch Cloud Connection Test Script

This script tests connection to both local and cloud MeiliSearch
instances using the keys from your .env file.
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv
import meilisearch
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MeiliSearch connection details
LOCAL_URL = "http://localhost:7700"
CLOUD_URL = "https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io"
MASTER_KEY = os.environ.get("MEILISEARCH_MASTER_KEY", "")
SEARCH_KEY = os.environ.get("MEILISEARCH_SEARCH_KEY", "")
ADMIN_KEY = os.environ.get("MEILISEARCH_ADMIN_KEY", "")

def test_instance(url, name):
    """Test connection to a MeiliSearch instance"""
    logger.info(f"\n=== Testing {name} MeiliSearch Instance ===")
    logger.info(f"URL: {url}")
    
    # Test basic connectivity (no auth)
    try:
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            logger.info(f"✅ {name} instance is running")
            logger.info(f"Health status: {response.json().get('status')}")
        else:
            logger.error(f"❌ {name} instance health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ {name} instance not reachable: {str(e)}")
        return False
    
    # Test with master key
    if MASTER_KEY:
        try:
            client = meilisearch.Client(url, MASTER_KEY)
            stats = client.get_stats()
            logger.info(f"✅ Master key is valid for {name}")
            logger.info(f"Stats: {len(stats.get('indexes', [])) if isinstance(stats, dict) else 0} indexes found")
        except Exception as e:
            logger.error(f"❌ Master key validation failed for {name}: {str(e)}")
    else:
        logger.warning("⚠️ No master key provided")
    
    # Test with search key
    if SEARCH_KEY:
        try:
            client = meilisearch.Client(url, SEARCH_KEY)
            indexes = client.get_indexes()
            index_count = len(indexes.get('results', [])) if isinstance(indexes, dict) else 0
            logger.info(f"✅ Search key is valid for {name}")
            logger.info(f"Found {index_count} searchable indexes")
        except Exception as e:
            logger.error(f"❌ Search key validation failed for {name}: {str(e)}")
    else:
        logger.warning("⚠️ No search key provided")
        
    # Test with admin key
    if ADMIN_KEY:
        try:
            client = meilisearch.Client(url, ADMIN_KEY)
            indexes = client.get_indexes()
            index_count = len(indexes.get('results', [])) if isinstance(indexes, dict) else 0
            logger.info(f"✅ Admin key is valid for {name}")
            logger.info(f"Found {index_count} indexes with admin key")
        except Exception as e:
            logger.error(f"❌ Admin key validation failed for {name}: {str(e)}")
    else:
        logger.warning("⚠️ No admin key provided")
    
    return True

if __name__ == "__main__":
    logger.info("=== MeiliSearch Cloud Connection Test ===")
    logger.info("Testing with these keys:")
    logger.info(f"Master key: {'Provided (' + MASTER_KEY[:5] + '...' + MASTER_KEY[-5:] + ')' if MASTER_KEY else 'Not provided'}")
    logger.info(f"Search key: {'Provided (' + SEARCH_KEY[:5] + '...' + SEARCH_KEY[-5:] + ')' if SEARCH_KEY else 'Not provided'}")
    logger.info(f"Admin key: {'Provided (' + ADMIN_KEY[:5] + '...' + ADMIN_KEY[-5:] + ')' if ADMIN_KEY else 'Not provided'}")
    
    # Test local instance
    local_success = test_instance(LOCAL_URL, "Local")
    
    # Test cloud instance
    cloud_success = test_instance(CLOUD_URL, "Cloud")
    
    # Summary
    logger.info("\n=== Connection Test Summary ===")
    logger.info(f"Local instance: {'Available' if local_success else 'Not available'}")
    logger.info(f"Cloud instance: {'Available' if cloud_success else 'Not available'}")
    
    if local_success and cloud_success:
        logger.info("\n✅ Both instances are available with the current keys!")
    elif local_success and not cloud_success:
        logger.info("\n⚠️ Only local instance is working with the current keys.")
        logger.info("You will need different keys for the cloud instance.")
    elif not local_success and cloud_success:
        logger.info("\n⚠️ Only cloud instance is working with the current keys.")
    else:
        logger.info("\n❌ Neither instance is working with the current keys.") 