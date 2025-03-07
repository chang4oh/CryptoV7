import requests
import hmac
import hashlib
import time
import urllib.parse
import logging
import re
from app.core.config import settings
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BinanceService:
    """Service for interacting with Binance Testnet API."""
    
    def __init__(self):
        self.api_key = settings.BINANCE_TESTNET_API_KEY
        self.api_secret = settings.BINANCE_TESTNET_SECRET_KEY
        self.base_url = settings.BINANCE_TESTNET_BASE_URL
        self._symbol_info_cache = {}
        self._last_cache_update = 0
        self._cache_ttl = 300  # 5 minutes in seconds
    
    def _generate_signature(self, params: dict) -> str:
        """Generate HMAC SHA256 signature for Binance API."""
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Validate symbol format."""
        return bool(re.match(r'^[A-Z0-9]{2,}$', symbol))
    
    def _should_update_cache(self) -> bool:
        """Check if the symbol info cache should be updated."""
        current_time = time.time()
        return current_time - self._last_cache_update > self._cache_ttl
    
    def get_exchange_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get exchange information.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
        """
        # Return cached data if available and not expired
        if self._symbol_info_cache and not self._should_update_cache() and not force_refresh:
            logger.info("Using cached exchange info")
            return self._symbol_info_cache
            
        endpoint = "/v3/exchangeInfo"
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Cache the response
            self._symbol_info_cache = response.json()
            self._last_cache_update = time.time()
            
            return self._symbol_info_cache
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting exchange info: {e}")
            return {"error": f"HTTP error: {e}"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error getting exchange info: {e}")
            return {"error": "Connection error, please check your internet connection"}
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error getting exchange info: {e}")
            return {"error": "Request timed out, please try again later"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting exchange info: {e}")
            return {"error": f"Request error: {e}"}
        except Exception as e:
            logger.error(f"Error getting exchange info: {e}")
            return {"error": str(e)}
    
    def get_ticker_price(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get current price for a symbol."""
        if not self._validate_symbol(symbol):
            return {"error": f"Invalid symbol format: {symbol}"}
            
        endpoint = "/v3/ticker/price"
        url = f"{self.base_url}{endpoint}"
        
        params = {"symbol": symbol}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                # Try to parse the error message
                try:
                    error_data = response.json()
                    if "msg" in error_data:
                        return {"error": error_data["msg"]}
                except:
                    pass
            logger.error(f"HTTP error getting ticker price for {symbol}: {e}")
            return {"error": f"HTTP error: {e}"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error getting ticker price for {symbol}: {e}")
            return {"error": "Connection error, please check your internet connection"}
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error getting ticker price for {symbol}: {e}")
            return {"error": "Request timed out, please try again later"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting ticker price for {symbol}: {e}")
            return {"error": f"Request error: {e}"}
        except Exception as e:
            logger.error(f"Error getting ticker price for {symbol}: {e}")
            return {"error": str(e)}
    
    def get_all_tickers(self) -> Dict[str, Any]:
        """Get prices for all symbols."""
        endpoint = "/v3/ticker/price"
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Convert list of tickers to a dictionary for easier access
            tickers = response.json()
            result = {}
            
            if isinstance(tickers, list):
                for ticker in tickers:
                    if "symbol" in ticker and "price" in ticker:
                        result[ticker["symbol"]] = ticker
            
            return {"tickers": result}
        except Exception as e:
            logger.error(f"Error getting all tickers: {e}")
            return {"error": str(e)}
    
    def get_crypto_list(self, quote_asset: str = "USDT") -> Dict[str, Any]:
        """
        Get a list of cryptocurrencies for a specific quote asset.
        
        Args:
            quote_asset: The quote asset to filter by (e.g., USDT, BTC)
        """
        # Get exchange info
        exchange_info = self.get_exchange_info()
        
        if "error" in exchange_info:
            return exchange_info
        
        if "symbols" not in exchange_info:
            return {"error": "Failed to retrieve symbols from exchange"}
        
        # Get all tickers for prices
        all_tickers = self.get_all_tickers()
        ticker_dict = all_tickers.get("tickers", {}) if "error" not in all_tickers else {}
        
        # Filter symbols by quote asset and status
        crypto_list = []
        for symbol_info in exchange_info["symbols"]:
            if (symbol_info.get("quoteAsset") == quote_asset and 
                symbol_info.get("status") == "TRADING"):
                
                base_asset = symbol_info.get("baseAsset", "")
                symbol = symbol_info.get("symbol", "")
                
                # Get price from tickers
                price = None
                if symbol in ticker_dict:
                    price = ticker_dict[symbol].get("price")
                
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
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information (requires authentication)."""
        if not self.api_key or not self.api_secret:
            return {"error": "API key and secret are required"}
            
        endpoint = "/v3/account"
        params = {
            "timestamp": self._get_timestamp()
        }
        signature = self._generate_signature(params)
        params["signature"] = signature
        
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return {"error": "Invalid API-key, IP, or permissions for action"}
            try:
                error_data = response.json()
                if "msg" in error_data:
                    return {"error": error_data["msg"]}
            except:
                pass
            logger.error(f"HTTP error getting account info: {e}")
            return {"error": f"HTTP error: {e}"}
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"error": str(e)}
    
    def get_open_orders(self, symbol: str = None) -> Dict[str, Any]:
        """Get open orders (requires authentication)."""
        if not self.api_key or not self.api_secret:
            return {"error": "API key and secret are required"}
            
        if symbol and not self._validate_symbol(symbol):
            return {"error": f"Invalid symbol format: {symbol}"}
            
        endpoint = "/v3/openOrders"
        params = {
            "timestamp": self._get_timestamp()
        }
        
        if symbol:
            params["symbol"] = symbol
            
        signature = self._generate_signature(params)
        params["signature"] = signature
        
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return {"error": "Invalid API-key, IP, or permissions for action"}
            try:
                error_data = response.json()
                if "msg" in error_data:
                    return {"error": error_data["msg"]}
            except:
                pass
            logger.error(f"HTTP error getting open orders: {e}")
            return {"error": f"HTTP error: {e}"}
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return {"error": str(e)}

# Create a singleton instance
binance_service = BinanceService() 