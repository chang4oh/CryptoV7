import os
import requests
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Get MeiliSearch settings
MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY")
SEARCH_KEY = os.getenv("MEILISEARCH_SEARCH_KEY")
HOST = os.getenv("MEILISEARCH_HOST")

print("="*60)
print("MEILISEARCH CLOUD CONNECTIVITY TEST")
print("="*60)
print(f"MeiliSearch Host: {HOST}")
print(f"Master Key: {MASTER_KEY[:8]}..." if MASTER_KEY else "Not set")
print(f"Search Key: {SEARCH_KEY[:8]}..." if SEARCH_KEY else "Not set")
print("="*60)

# Test 1: Check health
print("\nTest 1: Checking MeiliSearch health...")
try:
    response = requests.get(f"{HOST}/health")
    print(f"Health Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ MeiliSearch is healthy")
        print(f"Server response: {response.json()}")
    else:
        print(f"❌ Unexpected response: {response.text}")
except Exception as e:
    print(f"❌ Error connecting: {str(e)}")

# Test 2: Check authentication with master key
print("\nTest 2: Testing master key authentication...")
try:
    headers = {"Authorization": f"Bearer {MASTER_KEY}"}
    response = requests.get(f"{HOST}/keys", headers=headers)
    
    if response.status_code == 200:
        keys = response.json()["results"]
        print("✅ Master key authentication successful")
        print(f"Found {len(keys)} API keys")
    else:
        print(f"❌ Master key authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 3: Check authentication with search key
print("\nTest 3: Testing search key authentication...")
try:
    headers = {"Authorization": f"Bearer {SEARCH_KEY}"}
    response = requests.get(f"{HOST}/indexes", headers=headers)
    
    if response.status_code == 200:
        indexes = response.json()["results"]
        print("✅ Search key authentication successful")
        print(f"Found {len(indexes)} indexes")
        
        # Print each index
        for idx in indexes:
            print(f"  - Index: {idx['uid']}, Primary Key: {idx.get('primaryKey', 'None')}")
            print(f"    Documents: {idx.get('stats', {}).get('numberOfDocuments', 0)}")
    else:
        print(f"❌ Search key authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\nTest complete! Now you can restart your API server with the correct cloud configuration.") 