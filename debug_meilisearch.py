import meilisearch
import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "1582d75025acd6f3b8f5445265deb499ee2e843c")
SEARCH_KEY = os.getenv("MEILISEARCH_SEARCH_KEY", "e260b7f247952f2b4a3bf78d326f830d04bdeffb38cc621825224c95da599d4e")

def test_meilisearch_connection():
    """Test basic connection to MeiliSearch server."""
    print(f"\n===== Testing Basic MeiliSearch Connection =====")
    print(f"URL: {MEILISEARCH_URL}")
    
    try:
        # Try a simple HTTP request first
        print("Testing with direct HTTP request...")
        response = requests.get(f"{MEILISEARCH_URL}/health")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print("✅ HTTP connection successful")
        else:
            print(f"Response: {response.text}")
            print("❌ HTTP connection failed")
            return False
    except Exception as e:
        print(f"❌ HTTP request error: {e}")
        print("Make sure MeiliSearch is running and accessible at the configured URL")
        return False
    
    # Now try with the Python client and master key
    try:
        print("\nTesting with MeiliSearch Python client (Master Key)...")
        client = meilisearch.Client(MEILISEARCH_URL, MASTER_KEY)
        health = client.health()
        print(f"Health: {health}")
        print("✅ Client connection with master key successful")
    except Exception as e:
        print(f"❌ Client error with master key: {e}")
        print("The master key might be incorrect or the server might be rejecting it")
        return False
    
    # Test with search key
    try:
        print("\nTesting with MeiliSearch Python client (Search Key)...")
        client = meilisearch.Client(MEILISEARCH_URL, SEARCH_KEY)
        # Try a simple operation that doesn't require admin privileges
        stats = client.get_indexes()
        print(f"Got response from get_indexes")
        print("✅ Client connection with search key successful")
    except Exception as e:
        print(f"❌ Client error with search key: {e}")
        print("The search key might be invalid or not registered with MeiliSearch")
        return False
    
    return True

def test_indexes():
    """Test the indexes in MeiliSearch."""
    print(f"\n===== Testing MeiliSearch Indexes =====")
    
    try:
        # Connect with master key for full access
        client = meilisearch.Client(MEILISEARCH_URL, MASTER_KEY)
        
        # Get list of indexes
        indexes = client.get_indexes()
        
        if isinstance(indexes, list):
            if not indexes:
                print("No indexes found. You need to create indexes first.")
                print("Would you like to create sample indexes? (y/n)")
                if input().lower() == 'y':
                    create_sample_indexes(client)
                return False
            
            print(f"Found {len(indexes)} indexes:")
            for idx, index in enumerate(indexes):
                if hasattr(index, 'uid'):
                    print(f"{idx+1}. {index.uid} (Primary key: {index.primary_key})")
        else:
            print(f"Unexpected response format from get_indexes: {type(indexes)}")
            return False
    except Exception as e:
        print(f"❌ Error testing indexes: {e}")
        return False
    
    return True

def create_sample_indexes(client):
    """Create sample indexes for testing."""
    print(f"\n===== Creating Sample Indexes =====")
    
    try:
        # Create trades index
        trades_index = client.index('trades_index')
        # Update settings
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
        
        # Add sample documents
        sample_trades = [
            {
                "id": "trade_1",
                "symbol": "BTCUSDT",
                "side": "buy",
                "price": 45000.0,
                "quantity": 0.1,
                "timestamp": "2025-03-01T12:00:00Z",
                "pnl": 0.0,
                "strategy": "dca"
            },
            {
                "id": "trade_2",
                "symbol": "ETHUSDT",
                "side": "sell",
                "price": 3000.0,
                "quantity": 1.0,
                "timestamp": "2025-03-02T14:30:00Z",
                "pnl": 150.0,
                "strategy": "trend_following"
            }
        ]
        trades_index.add_documents(sample_trades)
        print("✅ Created trades_index with sample data")
        
        # Create news index
        news_index = client.index('news_index')
        # Update settings
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
        
        # Add sample documents
        sample_news = [
            {
                "id": "news_1",
                "title": "Bitcoin Price Surges Above $50,000",
                "content": "Bitcoin has surged above $50,000 for the first time in months, signaling renewed interest in cryptocurrencies.",
                "source": "CryptoNews",
                "publication_date": "2025-03-01T10:15:00Z",
                "sentiment_score": 0.8
            },
            {
                "id": "news_2",
                "title": "Ethereum Upgrade Scheduled for Next Month",
                "content": "The Ethereum network is preparing for a major upgrade that will improve scalability and reduce gas fees.",
                "source": "BlockchainTimes",
                "publication_date": "2025-03-02T09:30:00Z",
                "sentiment_score": 0.6
            }
        ]
        news_index.add_documents(sample_news)
        print("✅ Created news_index with sample data")
        
        return True
    except Exception as e:
        print(f"❌ Error creating sample indexes: {e}")
        return False

def test_search():
    """Test search functionality."""
    print(f"\n===== Testing Search Functionality =====")
    
    try:
        # Test with search key which should have enough permissions
        client = meilisearch.Client(MEILISEARCH_URL, SEARCH_KEY)
        
        # Get available indexes
        indexes = client.get_indexes()
        
        if not indexes:
            print("No indexes found to search")
            return False
        
        # Try to search in the first available index
        index = None
        for idx in indexes:
            if hasattr(idx, 'uid'):
                index = client.index(idx.uid)
                break
        
        if index is None:
            print("Could not find a valid index to search")
            return False
        
        print(f"Testing search in index: {index.uid}")
        
        # Try an empty search first (should return all documents)
        try:
            empty_results = index.search("")
            doc_count = len(empty_results.get('hits', []))
            print(f"Empty search returned {doc_count} documents")
            print("✅ Empty search successful")
        except Exception as e:
            print(f"❌ Error on empty search: {e}")
            return False
        
        # Try a more specific search
        try:
            if index.uid == 'trades_index':
                query = "btc"
            elif index.uid == 'news_index':
                query = "bitcoin"
            else:
                query = "test"
                
            print(f"Testing search with query: '{query}'")
            results = index.search(query)
            hit_count = len(results.get('hits', []))
            print(f"Search for '{query}' returned {hit_count} hits")
            if hit_count > 0:
                print("Sample hit:", json.dumps(results['hits'][0], indent=2))
            print("✅ Specific search successful")
        except Exception as e:
            print(f"❌ Error on specific search: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error during search test: {e}")
        return False

def test_api_search_endpoints():
    """Test the API search endpoints."""
    print(f"\n===== Testing API Search Endpoints =====")
    
    API_BASE_URL = "http://localhost:8000"
    
    # Test trades search endpoint
    try:
        print("Testing /api/search/trades endpoint...")
        response = requests.get(f"{API_BASE_URL}/api/search/trades?q=btc")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data.get('hits', []))} hits")
            print("✅ Trades search endpoint working")
        else:
            print(f"Response: {response.text}")
            print("❌ Trades search endpoint failed")
            return False
    except Exception as e:
        print(f"❌ Error testing trades search endpoint: {e}")
        return False
    
    # Test news search endpoint
    try:
        print("\nTesting /api/search/news endpoint...")
        response = requests.get(f"{API_BASE_URL}/api/search/news?q=crypto")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data.get('hits', []))} hits")
            print("✅ News search endpoint working")
        else:
            print(f"Response: {response.text}")
            print("❌ News search endpoint failed")
            return False
    except Exception as e:
        print(f"❌ Error testing news search endpoint: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("MEILISEARCH DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Test basic connection
    if not test_meilisearch_connection():
        print("\n❌ Basic connection test failed. Please fix connection issues before continuing.")
        return
    
    # Test indexes
    test_indexes()
    
    # Test search functionality
    test_search()
    
    # Test API endpoints
    print("\nWould you like to test the API search endpoints? (y/n)")
    print("Note: This requires your FastAPI application to be running")
    if input().lower() == 'y':
        test_api_search_endpoints()
    
    print("\n" + "=" * 60)
    print("Diagnostics complete!")
    print("=" * 60)

if __name__ == "__main__":
    main() 