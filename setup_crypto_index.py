#!/usr/bin/env python
"""
Crypto Index Setup Script

This script creates and populates the 'crypto' index in MeiliSearch
with sample cryptocurrency data to demonstrate search functionality.
"""

import os
import json
import logging
import requests
import meilisearch
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MeiliSearch connection details
MEILISEARCH_URL = os.environ.get("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_ADMIN_KEY = os.environ.get("MEILISEARCH_ADMIN_KEY", "")
INDEX_NAME = "crypto"

# Sample cryptocurrency data
CRYPTO_DATA = [
    {
        "id": "1",
        "symbol": "BTC",
        "name": "Bitcoin",
        "description": "Bitcoin is a decentralized digital currency that can be transferred on the peer-to-peer bitcoin network.",
        "current_price": 45678.92,
        "market_cap": 876543210000,
        "volume_24h": 32456789000,
        "price_change_24h": 2.5,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "store of value", "payment"],
        "tags": ["defi", "bitcoin", "original"],
        "launch_date": "2009-01-03",
        "website": "https://bitcoin.org",
        "whitepaper": "https://bitcoin.org/bitcoin.pdf"
    },
    {
        "id": "2",
        "symbol": "ETH",
        "name": "Ethereum",
        "description": "Ethereum is a decentralized, open-source blockchain with smart contract functionality.",
        "current_price": 3245.67,
        "market_cap": 389012345678,
        "volume_24h": 19876543210,
        "price_change_24h": -1.2,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "smart contracts", "defi"],
        "tags": ["defi", "smart contract", "ethereum", "web3"],
        "launch_date": "2015-07-30",
        "website": "https://ethereum.org",
        "whitepaper": "https://ethereum.org/en/whitepaper/"
    },
    {
        "id": "3",
        "symbol": "USDT",
        "name": "Tether",
        "description": "Tether is a stablecoin pegged to the U.S. dollar, backed by Tether's reserves.",
        "current_price": 1.00,
        "market_cap": 87654321000,
        "volume_24h": 76543210000,
        "price_change_24h": 0.01,
        "is_stablecoin": True,
        "category": ["stablecoin", "payment"],
        "tags": ["stablecoin", "trading", "tether", "usd"],
        "launch_date": "2014-10-06",
        "website": "https://tether.to",
        "whitepaper": "https://tether.to/en/transparency/#reports"
    },
    {
        "id": "4",
        "symbol": "BNB",
        "name": "Binance Coin",
        "description": "Binance Coin is the cryptocurrency issued by the Binance exchange.",
        "current_price": 456.78,
        "market_cap": 75123456789,
        "volume_24h": 3456789012,
        "price_change_24h": 1.5,
        "is_stablecoin": False,
        "category": ["exchange token", "payment"],
        "tags": ["exchange", "binance", "trading"],
        "launch_date": "2017-07-01",
        "website": "https://www.binance.com",
        "whitepaper": "https://www.binance.com/resources/ico/Binance_WhitePaper_en.pdf"
    },
    {
        "id": "5",
        "symbol": "SOL",
        "name": "Solana",
        "description": "Solana is a high-performance blockchain supporting builders around the world creating crypto apps.",
        "current_price": 123.45,
        "market_cap": 45678901234,
        "volume_24h": 2345678901,
        "price_change_24h": 3.7,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "smart contracts", "defi"],
        "tags": ["solana", "web3", "fast", "nft"],
        "launch_date": "2020-03-16",
        "website": "https://solana.com",
        "whitepaper": "https://solana.com/solana-whitepaper.pdf"
    },
    {
        "id": "6",
        "symbol": "ADA",
        "name": "Cardano",
        "description": "Cardano is a proof-of-stake blockchain platform with a focus on security and sustainability.",
        "current_price": 0.45,
        "market_cap": 16012345678,
        "volume_24h": 654321098,
        "price_change_24h": -0.9,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "smart contracts", "sustainability"],
        "tags": ["cardano", "pos", "research", "sustainability"],
        "launch_date": "2017-09-29",
        "website": "https://cardano.org",
        "whitepaper": "https://docs.cardano.org/en/latest/"
    },
    {
        "id": "7",
        "symbol": "XRP",
        "name": "Ripple",
        "description": "Ripple is a real-time gross settlement system, currency exchange and remittance network.",
        "current_price": 0.56,
        "market_cap": 28765432198,
        "volume_24h": 1234567890,
        "price_change_24h": 0.3,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "payment", "remittance"],
        "tags": ["ripple", "swift", "banking", "remittance"],
        "launch_date": "2012-01-01",
        "website": "https://ripple.com",
        "whitepaper": "https://ripple.com/files/ripple_consensus_whitepaper.pdf"
    },
    {
        "id": "8",
        "symbol": "DOGE",
        "name": "Dogecoin",
        "description": "Dogecoin is a cryptocurrency created as a joke, featuring a Shiba Inu dog from a meme.",
        "current_price": 0.08,
        "market_cap": 11087654321,
        "volume_24h": 987654321,
        "price_change_24h": 5.2,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "meme", "payment"],
        "tags": ["doge", "meme", "elon musk", "dogecoin"],
        "launch_date": "2013-12-06",
        "website": "https://dogecoin.com",
        "whitepaper": "https://github.com/dogecoin/dogecoin"
    },
    {
        "id": "9",
        "symbol": "DOT",
        "name": "Polkadot",
        "description": "Polkadot is a protocol that connects blockchains, allowing them to communicate with each other.",
        "current_price": 6.78,
        "market_cap": 8765432109,
        "volume_24h": 567890123,
        "price_change_24h": -2.1,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "interoperability", "infrastructure"],
        "tags": ["polkadot", "interoperability", "parachains", "web3"],
        "launch_date": "2020-05-26",
        "website": "https://polkadot.network",
        "whitepaper": "https://polkadot.network/PolkaDotPaper.pdf"
    },
    {
        "id": "10",
        "symbol": "AVAX",
        "name": "Avalanche",
        "description": "Avalanche is an open-source platform for launching decentralized finance applications.",
        "current_price": 23.45,
        "market_cap": 7654321098,
        "volume_24h": 456789012,
        "price_change_24h": 1.8,
        "is_stablecoin": False,
        "category": ["cryptocurrency", "smart contracts", "defi"],
        "tags": ["avalanche", "defi", "layer1", "smart contract"],
        "launch_date": "2020-09-21",
        "website": "https://www.avax.network",
        "whitepaper": "https://www.avalabs.org/whitepapers"
    }
]

# Generate price history data for each cryptocurrency
def generate_price_history(crypto_data):
    """Generate 30 days of price history for each cryptocurrency"""
    enhanced_data = []
    
    for crypto in crypto_data:
        # Copy the original data
        enhanced_crypto = crypto.copy()
        
        # Generate 30 days of price history
        price_history = []
        current_price = enhanced_crypto["current_price"]
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).strftime("%Y-%m-%d")
            
            # Add some randomness to the price
            daily_change = random.uniform(-0.05, 0.05)  # -5% to +5%
            if i > 0:
                price = price_history[-1]["price"] * (1 + daily_change)
            else:
                # Start with a price about 30% different from current
                price = current_price * (1 - random.uniform(0.2, 0.4))
            
            # Ensure the final price matches the current price
            if i == 29:
                price = current_price
                
            price_history.append({
                "date": date,
                "price": round(price, 2),
                "volume": round(random.uniform(0.5, 1.5) * enhanced_crypto["volume_24h"] / 30, 0)
            })
        
        enhanced_crypto["price_history"] = price_history
        enhanced_data.append(enhanced_crypto)
    
    return enhanced_data

def configure_index_settings(index):
    """Configure the index settings for optimal search experience"""
    logger.info("Configuring index settings...")
    
    # Set searchable attributes
    try:
        task = index.update_searchable_attributes([
            "name", 
            "symbol", 
            "description", 
            "tags", 
            "category"
        ])
        logger.info(f"✅ Updated searchable attributes: {task}")
    except Exception as e:
        logger.error(f"Failed to update searchable attributes: {str(e)}")
    
    # Set filterable attributes
    try:
        task = index.update_filterable_attributes([
            "current_price", 
            "market_cap", 
            "volume_24h", 
            "price_change_24h",
            "is_stablecoin",
            "category",
            "tags",
            "launch_date"
        ])
        logger.info(f"✅ Updated filterable attributes: {task}")
    except Exception as e:
        logger.error(f"Failed to update filterable attributes: {str(e)}")
    
    # Set sortable attributes
    try:
        task = index.update_sortable_attributes([
            "current_price", 
            "market_cap", 
            "volume_24h", 
            "price_change_24h",
            "launch_date"
        ])
        logger.info(f"✅ Updated sortable attributes: {task}")
    except Exception as e:
        logger.error(f"Failed to update sortable attributes: {str(e)}")
    
    # Set ranking rules
    try:
        task = index.update_ranking_rules([
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness"
        ])
        logger.info(f"✅ Updated ranking rules: {task}")
    except Exception as e:
        logger.error(f"Failed to update ranking rules: {str(e)}")
    
    # Set synonyms
    try:
        task = index.update_synonyms({
            "btc": ["bitcoin"],
            "eth": ["ethereum"],
            "cryptocurrency": ["crypto", "coin", "token"],
            "defi": ["decentralized finance"]
        })
        logger.info(f"✅ Updated synonyms: {task}")
    except Exception as e:
        logger.error(f"Failed to update synonyms: {str(e)}")

def main():
    """Main execution function"""
    logger.info("=== Crypto Index Setup ===")
    
    if not MEILISEARCH_ADMIN_KEY:
        logger.error("❌ MEILISEARCH_ADMIN_KEY is not set in the .env file.")
        logger.info("Please run fix_meilisearch_setup.py first to set up your MeiliSearch keys.")
        return False
    
    # Connect to MeiliSearch
    try:
        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_ADMIN_KEY)
        logger.info(f"✅ Connected to MeiliSearch at {MEILISEARCH_URL}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MeiliSearch: {str(e)}")
        return False
    
    # Check if index exists, create if it doesn't
    try:
        # Check if index exists
        indexes = client.get_indexes()
        index_exists = any(idx.get("uid") == INDEX_NAME for idx in indexes.get("results", []))
        
        if not index_exists:
            # Create the index
            task = client.create_index(INDEX_NAME, {"primaryKey": "id"})
            logger.info(f"✅ Created crypto index: {task}")
        else:
            logger.info(f"ℹ️ Crypto index already exists. Will update data.")
    except Exception as e:
        logger.error(f"❌ Error checking/creating index: {str(e)}")
        return False
    
    # Get the index object
    index = client.index(INDEX_NAME)
    
    # Generate enhanced data with price history
    enhanced_data = generate_price_history(CRYPTO_DATA)
    
    # Add documents to the index
    try:
        task = index.add_documents(enhanced_data)
        logger.info(f"✅ Added crypto data to index: {task}")
    except Exception as e:
        logger.error(f"❌ Failed to add documents: {str(e)}")
        return False
    
    # Configure index settings
    configure_index_settings(index)
    
    # Display sample searches to try
    logger.info("\n=== Setup Complete ===")
    logger.info("""
You can now search the crypto index. Try these example searches:

1. Basic search:
   client.index("crypto").search("bitcoin")

2. Filter by price:
   client.index("crypto").search("", {"filter": "current_price > 1000"})

3. Sort by market cap:
   client.index("crypto").search("", {"sort": ["market_cap:desc"]})

4. Search by category:
   client.index("crypto").search("", {"filter": "category = defi"})

5. Combined search and filter:
   client.index("crypto").search("coin", {"filter": "is_stablecoin = true"})

Use these in the meilisearch_demo.py script or create your own search queries!
""")
    
    return True

if __name__ == "__main__":
    main() 