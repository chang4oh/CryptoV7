import requests
import os
from dotenv import load_dotenv
import json
import uuid

# Load environment variables
load_dotenv()

MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "1582d75025acd6f3b8f5445265deb499ee2e843c")

def create_search_key():
    """Create a proper search API key for MeiliSearch."""
    print(f"\n===== Creating MeiliSearch Search API Key =====")
    print(f"MeiliSearch URL: {MEILISEARCH_URL}")
    print(f"Using Master Key: {MASTER_KEY[:8]}... (masked)")
    
    # First check if MeiliSearch is running
    try:
        health_response = requests.get(f"{MEILISEARCH_URL}/health")
        if health_response.status_code != 200:
            print(f"❌ MeiliSearch health check failed with status code: {health_response.status_code}")
            print(f"Response: {health_response.text}")
            return False
            
        print(f"✅ MeiliSearch is running and healthy")
    except Exception as e:
        print(f"❌ Error connecting to MeiliSearch: {e}")
        print("Make sure MeiliSearch is running at the configured URL")
        return False
    
    # Now create a search key
    try:
        # Define the key properties following the MeiliSearch documentation
        key_data = {
            "name": "CryptoV7 Search Key",
            "description": "Search-only key for the CryptoV7 application",
            "actions": ["search", "documents.get", "indexes.get"],
            "indexes": ["*"],  # Allow access to all indexes
            "expiresAt": None  # Key won't expire
        }
        
        # Send the request to create the key
        headers = {
            "Authorization": f"Bearer {MASTER_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{MEILISEARCH_URL}/keys",
            headers=headers,
            json=key_data
        )
        
        if response.status_code == 201:
            key_info = response.json()
            print(f"✅ Search key created successfully!")
            print(f"Key: {key_info['key']}")
            print(f"UID: {key_info['uid']}")
            
            # Save the key to .env file
            update_env_file(key_info['key'])
            
            return key_info
        else:
            print(f"❌ Failed to create key. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating search key: {e}")
        return False

def list_all_keys():
    """List all existing MeiliSearch API keys."""
    print(f"\n===== Listing All MeiliSearch API Keys =====")
    
    try:
        headers = {
            "Authorization": f"Bearer {MASTER_KEY}"
        }
        
        response = requests.get(
            f"{MEILISEARCH_URL}/keys",
            headers=headers
        )
        
        if response.status_code == 200:
            keys_info = response.json()
            print(f"Found {keys_info.get('total', 0)} keys:")
            
            for i, key in enumerate(keys_info.get('results', [])):
                print(f"\nKey #{i+1}:")
                print(f"  Name: {key.get('name')}")
                print(f"  Description: {key.get('description')}")
                print(f"  Key: {key.get('key')[:8]}... (masked)")
                print(f"  UID: {key.get('uid')}")
                print(f"  Actions: {', '.join(key.get('actions', []))}")
                print(f"  Indexes: {', '.join(key.get('indexes', []))}")
                print(f"  Expires At: {key.get('expiresAt', 'Never')}")
            
            return keys_info
        else:
            print(f"❌ Failed to list keys. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error listing keys: {e}")
        return False

def verify_search_key(key):
    """Verify that a search key works correctly."""
    print(f"\n===== Verifying Search Key =====")
    print(f"Testing key: {key[:8]}... (masked)")
    
    try:
        # Try to use the key to get indexes (a basic read operation)
        headers = {
            "Authorization": f"Bearer {key}"
        }
        
        response = requests.get(
            f"{MEILISEARCH_URL}/indexes",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Search key is valid and working correctly")
            return True
        else:
            print(f"❌ Search key verification failed. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error verifying search key: {e}")
        return False

def update_env_file(new_key):
    """Update the .env file with the new search key."""
    try:
        env_path = '.env'
        if not os.path.exists(env_path):
            print(f"❌ .env file not found at {env_path}")
            return False
            
        # Read the current .env file
        with open(env_path, 'r') as file:
            lines = file.readlines()
            
        # Check if MEILISEARCH_SEARCH_KEY already exists
        key_exists = False
        for i, line in enumerate(lines):
            if line.startswith('MEILISEARCH_SEARCH_KEY='):
                # Update the existing key
                lines[i] = f'MEILISEARCH_SEARCH_KEY={new_key}\n'
                key_exists = True
                break
                
        # If key doesn't exist, add it
        if not key_exists:
            lines.append(f'MEILISEARCH_SEARCH_KEY={new_key}\n')
            
        # Write the updated content back to .env
        with open(env_path, 'w') as file:
            file.writelines(lines)
            
        print(f"✅ Updated .env file with new search key")
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Run the main script to create and verify a MeiliSearch search key."""
    print("=" * 60)
    print("MEILISEARCH API KEY MANAGEMENT")
    print("=" * 60)
    
    # List existing keys
    existing_keys = list_all_keys()
    
    # Ask if the user wants to create a new key
    print("\nDo you want to create a new search key? (y/n)")
    choice = input().strip().lower()
    
    if choice == 'y':
        new_key = create_search_key()
        if new_key:
            verify_search_key(new_key['key'])
    else:
        # If not creating a new key, try to use the existing one from .env
        existing_key = os.getenv("MEILISEARCH_SEARCH_KEY")
        if existing_key:
            print(f"\nUsing existing key from .env: {existing_key[:8]}... (masked)")
            verify_search_key(existing_key)
        else:
            print("❌ No existing search key found in .env")
    
    print("\n" + "=" * 60)
    print("Management complete!")
    print("=" * 60)
    print("\nRemember to restart your application after updating the keys.")

if __name__ == "__main__":
    main() 