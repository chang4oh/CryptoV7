from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from enum import Enum


class SignalType(str, Enum):
    """Types of trading signals."""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class SignalSource(str, Enum):
    """Source of trading signals."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    AI = "ai"
    CUSTOM = "custom"


class TradeSignal(BaseModel):
    """Model for trading signals."""
    id: Optional[str] = Field(None, alias="_id")
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    source: SignalSource
    strategy: str
    price: float
    confidence: float = Field(ge=0.0, le=1.0)  # Confidence level between 0 and 1
    indicators: Dict[str, Any] = {}  # Flexible structure for various indicators
    timeframe: str  # e.g., "1m", "5m", "1h", "1d"
    tags: List[str] = []
    description: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyPerformance(BaseModel):
    """Model for strategy performance metrics."""
    id: Optional[str] = Field(None, alias="_id")
    strategy: str
    symbol: Optional[str] = None  # Can be None for all symbols
    start_date: datetime
    end_date: datetime
    total_signals: int
    win_count: int
    loss_count: int
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    timeframe: str
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.total_signals == 0:
            return 0.0
        return self.win_count / self.total_signals
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 