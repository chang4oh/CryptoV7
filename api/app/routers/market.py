from fastapi import APIRouter, Query, HTTPException, Path, Depends
from typing import List, Optional, Dict, Any
from app.services.binance_service import binance_service
import logging
import re

router = APIRouter(prefix="/market", tags=["market"])
logger = logging.getLogger(__name__)

def validate_symbol(symbol: str) -> str:
    """Validate the symbol format."""
    # Basic validation for Binance symbols
    if not re.match(r'^[A-Z0-9]{2,}$', symbol):
        raise HTTPException(
            status_code=422, 
            detail=f"Invalid symbol format: {symbol}. Symbol should contain only uppercase letters and numbers."
        )
    return symbol

@router.get("/price/{symbol}")
async def get_price(symbol: str = Path(..., example="BTCUSDT", description="Trading pair symbol (e.g., BTCUSDT)")):
    """Get current price for a symbol."""
    try:
        # Validate symbol format
        symbol = validate_symbol(symbol)
        
        price_data = binance_service.get_ticker_price(symbol)
        
        if "error" in price_data:
            if "Unknown symbol" in price_data["error"]:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Symbol not found: {symbol}"
                )
            else:
                raise HTTPException(status_code=400, detail=price_data["error"])
            
        return price_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prices")
async def get_multiple_prices(symbols: str = Query(..., description="Comma-separated list of symbols (e.g., BTCUSDT,ETHUSDT)")):
    """Get prices for multiple symbols at once."""
    try:
        # Split and validate symbols
        symbol_list = [s.strip() for s in symbols.split(",")]
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
            
        results = {}
        errors = []
        
        # Get prices for each symbol
        for symbol in symbol_list:
            try:
                # Validate symbol format
                symbol = validate_symbol(symbol)
                price_data = binance_service.get_ticker_price(symbol)
                
                if "error" in price_data:
                    errors.append({"symbol": symbol, "error": price_data["error"]})
                else:
                    results[symbol] = price_data
            except Exception as e:
                errors.append({"symbol": symbol, "error": str(e)})
        
        return {
            "prices": results,
            "errors": errors if errors else None
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting multiple prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exchange-info")
async def get_exchange_info(symbol: Optional[str] = None):
    """Get exchange information."""
    try:
        # Validate symbol if provided
        if symbol:
            symbol = validate_symbol(symbol)
            
        exchange_info = binance_service.get_exchange_info()
        
        if "error" in exchange_info:
            raise HTTPException(status_code=400, detail=exchange_info["error"])
        
        # If symbol is provided, filter the results
        if symbol and "symbols" in exchange_info:
            filtered_symbols = [s for s in exchange_info["symbols"] if s["symbol"] == symbol]
            if filtered_symbols:
                return {"symbols": filtered_symbols}
            else:
                raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
            
        return exchange_info
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting exchange info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crypto-list")
async def get_crypto_list(quote_asset: str = Query("USDT", description="Quote asset (e.g., USDT, BTC)")):
    """Get a list of available cryptocurrencies for a specific quote asset."""
    try:
        exchange_info = binance_service.get_exchange_info()
        
        if "error" in exchange_info:
            raise HTTPException(status_code=400, detail=exchange_info["error"])
        
        if "symbols" not in exchange_info:
            raise HTTPException(status_code=500, detail="Failed to retrieve symbols from exchange")
        
        # Filter symbols by quote asset and status
        crypto_list = []
        for symbol_info in exchange_info["symbols"]:
            if (symbol_info.get("quoteAsset") == quote_asset and 
                symbol_info.get("status") == "TRADING"):
                
                base_asset = symbol_info.get("baseAsset", "")
                symbol = symbol_info.get("symbol", "")
                
                # Get current price
                try:
                    price_data = binance_service.get_ticker_price(symbol)
                    price = price_data.get("price") if "error" not in price_data else None
                except:
                    price = None
                
                crypto_list.append({
                    "symbol": symbol,
                    "baseAsset": base_asset,
                    "quoteAsset": quote_asset,
                    "price": price
                })
        
        return {
            "quote_asset": quote_asset,
            "count": len(crypto_list),
            "cryptocurrencies": crypto_list
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting crypto list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account")
async def get_account_info():
    """Get account information (requires authentication)."""
    try:
        account_info = binance_service.get_account_info()
        
        if "error" in account_info:
            # Check for specific error types
            if "Invalid API-key" in account_info["error"]:
                raise HTTPException(status_code=401, detail="Invalid API key")
            else:
                raise HTTPException(status_code=400, detail=account_info["error"])
            
        return account_info
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/open-orders")
async def get_open_orders(symbol: Optional[str] = None):
    """Get open orders (requires authentication)."""
    try:
        # Validate symbol if provided
        if symbol:
            symbol = validate_symbol(symbol)
            
        open_orders = binance_service.get_open_orders(symbol)
        
        if "error" in open_orders:
            # Check for specific error types
            if "Invalid API-key" in open_orders["error"]:
                raise HTTPException(status_code=401, detail="Invalid API key")
            else:
                raise HTTPException(status_code=400, detail=open_orders["error"])
            
        return open_orders
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting open orders: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 