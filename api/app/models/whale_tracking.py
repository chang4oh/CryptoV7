from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class BlockchainNetwork(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    BINANCE_SMART_CHAIN = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"
    SOLANA = "solana"


class TransactionType(str, Enum):
    """Types of blockchain transactions."""
    TRANSFER = "transfer"
    SWAP = "swap"
    LIQUIDITY_ADD = "liquidity_add"
    LIQUIDITY_REMOVE = "liquidity_remove"
    CONTRACT_INTERACTION = "contract_interaction"
    NFT_TRADE = "nft_trade"
    STAKING = "staking"
    OTHER = "other"


class WhaleTransaction(BaseModel):
    """Model for whale transactions."""
    id: Optional[str] = Field(None, alias="_id")
    wallet_address: str
    transaction_hash: str
    network: BlockchainNetwork
    timestamp: datetime
    transaction_type: TransactionType
    token: str  # Token symbol or address
    amount: float
    usd_value: Optional[float] = None  # USD value at transaction time
    to_address: Optional[str] = None
    gas_fee: Optional[float] = None
    block_number: int
    significant: bool = False  # Flag for particularly significant transactions
    tags: List[str] = []
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WhaleWallet(BaseModel):
    """Model for tracking whale wallets."""
    id: Optional[str] = Field(None, alias="_id")
    address: str
    name: Optional[str] = None  # Known entity name if identified
    networks: List[BlockchainNetwork]
    total_value_usd: Optional[float] = None
    last_active: Optional[datetime] = None
    first_seen: Optional[datetime] = None
    tags: List[str] = []
    is_exchange: bool = False
    is_institution: bool = False
    watch_level: int = Field(1, ge=1, le=5)  # Importance level from 1-5
    description: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TokenHolding(BaseModel):
    """Model for token holdings in a wallet."""
    wallet_address: str
    token: str
    network: BlockchainNetwork
    amount: float
    usd_value: Optional[float] = None
    last_updated: datetime
    percentage_of_supply: Optional[float] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 