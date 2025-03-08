import requests
import json
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

API_BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test the API health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}")
        print(f"Health check - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing health: {e}")
        return False

def test_sync_endpoint():
    """Test the MeiliSearch sync endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/sync")
        print(f"Sync endpoint - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing sync endpoint: {e}")
        return False

def test_search_trades():
    """Test the search trades endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/search/trades?q=btc")
        print(f"Search trades - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing search trades: {e}")
        return False

def test_search_news():
    """Test the search news endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/search/news?q=crypto")
        print(f"Search news - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing search news: {e}")
        return False

def test_meilisearch_health():
    """Test the MeiliSearch health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/health/meilisearch")
        print(f"MeiliSearch health - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing MeiliSearch health: {e}")
        return False

def test_market_price():
    """Test the market price endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/market/price/BTCUSDT")
        print(f"Market price - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing market price: {e}")
        return False

def test_market_prices():
    """Test the multiple market prices endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/market/prices?symbols=BTCUSDT,ETHUSDT,SOLUSDT")
        print(f"Multiple market prices - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing multiple market prices: {e}")
        return False

def test_crypto_list():
    """Test the crypto list endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/market/crypto-list")
        print(f"Crypto list - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('count', 0)} cryptocurrencies with quote asset {data.get('quote_asset', 'USDT')}")
            
            # Print first 3 cryptocurrencies as a sample
            cryptos = data.get('cryptocurrencies', [])
            if cryptos:
                print("\nSample cryptocurrencies:")
                for i, crypto in enumerate(cryptos[:3]):
                    print(f"{i+1}. {crypto.get('baseAsset')} ({crypto.get('symbol')}): {crypto.get('price')}")
            
            return True
        else:
            print(f"Response: {response.json()}")
            return False
    except Exception as e:
        print(f"Error testing crypto list: {e}")
        return False

def test_market_exchange_info():
    """Test the market exchange info endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/market/exchange-info")
        print(f"Market exchange info - Status: {response.status_code}")
        # Print only a sample to avoid too much output
        data = response.json()
        if "symbols" in data:
            print(f"Found {len(data['symbols'])} symbols")
            print(f"Sample symbol: {json.dumps(data['symbols'][0], indent=2)}")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing market exchange info: {e}")
        return False

def test_crypto_news():
    """Test the crypto news endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/news/crypto?page_size=3")
        print(f"Crypto news - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "articles" in data:
                print(f"Found {len(data['articles'])} articles")
                if len(data['articles']) > 0:
                    print(f"First article: {data['articles'][0]['title']}")
                    if "sentiment" in data['articles'][0]:
                        print(f"Sentiment: {data['articles'][0]['sentiment']}")
            else:
                print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing crypto news: {e}")
        return False

def test_all_apis_health():
    """Test the all APIs health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/health/all")
        print(f"All APIs health - Status: {response.status_code}")
        
        # Print only a summary to avoid too much output
        if response.status_code == 200:
            data = response.json()
            print(f"Overall status: {data.get('overall_status', 'unknown')}")
            
            # Print status of each API
            for api, result in data.items():
                if api != 'overall_status':
                    status = result.get('status', 'unknown')
                    print(f"- {api}: {status}")
            
            # Show a sample of data from one API for verification
            if 'binance_api' in data and data['binance_api'].get('status') == 'connected':
                print(f"\nSample data - BTC price: {data['binance_api'].get('btc_price', 'N/A')}")
        else:
            print(f"Response: {response.json()}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing all APIs health: {e}")
        return False

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def check_api_health():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is not running or not reachable")
        return False

def check_mongodb_status():
    """Check MongoDB connection status."""
    try:
        response = requests.get(f"{API_BASE_URL}/mongodb/status")
        if response.status_code == 200:
            data = response.json()
            print("MongoDB Status:")
            print_json(data)
            return data
        else:
            print(f"❌ MongoDB status check failed with status code {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ API is not running or not reachable")
        return None

def create_sample_data():
    """Create sample data in MongoDB."""
    print("\nCreating sample data...")
    endpoints = [
        "/mongodb/market-data/sample",
        "/mongodb/trade-signals/sample",
        "/mongodb/whale-transactions/sample"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(f"{API_BASE_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                name = endpoint.split("/")[-1]
                print(f"✅ Created sample {name}")
                print_json(data)
            else:
                print(f"❌ Failed to create {endpoint} with status code {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ API is not running or not reachable")

def sync_to_meilisearch():
    """Sync data to MeiliSearch."""
    print("\nSyncing data to MeiliSearch...")
    try:
        response = requests.post(f"{API_BASE_URL}/sync/all")
        if response.status_code == 200:
            data = response.json()
            print("✅ Sync started")
            print_json(data)
        else:
            print(f"❌ Sync failed with status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API is not running or not reachable")

def main():
    """Run tests for the API."""
    print("Testing CryptoV7 API...\n")
    
    # Check if the API is running
    if not check_api_health():
        print("\nPlease make sure the API is running with:")
        print("cd api && uvicorn main:app --reload")
        return
    
    # Check MongoDB status
    mongodb_status = check_mongodb_status()
    
    if mongodb_status and mongodb_status.get("status") == "connected":
        # Create sample data
        create_sample_data()
        
        # Sync to MeiliSearch
        sync_to_meilisearch()
    else:
        print("\nMongoDB is not connected. Please check your configuration.")
        print("1. Verify your MongoDB Atlas credentials in .env file")
        print("2. Make sure you have network access to MongoDB Atlas")
        print("3. Check that the database name is correct")

if __name__ == "__main__":
    main() 