#!/usr/bin/env python
"""
MeiliSearch Configuration Switcher

This script allows you to easily switch between local and cloud MeiliSearch configurations.
It backs up your current .env file and creates a new one with the selected configuration.
"""

import os
import shutil
import sys
import logging
from dotenv import load_dotenv
import argparse

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
    
    # Load current .env file
    load_dotenv(env_path)
    
    # Get all environment variables except MeiliSearch ones
    env_vars = {}
    for key, value in os.environ.items():
        if not key.startswith("MEILISEARCH_") and not key.startswith("PYTHON"):
            env_vars[key] = value
    
    return env_vars

def create_new_env_file(env_path, env_vars, config_type):
    """Create a new .env file with the specified configuration"""
    # Local configuration
    local_config = {
        "MEILISEARCH_URL": "http://localhost:7700",
        "MEILISEARCH_MASTER_KEY": "4872ee35c9fbdc44ddea43ed21c26683508222d5",
        "MEILISEARCH_SEARCH_KEY": "83ce7af231e18059f56aab767e6a8f1c54a5b2198091fe4ea2bb107d9011af9f",
        "MEILISEARCH_ADMIN_KEY": "4918956520b33882049fe5ab5eaf75de5788fc06ab3fb39cb13dfba7918e404e",
        "MEILISEARCH_HOST": "http://localhost:7700"
    }
    
    # Cloud configuration (using same keys as specified by user)
    cloud_config = {
        "MEILISEARCH_URL": "https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io",
        "MEILISEARCH_MASTER_KEY": "4872ee35c9fbdc44ddea43ed21c26683508222d5",
        "MEILISEARCH_SEARCH_KEY": "83ce7af231e18059f56aab767e6a8f1c54a5b2198091fe4ea2bb107d9011af9f",
        "MEILISEARCH_ADMIN_KEY": "4918956520b33882049fe5ab5eaf75de5788fc06ab3fb39cb13dfba7918e404e",
        "MEILISEARCH_HOST": "https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io"
    }
    
    # Choose the configuration
    config = local_config if config_type == "local" else cloud_config
    
    # Write the new .env file
    with open(env_path, "w") as f:
        # Write MeiliSearch config first with a header
        f.write(f"# MeiliSearch {config_type.capitalize()} Configuration\n")
        for key, value in config.items():
            f.write(f"{key}={value}\n")
        
        # Write an empty line as separator
        f.write("\n")
        
        # Write other environment variables
        f.write("# Other API settings\n")
        for key, value in env_vars.items():
            if not key.startswith("_") and len(str(value).strip()) > 0:
                f.write(f"{key}={value}\n")
    
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
    logger.info(f"Run 'python test_meilisearch_cloud.py' to test the configuration") 