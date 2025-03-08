from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MarketData(BaseModel):
    """Market data model for price information."""
    id: Optional[str] = Field(None, alias="_id")
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: Optional[float] = None
    trades: Optional[int] = None
    interval: str  # e.g., "1m", "5m", "1h", "1d"
    source: str    # e.g., "binance", "kucoin", etc.
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderBookLevel(BaseModel):
    """Single price level in an order book."""
    price: float
    quantity: float


class OrderBook(BaseModel):
    """Order book model representing market depth."""
    id: Optional[str] = Field(None, alias="_id")
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    source: str
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LiquidityZone(BaseModel):
    """Model representing liquidity zones for analysis."""
    id: Optional[str] = Field(None, alias="_id")
    symbol: str
    start_time: datetime
    end_time: datetime
    price_low: float
    price_high: float
    avg_bid_volume: float
    avg_ask_volume: float
    strength: float  # Calculated metric for zone strength
    tags: List[str] = []
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 