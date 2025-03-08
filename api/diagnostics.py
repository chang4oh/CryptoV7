import asyncio
import logging
import os
import sys
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import meilisearch
import requests
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("diagnostics")

# Load environment variables
load_dotenv()

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "cryptov7")
MEILISEARCH_HOST = os.getenv("MEILISEARCH_HOST", "http://localhost:7700")
MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")
MEILISEARCH_SEARCH_KEY = os.getenv("MEILISEARCH_SEARCH_KEY", "")

async def check_mongodb():
    """Check MongoDB connection and database."""
    print("\n=== MongoDB Diagnostics ===")
    
    try:
        print(f"Connecting to MongoDB at {MONGODB_URI}...")
        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB server")
        
        # Check if database exists
        db = client[MONGODB_DB_NAME]
        db_list = await client.list_database_names()
        if MONGODB_DB_NAME in db_list:
            print(f"✅ Database '{MONGODB_DB_NAME}' exists")
        else:
            print(f"⚠️ Database '{MONGODB_DB_NAME}' does not exist yet (will be created on first use)")
        
        # Test collection creation
        collection = db.test_collection
        await collection.insert_one({"test": "document", "timestamp": "diagnostic_test"})
        print("✅ Successfully inserted test document")
        
        # Clean up the test document
        await collection.delete_one({"test": "document"})
        print("✅ Successfully cleaned up test document")
        
        # Check available collections
        collections = await db.list_collection_names()
        if collections:
            print(f"Collections in {MONGODB_DB_NAME}: {', '.join(collections)}")
        else:
            print(f"No collections in {MONGODB_DB_NAME} database yet")
        
        # Close connection
        client.close()
        print("MongoDB connection test completed successfully")
        return True
        
    except ConnectionFailure as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        print("Please check if MongoDB is running and accessible")
        return False
    except ServerSelectionTimeoutError as e:
        print(f"❌ Server selection timeout: {e}")
        print("MongoDB server is not responding within timeout period")
        return False
    except Exception as e:
        print(f"❌ Unexpected MongoDB error: {e}")
        return False

def check_meilisearch():
    """Check MeiliSearch connection and indexes."""
    print("\n=== MeiliSearch Diagnostics ===")
    
    try:
        print(f"Connecting to MeiliSearch at {MEILISEARCH_HOST}...")
        client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_MASTER_KEY)
        
        # Test connection
        health = client.health()
        print(f"✅ MeiliSearch health status: {health['status']}")
        
        # Get version information
        stats = client.get_stats()
        print(f"MeiliSearch version: {stats.get('version', 'Unknown')}")
        
        # List indexes
        indexes = client.get_indexes()
        if indexes['results']:
            print(f"Found {len(indexes['results'])} indexes:")
            for index in indexes['results']:
                print(f"  - {index['uid']}: {index['stats']['numberOfDocuments']} documents")
        else:
            print("No indexes found")
        
        # Test search key if available
        if MEILISEARCH_SEARCH_KEY:
            print("Testing search key...")
            search_client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_SEARCH_KEY)
            try:
                # Try to access indexes with search key
                search_client.get_indexes()
                print("✅ Search key working correctly")
            except Exception as e:
                print(f"❌ Search key not working: {e}")
        else:
            print("⚠️ No search key defined in environment variables")
        
        # Verify master key capabilities
        try:
            keys = client.get_keys()
            print("✅ Master key has sufficient permissions")
        except Exception as e:
            print(f"❌ Master key permissions issue: {e}")
        
        print("MeiliSearch connection test completed successfully")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to MeiliSearch server")
        print("Please check if MeiliSearch is running and accessible")
        return False
    except Exception as e:
        print(f"❌ Unexpected MeiliSearch error: {e}")
        return False

def print_diagnostics_summary(mongodb_ok, meilisearch_ok):
    """Print a summary of the diagnostics."""
    print("\n=== Diagnostics Summary ===")
    print(f"MongoDB: {'✅ CONNECTED' if mongodb_ok else '❌ NOT CONNECTED'}")
    print(f"MeiliSearch: {'✅ CONNECTED' if meilisearch_ok else '❌ NOT CONNECTED'}")
    
    if not mongodb_ok:
        print("\nMongoDB Troubleshooting:")
        print("1. Ensure MongoDB is installed and running")
        print("2. Check if MongoDB is running on a different port")
        print("3. Verify there are no authentication requirements")
        print("4. Check if MongoDB is running in a Docker container")
        print("5. Verify network settings if using a remote MongoDB")
    
    if not meilisearch_ok:
        print("\nMeiliSearch Troubleshooting:")
        print("1. Ensure MeiliSearch is installed and running")
        print("2. Verify the host URL is correct (default: http://localhost:7700)")
        print("3. Check if the master key is required/correct")
        print("4. Try running MeiliSearch with: ./meilisearch --master-key=masterKey")
        print("5. Check firewall settings if using a remote instance")

    if not mongodb_ok or not meilisearch_ok:
        print("\nEnvironment Variables:")
        print(f"MONGODB_URI: {MONGODB_URI}")
        print(f"MONGODB_DB_NAME: {MONGODB_DB_NAME}")
        print(f"MEILISEARCH_HOST: {MEILISEARCH_HOST}")
        print(f"MEILISEARCH_MASTER_KEY: {'Defined' if MEILISEARCH_MASTER_KEY else 'Not defined'}")
        print(f"MEILISEARCH_SEARCH_KEY: {'Defined' if MEILISEARCH_SEARCH_KEY else 'Not defined'}")

async def main():
    """Run all diagnostics."""
    print("=== CryptoV7 System Diagnostics ===")
    print("Running diagnostics to check system components...\n")
    
    # Check MongoDB
    mongodb_ok = await check_mongodb()
    
    # Check MeiliSearch
    meilisearch_ok = check_meilisearch()
    
    # Print summary
    print_diagnostics_summary(mongodb_ok, meilisearch_ok)

if __name__ == "__main__":
    asyncio.run(main()) 