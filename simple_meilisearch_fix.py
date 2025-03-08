#!/usr/bin/env python
"""
Simple MeiliSearch Fix Script

This script helps fix common issues with MeiliSearch configuration
by testing connectivity and updating environment variables.
"""

import os
import sys
import json
import shutil
import logging
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
CLOUD_ADMIN_KEY = "4918956520b33882049fe5ab5eaf75de5788fc06ab3fb39cb13dfba7918e404e"

def test_connection(url):
    """Test basic connectivity to a MeiliSearch instance"""
    try:
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            logger.info(f"✅ MeiliSearch at {url} is running")
            return True
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Connection error: {str(e)}")
        return False

def update_env_for_local():
    """Update .env file for local MeiliSearch use"""
    # Default keys from the start_meilisearch.bat file
    local_master_key = "4872ee35c9fbdc44ddea43ed21c26683508222d5"
    local_search_key = "83ce7af231e18059f56aab767e6a8f1c54a5b2198091fe4ea2bb107d9011af9f"
    local_admin_key = "4918956520b33882049fe5ab5eaf75de5788fc06ab3fb39cb13dfba7918e404e"
    
    # Backup .env file
    if os.path.exists(ENV_FILE_PATH):
        backup_path = f"{ENV_FILE_PATH}.bak"
        shutil.copy2(ENV_FILE_PATH, backup_path)
        logger.info(f"Created backup of .env file at {backup_path}")
    
    # Read all non-MeiliSearch settings from current .env
    env_vars = {}
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    if not key.startswith('MEILISEARCH_'):
                        env_vars[key] = value
    
    # Create new .env file with local MeiliSearch settings
    with open(ENV_FILE_PATH, 'w') as f:
        f.write("# MeiliSearch Local Configuration\n")
        f.write(f"MEILISEARCH_URL={LOCAL_URL}\n")
        f.write(f"MEILISEARCH_MASTER_KEY={local_master_key}\n")
        f.write(f"MEILISEARCH_SEARCH_KEY={local_search_key}\n")
        f.write(f"MEILISEARCH_ADMIN_KEY={local_admin_key}\n")
        f.write(f"MEILISEARCH_HOST={LOCAL_URL}\n\n")
        
        # Write other environment variables
        f.write("# Other settings\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    logger.info("✅ Updated .env file for local MeiliSearch use")
    return True

def update_env_for_cloud():
    """Update .env file for cloud MeiliSearch use"""
    # Known working cloud admin key
    cloud_master_key = CLOUD_ADMIN_KEY
    cloud_search_key = CLOUD_ADMIN_KEY  # Use admin key for search too for now
    cloud_admin_key = CLOUD_ADMIN_KEY
    
    # Backup .env file
    if os.path.exists(ENV_FILE_PATH):
        backup_path = f"{ENV_FILE_PATH}.bak"
        shutil.copy2(ENV_FILE_PATH, backup_path)
        logger.info(f"Created backup of .env file at {backup_path}")
    
    # Read all non-MeiliSearch settings from current .env
    env_vars = {}
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    if not key.startswith('MEILISEARCH_'):
                        env_vars[key] = value
    
    # Create new .env file with cloud MeiliSearch settings
    with open(ENV_FILE_PATH, 'w') as f:
        f.write("# MeiliSearch Cloud Configuration\n")
        f.write(f"MEILISEARCH_URL={CLOUD_URL}\n")
        f.write(f"MEILISEARCH_MASTER_KEY={cloud_master_key}\n")
        f.write(f"MEILISEARCH_SEARCH_KEY={cloud_search_key}\n")
        f.write(f"MEILISEARCH_ADMIN_KEY={cloud_admin_key}\n")
        f.write(f"MEILISEARCH_HOST={CLOUD_URL}\n\n")
        
        # Write other environment variables
        f.write("# Other settings\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    logger.info("✅ Updated .env file for cloud MeiliSearch use")
    return True

def update_api_env_file(is_cloud):
    """Update the API .env file with the same MeiliSearch settings"""
    if not os.path.exists(API_ENV_FILE_PATH):
        logger.warning(f"API .env file not found at {API_ENV_FILE_PATH}")
        return False
    
    # Backup API .env file
    backup_path = f"{API_ENV_FILE_PATH}.bak"
    shutil.copy2(API_ENV_FILE_PATH, backup_path)
    logger.info(f"Created backup of API .env file at {backup_path}")
    
    # Read current settings from the root .env file we just updated
    meili_settings = {}
    with open(ENV_FILE_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line and line.startswith('MEILISEARCH_'):
                key, value = line.split('=', 1)
                meili_settings[key] = value
    
    # Read non-MeiliSearch settings from API .env
    api_env_vars = {}
    with open(API_ENV_FILE_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                if not key.startswith('MEILISEARCH_'):
                    api_env_vars[key] = value
    
    # Create new API .env file
    with open(API_ENV_FILE_PATH, 'w') as f:
        f.write(f"# MeiliSearch {'Cloud' if is_cloud else 'Local'} Configuration\n")
        for key, value in meili_settings.items():
            f.write(f"{key}={value}\n")
        
        f.write("\n# Other API settings\n")
        for key, value in api_env_vars.items():
            f.write(f"{key}={value}\n")
    
    logger.info(f"✅ Updated API .env file for {'cloud' if is_cloud else 'local'} MeiliSearch use")
    return True

def create_switch_command():
    """Create a batch script to easily switch between local and cloud configurations"""
    with open("switch_meili_config.bat", "w") as f:
        f.write("""@echo off
REM Switch between local and cloud MeiliSearch configurations

if "%1"=="" (
    echo Usage: switch_meili_config.bat [local^|cloud]
    exit /b 1
)

if "%1"=="local" (
    echo Switching to local MeiliSearch configuration...
    python simple_meilisearch_fix.py local
    echo Done.
) else if "%1"=="cloud" (
    echo Switching to cloud MeiliSearch configuration...
    python simple_meilisearch_fix.py cloud
    echo Done.
) else (
    echo Invalid option. Use 'local' or 'cloud'.
    exit /b 1
)
""")
    logger.info("✅ Created switch_meili_config.bat script")
    return True

def main():
    """Main execution function"""
    logger.info("=== Simple MeiliSearch Fix ===")
    
    # Check command line arguments
    if len(sys.argv) < 2 or sys.argv[1] not in ["local", "cloud", "test"]:
        logger.info("Usage: python simple_meilisearch_fix.py [local|cloud|test]")
        logger.info("  local: Configure for local MeiliSearch")
        logger.info("  cloud: Configure for cloud MeiliSearch")
        logger.info("  test:  Test connectivity to both instances")
        return False
    
    command = sys.argv[1]
    
    # Test connectivity
    if command == "test" or command == "local":
        logger.info("\nTesting local MeiliSearch instance...")
        local_running = test_connection(LOCAL_URL)
        if command == "local" and not local_running:
            logger.error("❌ Local MeiliSearch is not running!")
            logger.info("Please start it with: ./start_meilisearch.bat")
            return False
    
    if command == "test" or command == "cloud":
        logger.info("\nTesting cloud MeiliSearch instance...")
        cloud_running = test_connection(CLOUD_URL)
        if command == "cloud" and not cloud_running:
            logger.error("❌ Cloud MeiliSearch is not accessible!")
            logger.info("Please check your internet connection and the cloud URL")
            return False
    
    # If just testing, exit now
    if command == "test":
        logger.info("\n=== Test Results ===")
        logger.info(f"Local MeiliSearch: {'Available' if local_running else 'Not available'}")
        logger.info(f"Cloud MeiliSearch: {'Available' if cloud_running else 'Not available'}")
        return True
    
    # Update environment files
    if command == "local":
        logger.info("\nConfiguring for local MeiliSearch...")
        update_env_for_local()
        update_api_env_file(is_cloud=False)
    elif command == "cloud":
        logger.info("\nConfiguring for cloud MeiliSearch...")
        update_env_for_cloud()
        update_api_env_file(is_cloud=True)
    
    # Create switch command
    create_switch_command()
    
    # Final message
    logger.info(f"\n✅ Configuration updated for {command} MeiliSearch")
    logger.info("You can now run your application with the updated configuration")
    logger.info("In the future, you can switch configurations with: switch_meili_config.bat [local|cloud]")
    
    return True

if __name__ == "__main__":
    main() 