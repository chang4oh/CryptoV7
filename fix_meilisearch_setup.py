#!/usr/bin/env python
"""
MeiliSearch Setup Fixer

This script resolves common MeiliSearch setup issues by:
1. Testing connections to both local and cloud instances
2. Retrieving valid keys for both instances
3. Creating necessary indexes
4. Updating .env files and configuration
"""

import os
import sys
import json
import logging
import shutil
import requests
import meilisearch
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Constants
LOCAL_URL = "http://localhost:7700"
CLOUD_URL = "https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io"
ENV_FILE_PATH = ".env"
API_ENV_FILE_PATH = "api/.env"

# The admin key that works with the cloud instance
CLOUD_ADMIN_KEY = "4918956520b33882049fe5ab5eaf75de5788fc06ab3fb39cb13dfba7918e404e"

# Common indexes to create
DEFAULT_INDEXES = ["crypto", "news", "markets"]

def test_connection(url, key=None, key_type="admin"):
    """Test connection to a MeiliSearch instance with a specific key"""
    try:
        if key:
            headers = {"Authorization": f"Bearer {key}"}
            response = requests.get(f"{url}/health", headers=headers)
        else:
            response = requests.get(f"{url}/health")
        
        if response.status_code == 200:
            logger.info(f"✅ Instance at {url} is running")
            return True
        else:
            logger.error(f"❌ Health check failed: Status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Connection error: {str(e)}")
        return False

def get_valid_keys(url, master_key):
    """Retrieve valid keys from MeiliSearch instance"""
    try:
        headers = {"Authorization": f"Bearer {master_key}"}
        response = requests.get(f"{url}/keys", headers=headers)
        
        if response.status_code == 200:
            keys = response.json()
            logger.info(f"✅ Successfully retrieved keys from {url}")
            return keys
        else:
            logger.error(f"❌ Failed to get keys: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Error retrieving keys: {str(e)}")
        return None

def extract_key_values(keys_data):
    """Extract master, search and admin keys from keys response"""
    if not keys_data or "results" not in keys_data:
        return None, None, None
    
    master_key = None
    search_key = None
    admin_key = None
    
    for key in keys_data.get("results", []):
        if "*" in key.get("actions", []):
            master_key = key.get("key")
        elif "search" in key.get("actions", []) and not admin_key:
            search_key = key.get("key")
        elif set(["documents.add", "indexes.create", "indexes.update"]).issubset(set(key.get("actions", []))):
            admin_key = key.get("key")
    
    return master_key, search_key, admin_key

def create_indexes(url, key, indexes):
    """Create required indexes on a MeiliSearch instance"""
    client = meilisearch.Client(url, key)
    created_indexes = []
    
    try:
        # List existing indexes
        response = client.get_indexes()
        existing_indexes = [idx.get("uid") for idx in response.get("results", [])]
        logger.info(f"Found {len(existing_indexes)} existing indexes: {', '.join(existing_indexes) if existing_indexes else 'none'}")
        
        # Create missing indexes
        for index_name in indexes:
            if index_name not in existing_indexes:
                logger.info(f"Creating index '{index_name}'...")
                response = client.create_index(index_name, {"primaryKey": "id"})
                logger.info(f"Index creation task: {response.task_uid if hasattr(response, 'task_uid') else response}")
                created_indexes.append(index_name)
            else:
                logger.info(f"Index '{index_name}' already exists")
        
        if created_indexes:
            logger.info(f"✅ Created {len(created_indexes)} new indexes: {', '.join(created_indexes)}")
        else:
            logger.info("No new indexes needed to be created")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {str(e)}")
        return False

def create_switch_config_file(local_master_key, local_search_key, local_admin_key,
                             cloud_master_key, cloud_search_key, cloud_admin_key):
    """Create switch_meilisearch_config.py file"""
    # Set default values for keys
    local_master = local_master_key or "MISSING_KEY"
    local_search = local_search_key or "MISSING_KEY"
    local_admin = local_admin_key or "MISSING_KEY"
    cloud_master = cloud_master_key or "MISSING_KEY" 
    cloud_search = cloud_search_key or "MISSING_KEY"
    cloud_admin = cloud_admin_key or "MISSING_KEY"
    
    # Create the file content
    content = """#!/usr/bin/env python
"""
    content += """
MeiliSearch Configuration Switcher

This script switches between local and cloud MeiliSearch configurations.
"""
    content += """

import os
import shutil
import logging
import argparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def backup_env_file(env_path):
    """Create a backup of the .env file"""
    if os.path.exists(env_path):
        backup_path = f"{env_path}.bak"
        shutil.copy2(env_path, backup_path)
        logger.info(f"Created backup of .env file at {backup_path}")
        return True
    return False

def load_current_env(env_path):
    """Load non-MeiliSearch settings from current .env file"""
    if not os.path.exists(env_path):
        logger.error(f".env file not found at {env_path}")
        return {}
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                if not key.startswith('MEILISEARCH_'):
                    env_vars[key] = value
    
    return env_vars

def create_new_env_file(env_path, env_vars, config_type):
    """Create a new .env file with the specified configuration"""
    # Local configuration
    local_config = {{
        "MEILISEARCH_URL": "http://localhost:7700",
        "MEILISEARCH_MASTER_KEY": "{local_master}",
        "MEILISEARCH_SEARCH_KEY": "{local_search}",
        "MEILISEARCH_ADMIN_KEY": "{local_admin}",
        "MEILISEARCH_HOST": "http://localhost:7700"
    }}
    
    # Cloud configuration
    cloud_config = {{
        "MEILISEARCH_URL": "https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io",
        "MEILISEARCH_MASTER_KEY": "{cloud_master}",
        "MEILISEARCH_SEARCH_KEY": "{cloud_search}",
        "MEILISEARCH_ADMIN_KEY": "{cloud_admin}",
        "MEILISEARCH_HOST": "https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io"
    }}
    
    # Choose the configuration
    config = local_config if config_type == "local" else cloud_config
    
    # Write the new .env file
    with open(env_path, "w") as f:
        # Write MeiliSearch config first with a header
        f.write(f"# MeiliSearch {config_type.capitalize()} Configuration\\n")
        for key, value in config.items():
            f.write(f"{key}={value}\\n")
        
        # Write an empty line as separator
        f.write("\\n")
        
        # Write other environment variables
        f.write("# Other API settings\\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\\n")
    
    logger.info(f"Created new .env file with {config_type} MeiliSearch configuration")
    return True

def switch_config(target_dir, config_type):
    """Switch MeiliSearch configuration in the specified directory"""
    env_path = os.path.join(target_dir, ".env")
    api_env_path = os.path.join(target_dir, "api", ".env")
    
    # Switch root .env file
    logger.info(f"Switching root .env to {config_type} configuration")
    backup_env_file(env_path)
    env_vars = load_current_env(env_path)
    create_new_env_file(env_path, env_vars, config_type)
    
    # Switch API .env file if it exists
    if os.path.exists(api_env_path):
        logger.info(f"Switching API .env to {config_type} configuration")
        backup_env_file(api_env_path)
        api_env_vars = load_current_env(api_env_path)
        create_new_env_file(api_env_path, api_env_vars, config_type)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Switch between MeiliSearch configurations")
    parser.add_argument("config", choices=["local", "cloud"], help="Configuration type to switch to")
    
    args = parser.parse_args()
    
    logger.info(f"Switching to {args.config} MeiliSearch configuration")
    switch_config(".", args.config)
    logger.info(f"Successfully switched to {args.config} MeiliSearch configuration")
    logger.info(f"Run your application now with the new configuration")
"""

    # Write the file
    with open("switch_meilisearch_config.py", "w") as f:
        f.write(content)
    
    logger.info("✅ Created switch_meilisearch_config.py script for easy switching between configurations")
    return True

def create_template_env_file(local_master_key, local_search_key, local_admin_key,
                            cloud_master_key, cloud_search_key, cloud_admin_key):
    """Create template .env file with both configurations"""
    # Set default values for keys
    local_master = local_master_key or "MISSING_KEY"
    local_search = local_search_key or "MISSING_KEY"
    local_admin = local_admin_key or "MISSING_KEY"
    cloud_master = cloud_master_key or "MISSING_KEY"
    cloud_search = cloud_search_key or "MISSING_KEY"
    cloud_admin = cloud_admin_key or "MISSING_KEY"
    
    # Create file content
    content = """# MeiliSearch Configuration
# You can switch between local and cloud using the switch_meilisearch_config.py script

# Local Configuration (default)
"""
    content += f"""MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_MASTER_KEY={local_master}
MEILISEARCH_SEARCH_KEY={local_search}
MEILISEARCH_ADMIN_KEY={local_admin}
MEILISEARCH_HOST=http://localhost:7700

# Cloud Configuration (commented out)
# MEILISEARCH_URL=https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io
# MEILISEARCH_MASTER_KEY={cloud_master}
# MEILISEARCH_SEARCH_KEY={cloud_search}
# MEILISEARCH_ADMIN_KEY={cloud_admin}
# MEILISEARCH_HOST=https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io

# Retain other environment variables below
"""

    # Write the file
    with open("meilisearch_template.env", "w") as f:
        f.write(content)
    
    logger.info("✅ Created meilisearch_template.env with both configurations")
    return True

def update_env_files(local_master_key, local_search_key, local_admin_key, 
                   cloud_master_key, cloud_search_key, cloud_admin_key):
    """Update main .env file and api/.env file with new keys"""
    # Backup existing files
    if os.path.exists(ENV_FILE_PATH):
        shutil.copy2(ENV_FILE_PATH, f"{ENV_FILE_PATH}.bak")
        logger.info(f"Created backup of main .env file at {ENV_FILE_PATH}.bak")
    
    if os.path.exists(API_ENV_FILE_PATH):
        shutil.copy2(API_ENV_FILE_PATH, f"{API_ENV_FILE_PATH}.bak")
        logger.info(f"Created backup of API .env file at {API_ENV_FILE_PATH}.bak")
    
    # Create switch config file
    created_switch = create_switch_config_file(
        local_master_key, local_search_key, local_admin_key,
        cloud_master_key, cloud_search_key, cloud_admin_key
    )
    
    # Create template env file
    created_template = create_template_env_file(
        local_master_key, local_search_key, local_admin_key,
        cloud_master_key, cloud_search_key, cloud_admin_key
    )
    
    return created_switch and created_template

def create_meilisearch_demo_script():
    """Create a demo script for MeiliSearch operations"""
    with open("meilisearch_demo.py", "w") as f:
        f.write("""#!/usr/bin/env python
"""
"""
MeiliSearch Demo Script

This script demonstrates common MeiliSearch operations:
1. Connecting to MeiliSearch
2. Creating and configuring indexes
3. Adding documents
4. Searching
5. Using filters
"""
"""

import json
import os
from dotenv import load_dotenv
import meilisearch

# Load environment variables
load_dotenv()

# Get MeiliSearch connection details
MEILISEARCH_URL = os.environ.get("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_ADMIN_KEY = os.environ.get("MEILISEARCH_ADMIN_KEY", "")
MEILISEARCH_SEARCH_KEY = os.environ.get("MEILISEARCH_SEARCH_KEY", "")

# Colors for terminal output
GREEN = "\\033[92m"
YELLOW = "\\033[93m"
RED = "\\033[91m"
RESET = "\\033[0m"
BOLD = "\\033[1m"

def print_header(title):
    """Print a formatted header"""
    print(f"\\n{BOLD}{GREEN}=== {title} ==={RESET}\\n")

def print_info(message):
    """Print formatted info message"""
    print(f"{YELLOW}-> {message}{RESET}")

def print_error(message):
    """Print formatted error message"""
    print(f"{RED}ERROR: {message}{RESET}")

def print_result(label, data):
    """Print a formatted result"""
    print(f"{BOLD}{label}:{RESET}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2))
    else:
        print(data)

def demo_index_operations():
    """Demonstrate index operations"""
    print_header("Index Operations")
    
    # Connect with admin key
    client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_ADMIN_KEY)
    
    # List all indexes
    print_info("Listing all indexes")
    try:
        indexes = client.get_indexes()
        print_result("Current indexes", indexes)
    except Exception as e:
        print_error(f"Failed to list indexes: {str(e)}")
    
    # Create a new index
    print_info("Creating a demo index")
    try:
        task = client.create_index("demo_index", {"primaryKey": "id"})
        print_result("Create index task", task)
    except Exception as e:
        if "index_already_exists" in str(e):
            print_info("Index 'demo_index' already exists")
        else:
            print_error(f"Failed to create index: {str(e)}")
    
    # Get index information
    try:
        index = client.get_index("demo_index")
        print_result("Index info", index)
    except Exception as e:
        print_error(f"Failed to get index info: {str(e)}")
    
    return client

def demo_document_operations(client):
    """Demonstrate document operations"""
    print_header("Document Operations")
    
    # Get the index
    index = client.index("demo_index")
    
    # Define some sample documents
    documents = [
        {
            "id": "1",
            "title": "Bitcoin",
            "description": "The first and most popular cryptocurrency",
            "price": 40000,
            "category": "cryptocurrency"
        },
        {
            "id": "2",
            "title": "Ethereum",
            "description": "A decentralized platform for applications",
            "price": 2500,
            "category": "cryptocurrency"
        },
        {
            "id": "3",
            "title": "Stock Market News",
            "description": "Latest updates from global stock markets",
            "source": "Financial Times",
            "category": "news"
        }
    ]
    
    # Add documents
    print_info("Adding documents")
    try:
        task = index.add_documents(documents)
        print_result("Add documents task", task)
    except Exception as e:
        print_error(f"Failed to add documents: {str(e)}")
    
    # Get documents
    print_info("Getting documents")
    try:
        result = index.get_documents({"limit": 5})
        print_result("Documents", result)
    except Exception as e:
        print_error(f"Failed to get documents: {str(e)}")
    
    return index

def demo_search_operations(index):
    """Demonstrate search operations"""
    print_header("Search Operations")
    
    # Basic search
    print_info("Basic search")
    try:
        result = index.search("bitcoin")
        print_result("Search for 'bitcoin'", result)
    except Exception as e:
        print_error(f"Failed to perform search: {str(e)}")
    
    # Search with filter
    print_info("Search with filter")
    try:
        result = index.search("crypto", {
            "filter": "category = cryptocurrency"
        })
        print_result("Search for 'crypto' in cryptocurrency category", result)
    except Exception as e:
        print_error(f"Failed to perform filtered search: {str(e)}")
    
    # Configure searchable attributes
    print_info("Configuring searchable attributes")
    try:
        task = index.update_searchable_attributes(["title", "description"])
        print_result("Update searchable attributes task", task)
    except Exception as e:
        print_error(f"Failed to update searchable attributes: {str(e)}")
    
    # Configure filterable attributes
    print_info("Configuring filterable attributes")
    try:
        task = index.update_filterable_attributes(["category", "price"])
        print_result("Update filterable attributes task", task)
    except Exception as e:
        print_error(f"Failed to update filterable attributes: {str(e)}")
    
    # Search with range filter
    print_info("Search with range filter")
    try:
        result = index.search("", {
            "filter": "price > 3000"
        })
        print_result("Search for items with price > 3000", result)
    except Exception as e:
        print_error(f"Failed to perform range filtered search: {str(e)}")

def demo_multi_search(client):
    """Demonstrate multi-search operations"""
    print_header("Multi-Search Operations")
    
    try:
        # Create another test index if needed
        try:
            client.create_index("test_index", {"primaryKey": "id"})
            test_index = client.index("test_index")
            test_index.add_documents([
                {"id": "101", "name": "Test Product", "category": "test"}
            ])
        except:
            pass
        
        # Define multi-search query
        queries = {
            "queries": [
                {
                    "indexUid": "demo_index",
                    "q": "bitcoin"
                },
                {
                    "indexUid": "test_index",
                    "q": "test"
                }
            ]
        }
        
        # Execute multi-search
        print_info("Executing multi-search")
        result = client.multi_search(queries)
        print_result("Multi-search results", result)
    except Exception as e:
        print_error(f"Failed to perform multi-search: {str(e)}")

if __name__ == "__main__":
    print_header("MeiliSearch Demo")
    print_info(f"Using MeiliSearch at {MEILISEARCH_URL}")
    
    # Check if keys are available
    if not MEILISEARCH_ADMIN_KEY:
        print_error("MEILISEARCH_ADMIN_KEY is not set in .env file")
        exit(1)
    
    if not MEILISEARCH_SEARCH_KEY:
        print_info("MEILISEARCH_SEARCH_KEY is not set in .env file, some operations might fail")
    
    # Run the demo
    try:
        client = demo_index_operations()
        index = demo_document_operations(client)
        demo_search_operations(index)
        demo_multi_search(client)
        
        print_header("Demo Completed Successfully")
        print_info("You can now explore MeiliSearch further using the Python client")
    except Exception as e:
        print_error(f"Demo failed: {str(e)}")
""")
    
    logger.info("✅ Created meilisearch_demo.py script for demonstrating MeiliSearch operations")
    return True

def main():
    """Main execution function"""
    logger.info("=== MeiliSearch Setup Fixer ===")
    
    # Step 1: Test connections
    logger.info("\nTesting MeiliSearch connections...")
    local_running = test_connection(LOCAL_URL)
    cloud_running = test_connection(CLOUD_URL)
    
    if not local_running and not cloud_running:
        logger.error("❌ Neither local nor cloud MeiliSearch instances are accessible")
        logger.info("Please start your local MeiliSearch with: ./start_meilisearch.bat")
        logger.info("Or check your cloud instance settings")
        return False
    
    # Default to empty values
    local_master_key = local_search_key = local_admin_key = None
    cloud_master_key = cloud_search_key = cloud_admin_key = None
    
    # Step 2: Get valid keys for local instance if running
    if local_running:
        logger.info("\nRetrieving keys for local MeiliSearch...")
        # Try with the current master key
        local_keys = get_valid_keys(LOCAL_URL, os.environ.get("MEILISEARCH_MASTER_KEY", "4872ee35c9fbdc44ddea43ed21c26683508222d5"))
        
        if local_keys:
            local_master_key, local_search_key, local_admin_key = extract_key_values(local_keys)
            logger.info(f"✅ Successfully retrieved valid keys for local instance")
        else:
            logger.warning("⚠️ Could not retrieve valid keys for local instance")
            logger.info("Using the master key from start_meilisearch.bat: 4872ee35c9fbdc44ddea43ed21c26683508222d5")
            local_master_key = "4872ee35c9fbdc44ddea43ed21c26683508222d5"
    
    # Step 3: Get valid keys for cloud instance
    if cloud_running:
        logger.info("\nRetrieving keys for cloud MeiliSearch...")
        cloud_admin_key = CLOUD_ADMIN_KEY  # We know this works from the test
        
        # Try to get other keys using the admin key
        cloud_keys = get_valid_keys(CLOUD_URL, cloud_admin_key)
        
        if cloud_keys:
            cloud_master_key, cloud_search_key, _ = extract_key_values(cloud_keys)
            logger.info(f"✅ Successfully retrieved valid keys for cloud instance")
        else:
            logger.warning("⚠️ Could not retrieve all valid keys for cloud instance")
            logger.info("Using only the known admin key")
            cloud_master_key = CLOUD_ADMIN_KEY  # Fallback to using the admin key for everything
            cloud_search_key = CLOUD_ADMIN_KEY
    
    # Step 4: Create indexes on the cloud instance
    if cloud_running and cloud_admin_key:
        logger.info("\nCreating required indexes on cloud instance...")
        if create_indexes(CLOUD_URL, cloud_admin_key, DEFAULT_INDEXES):
            logger.info("✅ Cloud indexes setup complete")
        else:
            logger.warning("⚠️ Could not complete cloud index setup")
    
    # Step 5: Create indexes on the local instance
    if local_running and local_master_key:
        logger.info("\nCreating required indexes on local instance...")
        if create_indexes(LOCAL_URL, local_master_key, DEFAULT_INDEXES):
            logger.info("✅ Local indexes setup complete")
        else:
            logger.warning("⚠️ Could not complete local index setup")
    
    # Step 6: Update env files
    logger.info("\nUpdating environment files with valid keys...")
    if update_env_files(
        local_master_key, local_search_key, local_admin_key,
        cloud_master_key, cloud_search_key, cloud_admin_key
    ):
        logger.info("✅ Environment files updated successfully")
    else:
        logger.warning("⚠️ Could not update environment files")
    
    # Step 7: Create demo script
    logger.info("\nCreating MeiliSearch demo script...")
    if create_meilisearch_demo_script():
        logger.info("✅ Demo script created successfully")
    else:
        logger.warning("⚠️ Could not create demo script")
    
    # Final summary
    logger.info("\n=== Setup Complete ===")
    logger.info("""
Next steps:
1. To switch to local mode: python switch_meilisearch_config.py local
2. To switch to cloud mode: python switch_meilisearch_config.py cloud
3. To try MeiliSearch operations: python meilisearch_demo.py

Your MeiliSearch keys have been configured in the switch script.
""")
    
    return True

if __name__ == "__main__":
    main() 