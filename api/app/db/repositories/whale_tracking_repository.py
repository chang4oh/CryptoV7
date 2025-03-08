from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from app.db.mongodb import get_database
from app.db.repositories.base_repository import BaseRepository
from app.models.whale_tracking import WhaleTransaction, WhaleWallet, TokenHolding, BlockchainNetwork
import logging

logger = logging.getLogger(__name__)

class WhaleTransactionRepository(BaseRepository[WhaleTransaction]):
    """Repository for whale transactions."""
    
    def __init__(self):
        super().__init__("whale_transactions", WhaleTransaction)
    
    async def get_recent_transactions(
        self, 
        network: Optional[BlockchainNetwork] = None,
        token: Optional[str] = None,
        min_usd_value: Optional[float] = None,
        limit: int = 50
    ) -> List[WhaleTransaction]:
        """Get recent significant whale transactions."""
        query = {"significant": True}
        
        if network:
            query["network"] = network
            
        if token:
            query["token"] = token
            
        if min_usd_value:
            query["usd_value"] = {"$gte": min_usd_value}
        
        sort = [("timestamp", -1)]  # Sort by timestamp descending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def get_wallet_transactions(
        self, 
        wallet_address: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[WhaleTransaction]:
        """Get transactions for a specific wallet."""
        query = {"wallet_address": wallet_address}
        
        if start_time or end_time:
            time_query = {}
            if start_time:
                time_query["$gte"] = start_time
            if end_time:
                time_query["$lte"] = end_time
            query["timestamp"] = time_query
        
        sort = [("timestamp", -1)]  # Sort by timestamp descending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def get_token_flow(
        self, 
        token: str,
        network: Optional[BlockchainNetwork] = None,
        lookback_days: int = 7
    ) -> Dict[str, Any]:
        """Get net flow of a token over the specified time period."""
        # Calculate start time
        start_time = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Build the match query
        match_query = {
            "token": token,
            "timestamp": {"$gte": start_time}
        }
        
        if network:
            match_query["network"] = network
        
        # Pipeline to calculate inflows and outflows
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "transaction_type": "$transaction_type"
                },
                "total_amount": {"$sum": "$amount"},
                "total_usd": {"$sum": "$usd_value"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        results = await self.aggregate(pipeline)
        
        # Process results
        daily_flows = {}
        
        for result in results:
            date = result["_id"]["date"]
            txn_type = result["_id"]["transaction_type"]
            
            if date not in daily_flows:
                daily_flows[date] = {
                    "date": date,
                    "inflow_amount": 0,
                    "outflow_amount": 0,
                    "inflow_usd": 0,
                    "outflow_usd": 0,
                    "net_amount": 0,
                    "net_usd": 0,
                    "transaction_count": 0
                }
            
            # Simplified categorization - can be made more sophisticated
            if txn_type == "transfer":
                daily_flows[date]["inflow_amount"] += result["total_amount"]
                daily_flows[date]["inflow_usd"] += result["total_usd"]
            else:
                daily_flows[date]["outflow_amount"] += result["total_amount"]
                daily_flows[date]["outflow_usd"] += result["total_usd"]
                
            daily_flows[date]["transaction_count"] += result["count"]
            daily_flows[date]["net_amount"] = daily_flows[date]["inflow_amount"] - daily_flows[date]["outflow_amount"]
            daily_flows[date]["net_usd"] = daily_flows[date]["inflow_usd"] - daily_flows[date]["outflow_usd"]
        
        # Convert to list for easier consumption
        return {
            "token": token,
            "network": network.value if network else "all",
            "period_days": lookback_days,
            "daily_flows": list(daily_flows.values())
        }
    
    async def sync_to_meilisearch(self, search_client, limit: int = 1000) -> int:
        """Sync recent whale transactions to MeiliSearch."""
        try:
            # Get recent transactions
            transactions = await self.find_many({}, limit=limit, sort=[("timestamp", -1)])
            
            if not transactions:
                logger.info("No whale transactions to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for tx in transactions:
                doc = tx.model_dump()
                
                if '_id' in doc and doc['_id']:
                    doc['id'] = doc['_id']
                    del doc['_id']
                
                # Convert datetime to ISO string
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                
                # Convert enum values to strings
                if 'network' in doc and hasattr(doc['network'], 'value'):
                    doc['network'] = doc['network'].value
                    
                if 'transaction_type' in doc and hasattr(doc['transaction_type'], 'value'):
                    doc['transaction_type'] = doc['transaction_type'].value
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('whale_transactions_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} whale transactions to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing whale transactions to MeiliSearch: {str(e)}")
            raise


class WhaleWalletRepository(BaseRepository[WhaleWallet]):
    """Repository for whale wallets."""
    
    def __init__(self):
        db = get_database()
        super().__init__(db.whale_wallets, WhaleWallet)
    
    async def get_top_whales(
        self, 
        network: Optional[BlockchainNetwork] = None,
        is_exchange: Optional[bool] = None,
        limit: int = 20
    ) -> List[WhaleWallet]:
        """Get top whale wallets by total value."""
        query = {}
        
        if network:
            query["networks"] = network
            
        if is_exchange is not None:
            query["is_exchange"] = is_exchange
        
        sort = [("total_value_usd", -1)]  # Sort by total value descending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def find_whales_by_tag(self, tag: str, limit: int = 50) -> List[WhaleWallet]:
        """Find whale wallets with a specific tag."""
        query = {"tags": tag}
        sort = [("total_value_usd", -1)]  # Sort by total value descending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def sync_to_meilisearch(self, search_client) -> int:
        """Sync all whale wallets to MeiliSearch."""
        try:
            # Get all whale wallets
            wallets = await self.find_many({})
            
            if not wallets:
                logger.info("No whale wallets to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for wallet in wallets:
                doc = wallet.model_dump()
                
                if '_id' in doc and doc['_id']:
                    doc['id'] = doc['_id']
                    del doc['_id']
                
                # Convert datetime objects to ISO strings
                if 'last_active' in doc and isinstance(doc['last_active'], datetime):
                    doc['last_active'] = doc['last_active'].isoformat()
                
                if 'first_seen' in doc and isinstance(doc['first_seen'], datetime):
                    doc['first_seen'] = doc['first_seen'].isoformat()
                
                # Convert list of enum values to strings
                if 'networks' in doc:
                    doc['networks'] = [
                        network.value if hasattr(network, 'value') else str(network) 
                        for network in doc['networks']
                    ]
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('whale_wallets_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} whale wallets to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing whale wallets to MeiliSearch: {str(e)}")
            raise


class TokenHoldingRepository(BaseRepository[TokenHolding]):
    """Repository for token holdings."""
    
    def __init__(self):
        db = get_database()
        super().__init__(db.token_holdings, TokenHolding)
    
    async def get_top_holders(
        self, 
        token: str,
        network: BlockchainNetwork,
        limit: int = 50
    ) -> List[TokenHolding]:
        """Get top holders of a token."""
        query = {"token": token, "network": network}
        sort = [("amount", -1)]  # Sort by amount descending
        
        return await self.find_many(query, limit=limit, sort=sort)
    
    async def get_wallet_holdings(
        self, 
        wallet_address: str,
        min_usd_value: Optional[float] = None
    ) -> List[TokenHolding]:
        """Get token holdings for a specific wallet."""
        query = {"wallet_address": wallet_address}
        
        if min_usd_value:
            query["usd_value"] = {"$gte": min_usd_value}
        
        sort = [("usd_value", -1)]  # Sort by USD value descending
        
        return await self.find_many(query, sort=sort)
    
    async def sync_to_meilisearch(self, search_client, limit: int = 2000) -> int:
        """Sync token holdings to MeiliSearch."""
        try:
            # Get token holdings
            holdings = await self.find_many({}, limit=limit)
            
            if not holdings:
                logger.info("No token holdings to sync to MeiliSearch")
                return 0
            
            # Process for MeiliSearch
            documents = []
            for holding in holdings:
                doc = holding.model_dump()
                
                # Create a unique ID since token holdings don't have a natural primary key
                doc['id'] = f"{doc['wallet_address']}_{doc['token']}_{doc['network'].value if hasattr(doc['network'], 'value') else doc['network']}"
                
                # Convert datetime to ISO string
                if 'last_updated' in doc and isinstance(doc['last_updated'], datetime):
                    doc['last_updated'] = doc['last_updated'].isoformat()
                
                # Convert enum values to strings
                if 'network' in doc and hasattr(doc['network'], 'value'):
                    doc['network'] = doc['network'].value
                
                documents.append(doc)
            
            # Update MeiliSearch index
            index = search_client.index('token_holdings_index')
            response = index.update_documents(documents)
            
            logger.info(f"Synced {len(documents)} token holdings to MeiliSearch")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error syncing token holdings to MeiliSearch: {str(e)}")
            raise 