import meilisearch
import os
import sys
from dotenv import load_dotenv
import json
import uuid

# Load environment variables
load_dotenv()

def main():
    """
    Register the search key with MeiliSearch.
    
    This script takes the search key from the .env file and registers it
    with MeiliSearch as a valid API key with proper permissions.
    """
    print("\n=== MeiliSearch Search Key Registration ===\n")
    
    # Get MeiliSearch connection details from environment variables
    meilisearch_url = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
    master_key = os.getenv("MEILISEARCH_MASTER_KEY")
    search_key = os.getenv("MEILISEARCH_SEARCH_KEY")
    
    # Check if both keys are present
    if not master_key:
        print("❌ ERROR: MEILISEARCH_MASTER_KEY not found in .env file")
        return
    
    if not search_key:
        print("❌ ERROR: MEILISEARCH_SEARCH_KEY not found in .env file")
        return
    
    print(f"✅ Found master key: {master_key[:8]}... (masked)")
    print(f"✅ Found search key: {search_key[:8]}... (masked)")
    
    # Connect to MeiliSearch with master key
    print(f"\nConnecting to MeiliSearch at {meilisearch_url} with master key...")
    client = meilisearch.Client(meilisearch_url, master_key)
    
    # Check that MeiliSearch is running
    try:
        health = client.health()
        print(f"✅ MeiliSearch health: {health}")
    except Exception as e:
        print(f"❌ Error connecting to MeiliSearch: {e}")
        print("   Make sure MeiliSearch is running and accessible")
        return
    
    # Define search permissions and create key
    try:
        # Define search-only permissions
        actions = ["search", "documents.get", "indexes.get", "stats.get"]
        indexes = ["*"]  # All indexes
        
        # First list existing keys
        print("\nChecking for existing keys...")
        try:
            keys = client.get_keys()
            
            if isinstance(keys, dict) and 'results' in keys:
                existing_keys = keys['results']
            else:
                existing_keys = keys
                
            # Check if our search key already exists
            key_found = False
            for key in existing_keys:
                if isinstance(key, dict) and key.get('key') == search_key:
                    key_found = True
                    print(f"✅ Search key is already registered in MeiliSearch")
                    print(f"   Key description: {key.get('description', 'No description')}")
                    print(f"   Key actions: {key.get('actions', [])}")
                    break
            
            if not key_found:
                print("Search key not found in MeiliSearch. Creating it now...")
                
                # Create a new key - MeiliSearch v1.13 doesn't accept 'key' parameter
                # Instead, we'll create a new key and update the .env file
                key_info = client.create_key({
                    "description": "Search-only key",
                    "actions": actions,
                    "indexes": indexes,
                    "expiresAt": None  # Never expires
                })
                
                new_key = key_info.get("key", "")
                if new_key:
                    print(f"✅ New search key created successfully: {new_key[:8]}... (masked)")
                    
                    # Update the .env file with the new key
                    try:
                        env_path = os.path.join(os.getcwd(), '.env')
                        
                        if os.path.exists(env_path):
                            with open(env_path, 'r') as file:
                                env_lines = file.readlines()
                            
                            # Update or add the search key
                            search_key_found = False
                            for i, line in enumerate(env_lines):
                                if line.startswith('MEILISEARCH_SEARCH_KEY='):
                                    env_lines[i] = f'MEILISEARCH_SEARCH_KEY={new_key}\n'
                                    search_key_found = True
                                    break
                            
                            if not search_key_found:
                                env_lines.append(f'\nMEILISEARCH_SEARCH_KEY={new_key}\n')
                            
                            with open(env_path, 'w') as file:
                                file.writelines(env_lines)
                                
                            print("✅ Search key updated in .env file")
                            print("   Please restart your application to use the new key")
                        else:
                            print("❌ .env file not found, couldn't save search key")
                    except Exception as e:
                        print(f"❌ Error updating .env file: {e}")
                else:
                    print("❌ No key returned from create operation")
                
        except Exception as e:
            # This might be a version issue with the MeiliSearch Python SDK
            print(f"⚠️ Could not list existing keys: {e}")
            print("Attempting to create a new key...")
            
            try:
                # Try to create a new key
                key_info = client.create_key({
                    "description": "Search-only key",
                    "actions": actions,
                    "indexes": indexes,
                    "expiresAt": None  # Never expires
                })
                
                new_key = key_info.get("key", "")
                if new_key:
                    print(f"✅ New search key created successfully: {new_key[:8]}... (masked)")
                    
                    # Update the .env file with the new key
                    try:
                        env_path = os.path.join(os.getcwd(), '.env')
                        
                        if os.path.exists(env_path):
                            with open(env_path, 'r') as file:
                                env_lines = file.readlines()
                            
                            # Update or add the search key
                            search_key_found = False
                            for i, line in enumerate(env_lines):
                                if line.startswith('MEILISEARCH_SEARCH_KEY='):
                                    env_lines[i] = f'MEILISEARCH_SEARCH_KEY={new_key}\n'
                                    search_key_found = True
                                    break
                            
                            if not search_key_found:
                                env_lines.append(f'\nMEILISEARCH_SEARCH_KEY={new_key}\n')
                            
                            with open(env_path, 'w') as file:
                                file.writelines(env_lines)
                                
                            print("✅ Search key updated in .env file")
                            print("   Please restart your application to use the new key")
                        else:
                            print("❌ .env file not found, couldn't save search key")
                    except Exception as e:
                        print(f"❌ Error updating .env file: {e}")
                else:
                    print("❌ No key returned from create operation")
            except Exception as inner_e:
                print(f"❌ Error creating key: {inner_e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test search access with the search key
    print("\nTesting search access with the search key...")
    try:
        # Use the updated search key if available
        current_search_key = os.getenv("MEILISEARCH_SEARCH_KEY")
        search_client = meilisearch.Client(meilisearch_url, current_search_key)
        
        # List indexes
        indexes = search_client.get_indexes()
        
        if isinstance(indexes, list):
            if indexes:
                print(f"✅ Found {len(indexes)} indexes")
                
                # Try a search on the first index
                first_index = indexes[0]
                if hasattr(first_index, 'uid'):
                    index_name = first_index.uid
                    index = search_client.index(index_name)
                    search_result = index.search("")
                    print(f"✅ Search test successful on index '{index_name}'")
                else:
                    print("⚠️ Could not determine index UID")
            else:
                print("✅ No indexes found, but connection was successful")
        else:
            print(f"⚠️ Unexpected response format from get_indexes: {type(indexes)}")
            
    except Exception as e:
        print(f"❌ Error testing search access: {e}")
    
    print("\n=== Registration complete ===")

if __name__ == "__main__":
    main() 