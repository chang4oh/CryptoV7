import requests
import json
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

API_BASE_URL = "http://localhost:8000"

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
        response = requests.get(f"{API_BASE_URL}/api/sync")
        print(f"Sync endpoint - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing sync endpoint: {e}")
        return False

def test_search_trades():
    """Test the search trades endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/search/trades?q=btc")
        print(f"Search trades - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing search trades: {e}")
        return False

def test_search_news():
    """Test the search news endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/search/news?q=crypto")
        print(f"Search news - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing search news: {e}")
        return False

def test_meilisearch_health():
    """Test the MeiliSearch health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health/meilisearch")
        print(f"MeiliSearch health - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing MeiliSearch health: {e}")
        return False

def test_market_price():
    """Test the market price endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/market/price/BTCUSDT")
        print(f"Market price - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing market price: {e}")
        return False

def test_market_prices():
    """Test the multiple market prices endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/market/prices?symbols=BTCUSDT,ETHUSDT,SOLUSDT")
        print(f"Multiple market prices - Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing multiple market prices: {e}")
        return False

def test_crypto_list():
    """Test the crypto list endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/market/crypto-list")
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
        response = requests.get(f"{API_BASE_URL}/api/market/exchange-info")
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
        response = requests.get(f"{API_BASE_URL}/api/news/crypto?page_size=3")
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
        response = requests.get(f"{API_BASE_URL}/api/health/all")
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

def run_tests():
    """Run all API tests."""
    print("=" * 50)
    print("TESTING API ENDPOINTS")
    print("=" * 50)
    
    tests = [
        ("Health check", test_health),
        ("Sync endpoint", test_sync_endpoint),
        ("Search trades", test_search_trades),
        ("Search news", test_search_news),
        ("MeiliSearch health", test_meilisearch_health),
        ("Market price", test_market_price),
        ("Multiple market prices", test_market_prices),
        ("Crypto list", test_crypto_list),
        ("Market exchange info", test_market_exchange_info),
        ("Crypto news", test_crypto_news),
        ("All APIs health", test_all_apis_health)
    ]
    
    success_count = 0
    for name, test_func in tests:
        print("\n" + "-" * 30)
        print(f"Testing: {name}")
        print("-" * 30)
        if test_func():
            print(f"✅ {name} - SUCCESS")
            success_count += 1
        else:
            print(f"❌ {name} - FAILED")
        
        # Add a short delay between tests
        time.sleep(0.5)
    
    print("\n" + "=" * 50)
    print(f"Test Summary: {success_count}/{len(tests)} tests passed")
    print("=" * 50)

if __name__ == "__main__":
    run_tests() 