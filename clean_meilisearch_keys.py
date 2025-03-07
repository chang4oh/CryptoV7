import os
import requests
import dotenv
from pathlib import Path

# Load environment variables
dotenv.load_dotenv()
MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY")
HOST = os.getenv("MEILISEARCH_HOST", "http://localhost:7700")

# API endpoints
KEYS_ENDPOINT = f"{HOST}/keys"
INDEXES_ENDPOINT = f"{HOST}/indexes"

def check_meilisearch_health():
    """Check if MeiliSearch is running."""
    try:
        response = requests.get(f"{HOST}/health")
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException:
        return False

def list_all_keys():
    """List all existing MeiliSearch API keys."""
    headers = {"Authorization": f"Bearer {MASTER_KEY}"}
    response = requests.get(KEYS_ENDPOINT, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching keys: {response.status_code} - {response.text}")
        return None
        
    return response.json()["results"]

def delete_key(uid):
    """Delete a MeiliSearch API key by its UID."""
    headers = {"Authorization": f"Bearer {MASTER_KEY}"}
    response = requests.delete(f"{KEYS_ENDPOINT}/{uid}", headers=headers)
    
    if response.status_code == 204:
        return True
    
    print(f"Error deleting key {uid}: {response.status_code} - {response.text}")
    return False

def verify_search_key(key):
    """Verify that a search key works correctly."""
    headers = {"Authorization": f"Bearer {key}"}
    
    # Try to access indexes (should be allowed with search key)
    try:
        response = requests.get(INDEXES_ENDPOINT, headers=headers)
        if response.status_code == 200:
            print("✅ Key successfully verified (can access indexes)")
            return True
        else:
            print(f"❌ Key verification failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Key verification failed: {str(e)}")
        return False

def update_env_file(key):
    """Update .env file with the search key."""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    # Read current .env content
    with open(env_path, 'r') as file:
        lines = file.readlines()
    
    # Update or add MEILISEARCH_SEARCH_KEY
    key_found = False
    new_lines = []
    
    for line in lines:
        if line.startswith('MEILISEARCH_SEARCH_KEY='):
            new_lines.append(f'MEILISEARCH_SEARCH_KEY={key}\n')
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        new_lines.append(f'MEILISEARCH_SEARCH_KEY={key}\n')
    
    # Write back to .env
    with open(env_path, 'w') as file:
        file.writelines(new_lines)
    
    print(f"✅ Updated .env file with search key")
    return True

def main():
    print("="*60)
    print("MEILISEARCH KEY CLEANUP & VERIFICATION")
    print("="*60)
    print("")
    
    # Check if MeiliSearch is running
    if not check_meilisearch_health():
        print("❌ MeiliSearch is not running. Please start it first.")
        return
    
    print("✅ MeiliSearch is running")
    print("")
    
    # List all keys
    print("Finding all MeiliSearch API Keys...")
    keys = list_all_keys()
    if not keys:
        print("No keys found or error occurred.")
        return
    
    # Find our primary key (CryptoV7 Search Key)
    primary_key = None
    default_keys = []
    keys_to_delete = []
    
    for key in keys:
        if key.get("name") == "CryptoV7 Search Key":
            primary_key = key
        elif key.get("name") in ["Default Search API Key", "Default Admin API Key"]:
            default_keys.append(key)
        else:
            keys_to_delete.append(key)
    
    if not primary_key:
        print("❌ CryptoV7 Search Key not found")
        return
    
    # Display keys to delete
    print(f"Found {len(keys_to_delete)} redundant keys to delete:")
    for i, key in enumerate(keys_to_delete, 1):
        print(f"  {i}. UID: {key['uid']}, Description: {key.get('description', 'None')}")
    
    print("")
    confirm = input("Proceed with deleting these keys? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Delete redundant keys
    print("\nDeleting redundant keys...")
    deleted_count = 0
    for key in keys_to_delete:
        if delete_key(key['uid']):
            deleted_count += 1
            print(f"✅ Deleted key: {key['uid']}")
    
    print(f"\n✅ Successfully deleted {deleted_count} out of {len(keys_to_delete)} keys")
    
    # Verify primary key
    print("\nVerifying CryptoV7 Search Key...")
    if verify_search_key(primary_key['key']):
        # Update .env file
        update_env_file(primary_key['key'])
        
        print("\n"+"="*60)
        print("SUMMARY")
        print("="*60)
        print(f"✅ Verified CryptoV7 Search Key (UID: {primary_key['uid']})")
        print(f"✅ This key has been set in your .env file")
        print(f"✅ Deleted {deleted_count} redundant keys")
        print(f"✅ Kept {len(default_keys)} default MeiliSearch keys")
        print("\n🔍 Next steps:")
        print("  1. Restart your FastAPI application")
        print("  2. Test your search endpoints")
        print("="*60)
    else:
        print("❌ Primary key verification failed. Please check your MeiliSearch setup.")

if __name__ == "__main__":
    main() 