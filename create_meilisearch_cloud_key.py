import os
import json
import requests
import dotenv
from datetime import datetime, timedelta

# Load environment variables
dotenv.load_dotenv()
MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY")
HOST = os.getenv("MEILISEARCH_HOST", "https://edge.meilisearch.com")

def create_search_key():
    """Create a search key with the right permissions."""
    print("\n===== Creating New Search Key =====")
    
    # Define the expiration date (30 days from now)
    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
    
    # Define the key attributes
    key_data = {
        "name": "CryptoV7 Search Key",
        "description": "Search-only key for the CryptoV7 application",
        "actions": ["search", "documents.get", "indexes.get"],
        "indexes": ["*"],  # Access to all indexes
        "expiresAt": expires_at
    }
    
    headers = {
        "Authorization": f"Bearer {MASTER_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{HOST}/keys",
            headers=headers,
            json=key_data
        )
        
        if response.status_code == 201:  # 201 Created
            key = response.json()
            print("✅ Successfully created new search key")
            print(f"Key: {key['key']}")
            print(f"Key UID: {key['uid']}")
            print(f"Expires At: {key['expiresAt']}")
            return key
        else:
            print(f"❌ Failed to create key: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating key: {str(e)}")
        return None

def update_env_file(key):
    """Update .env files with the new key."""
    print("\n===== Updating .env Files =====")
    
    # Update both .env files
    env_files = [".env", "api/.env"]
    
    for env_file in env_files:
        if not os.path.exists(env_file):
            print(f"❌ {env_file} does not exist, skipping")
            continue
        
        try:
            # Read current .env content
            with open(env_file, 'r') as file:
                lines = file.readlines()
            
            # Update MEILISEARCH_SEARCH_KEY
            updated_lines = []
            key_updated = False
            
            for line in lines:
                if line.startswith('MEILISEARCH_SEARCH_KEY='):
                    updated_lines.append(f'MEILISEARCH_SEARCH_KEY={key["key"]}\n')
                    key_updated = True
                else:
                    updated_lines.append(line)
            
            # Add the key if it wasn't found
            if not key_updated:
                updated_lines.append(f'MEILISEARCH_SEARCH_KEY={key["key"]}\n')
            
            # Write back to .env
            with open(env_file, 'w') as file:
                file.writelines(updated_lines)
            
            print(f"✅ Updated {env_file} with new search key")
        except Exception as e:
            print(f"❌ Error updating {env_file}: {str(e)}")

def verify_search_key(key):
    """Verify the new search key works."""
    print("\n===== Verifying New Search Key =====")
    
    headers = {"Authorization": f"Bearer {key['key']}"}
    
    try:
        # Try listing indexes (should be allowed with search key)
        response = requests.get(f"{HOST}/indexes", headers=headers)
        
        if response.status_code == 200:
            indexes = response.json()["results"]
            print("✅ Key successfully verified (can access indexes)")
            print(f"Found {len(indexes)} indexes")
            return True
        else:
            print(f"❌ Key verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error verifying key: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("MEILISEARCH CLOUD SEARCH KEY SETUP")
    print("=" * 60)
    print(f"Using MeiliSearch at: {HOST}")
    
    # Create new search key
    new_key = create_search_key()
    if not new_key:
        print("Failed to create search key. Exiting.")
        return
    
    # Verify the key works
    if verify_search_key(new_key):
        # Update .env files
        update_env_file(new_key)
        
        print("\n" + "=" * 60)
        print("SUCCESS! KEY SETUP COMPLETE")
        print("=" * 60)
        print("Your MeiliSearch cloud instance is now configured with a valid search key.")
        print("Next steps:")
        print("1. Restart your API server")
        print("2. Test the search functionality")
    else:
        print("\n❌ The created key did not work as expected.")
        print("Please check the MeiliSearch documentation for more information.")

if __name__ == "__main__":
    main() 