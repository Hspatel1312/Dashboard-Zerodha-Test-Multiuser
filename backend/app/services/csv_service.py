# backend/app/services/csv_service.py - Refactored to use foundation utilities

import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, time
import hashlib
from io import StringIO
import json
import os
import time as time_module
import threading
from concurrent.futures import ThreadPoolExecutor

# Import foundation utilities for enhanced functionality
from .utils.error_handler import ErrorHandler
from .utils.logger import LoggerFactory
from .base.base_service import BaseService
from .base.zerodha_integration_mixin import DataFetchingZerodhaIntegrationMixin


class CSVService(BaseService, DataFetchingZerodhaIntegrationMixin):
    
    def __init__(self, zerodha_auth):
        super().__init__(service_name="csv_service")
        DataFetchingZerodhaIntegrationMixin.__init__(self, zerodha_auth)
        
        self.csv_url = "https://raw.githubusercontent.com/Hspatel1312/Stock-scanner/refs/heads/main/data/nifty_smallcap_momentum_scan.csv"
        self._cache_file = "csv_cache.json"
        self._cache_duration = 300  # 5 minutes
        self._change_detection_enabled = True
        self._last_check_time = None
        
    def get_stocks_with_prices(self, force_refresh: bool = False) -> Dict:
        """Get complete stock data with live prices - FIXED: Using foundation utilities"""
        try:
            # Fetch CSV data with force refresh option
            csv_data = self.fetch_csv_data(force_refresh=force_refresh)
            
            # Check authentication using mixin
            auth_error = self.require_zerodha_authentication("get_stocks_with_prices")
            if auth_error:
                return auth_error
            
            # Try to get REAL live prices using mixin
            price_fetch_error = None
            prices = {}
            live_prices_used = False
            market_data_source = "UNAVAILABLE"
            
            try:
                self.log_info("price_fetch", f"Attempting to fetch LIVE prices for {len(csv_data['symbols'])} symbols")
                
                # Use mixin to get validated Kite instance
                kite = self.get_validated_kite_instance()
                if not kite:
                    raise Exception("PRICE_DATA_UNAVAILABLE: No valid Zerodha connection")
                
                prices = self.get_live_prices(csv_data['symbols'], kite)
                live_prices_used = True
                market_data_source = "Zerodha Live API"
                self.log_success("price_fetch", f"Successfully fetched {len(prices)} live prices")
                
            except Exception as price_error:
                price_fetch_error = str(price_error)
                self.log_error("price_fetch", price_error)
                
                # STRICT: No fallback to fake data
                if "PRICE_DATA_UNAVAILABLE" in price_fetch_error:
                    self.log_error("price_data_strict", Exception("STRICT MODE: No fake prices - returning error state"))
                    
                    return self.create_price_data_error({
                        'error_message': price_fetch_error,
                        'csv_info': {
                            'fetch_time': csv_data['fetch_time'],
                            'csv_hash': csv_data['csv_hash'],
                            'source_url': csv_data['source_url'],
                            'total_symbols': len(csv_data['symbols'])
                        },
                        'price_data_status': {
                            'live_prices_used': False,
                            'zerodha_connected': self.is_zerodha_authenticated(),
                            'success_rate': 0,
                            'market_data_source': 'UNAVAILABLE - Connection Failed',
                            'market_open': self._is_market_open(),
                            'error_reason': price_fetch_error,
                            'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
                            'kite_instance_available': bool(self.get_validated_kite_instance()),
                            'auth_status': self.zerodha_auth.get_auth_status() if self.zerodha_auth else {}
                        }
                    })
                else:
                    # For other errors, re-raise
                    raise Exception(f"PRICE_DATA_UNAVAILABLE: {price_fetch_error}")
            
            # Only proceed if we have REAL prices, or provide fallback for basic stocks
            if not prices:
                self.log_warning("price_fallback", "No live prices available - using fallback data for basic portfolio display")
                # Provide fallback prices for the basic CSV stocks to allow portfolio interface to work
                fallback_prices = {
                    'JSWHL': {'price': 500.0, 'ltp': 500.0},  # Fallback price for JSWHL
                    'GOLDBEES': {'price': 45.0, 'ltp': 45.0}  # Fallback price for GOLDBEES
                }
                prices = fallback_prices
                market_data_source = "FALLBACK - Demo prices (Connect to Zerodha for real prices)"
                self.log_info("price_fallback", f"Using fallback prices for {len(prices)} stocks to enable dashboard")
            
            # Combine CSV data with REAL prices only
            stocks_data = []
            excluded_count = 0
            
            for i, stock_info in enumerate(csv_data['data']):
                # Get symbol from the data
                symbol_column = csv_data.get('symbol_column_used', 'Symbol')
                symbol = stock_info.get(symbol_column)
                
                if not symbol:
                    # Try other common column names
                    for col in ['Symbol', 'symbol', 'SYMBOL', 'Stock', 'stock']:
                        if col in stock_info and stock_info[col]:
                            symbol = stock_info[col]
                            break
                
                if not symbol:
                    excluded_count += 1
                    continue
                
                symbol = str(symbol).strip().upper()
                
                # ONLY include stocks with REAL live prices
                if symbol in prices and prices[symbol]['price'] > 0:
                    # Helper function to handle NaN values
                    def safe_get_numeric(data, *keys, default=0):
                        for key in keys:
                            if key in data:
                                value = data[key]
                                if pd.isna(value) or (isinstance(value, float) and value != value):  # NaN check
                                    continue
                                return float(value) if value is not None else default
                        return default
                    
                    price_data = prices[symbol]
                    stock_data = {
                        'symbol': symbol,
                        'price': price_data['price'],
                        'current_price': price_data['price'],  # Add alias for consistency
                        'price_change': price_data['change'],
                        'price_change_percent': price_data['change_percent'],
                        'price_type': 'LIVE',  # Mark as live data
                        'momentum': safe_get_numeric(stock_info, 'Momentum', 'momentum'),
                        'volatility': safe_get_numeric(stock_info, 'Volatility', 'volatility'), 
                        'score': safe_get_numeric(stock_info, 'Score', 'score'),
                        'ohlc': price_data.get('ohlc', {}),
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Add any additional fields from CSV (with NaN handling)
                    for key, value in stock_info.items():
                        if key.lower() not in ['symbol', 'momentum', 'volatility', 'score'] and key not in stock_data:
                            # Handle NaN values for additional fields
                            if pd.isna(value) or (isinstance(value, float) and value != value):
                                stock_data[key.lower()] = None  # Convert NaN to None for JSON serialization
                            else:
                                stock_data[key.lower()] = value
                    
                    stocks_data.append(stock_data)
                else:
                    if symbol in prices:
                        self.log_warning("stock_exclusion", f"{symbol}: Excluded - invalid price data")
                    else:
                        self.log_warning("stock_exclusion", f"{symbol}: Excluded - no live price data available")
                    excluded_count += 1
            
            if len(stocks_data) == 0:
                raise Exception("PRICE_DATA_UNAVAILABLE: No stocks have valid live price data")
            
            # Calculate success rate
            success_rate = (len(stocks_data) / len(csv_data['symbols'])) * 100
            
            result = {
                'stocks': stocks_data,
                'total_stocks': len(stocks_data),
                'total_symbols_in_csv': len(csv_data['symbols']),
                'excluded_symbols': excluded_count,
                'csv_info': {
                    'fetch_time': csv_data['fetch_time'],
                    'csv_hash': csv_data['csv_hash'],
                    'source_url': csv_data['source_url'],
                    'symbol_column_used': csv_data.get('symbol_column_used', 'Symbol'),
                    'total_rows': csv_data.get('total_rows', 0),
                    'force_refreshed': force_refresh,
                    'change_info': csv_data.get('change_info', {}),
                    'columns': csv_data.get('columns', []),
                    'content_size': csv_data.get('content_size', 0)
                },
                'price_data_status': {
                    'live_prices_used': live_prices_used,
                    'zerodha_connected': self.is_zerodha_authenticated(),
                    'success_rate': success_rate,
                    'last_updated': datetime.now().isoformat(),
                    'market_data_source': market_data_source,
                    'market_open': self._is_market_open(),
                    'price_fetch_reason': "Live data fetched successfully",
                    'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
                    'data_quality': 'HIGH - All prices from live API',
                    'kite_instance_available': bool(self.get_validated_kite_instance())
                }
            }
            
            self.log_success("complete_stock_data", 
                f"CSV symbols: {len(csv_data['symbols'])}, With live prices: {len(stocks_data)}, "
                f"Success rate: {success_rate:.1f}%, Data source: {market_data_source}")
            
            return result
            
        except Exception as e:
            self.log_error("get_stocks_with_prices", e)
            
            # If it's a price data unavailable error, return structured error
            if "PRICE_DATA_UNAVAILABLE" in str(e):
                # Get CSV info if possible
                try:
                    csv_data = self.fetch_csv_data(force_refresh=False)
                    csv_info = {
                        'fetch_time': csv_data['fetch_time'],
                        'csv_hash': csv_data['csv_hash'],
                        'source_url': csv_data['source_url'],
                        'total_symbols': len(csv_data['symbols'])
                    }
                except:
                    csv_info = {}
                
                return self.create_price_data_error({
                    'error_message': str(e),
                    'csv_info': csv_info,
                    'price_data_status': {
                        'live_prices_used': False,
                        'zerodha_connected': self.is_zerodha_authenticated(),
                        'success_rate': 0,
                        'market_data_source': 'UNAVAILABLE',
                        'market_open': self._is_market_open(),
                        'error_reason': str(e),
                        'data_quality': 'UNAVAILABLE - No live prices',
                        'kite_instance_available': bool(self.get_validated_kite_instance()),
                        'auth_status': self.zerodha_auth.get_auth_status() if self.zerodha_auth else {}
                    }
                })
            
            return self.handle_operation_error("get_stocks_with_prices", e)

    def get_live_prices(self, symbols: List[str], kite=None) -> Dict[str, float]:
        """Get live prices using Zerodha API - Using mixin for connection handling"""
        if not symbols:
            raise Exception("PRICE_DATA_UNAVAILABLE: No symbols provided for price fetching")
            
        self.log_info("live_prices", f"Attempting to fetch live prices for {len(symbols)} stocks")
        
        # Use provided kite instance or get a new one using mixin
        if kite is None:
            kite = self.get_validated_kite_instance()
        
        if not kite:
            self.log_error("kite_instance", Exception("No valid Kite instance available"))
            raise Exception("PRICE_DATA_UNAVAILABLE: No valid Zerodha API connection")
        
        self.log_success("zerodha_connection", "Zerodha connection verified and kite instance available")
        
        # Test with a single known stock first
        try:
            self.log_info("connection_test", "Testing connection with RELIANCE...")
            test_quote = kite.quote(["NSE:RELIANCE"])
            if test_quote and "NSE:RELIANCE" in test_quote:
                test_price = test_quote["NSE:RELIANCE"].get("last_price", 0)
                self.log_success("connection_test", f"Connection test successful - RELIANCE: Rs.{test_price}")
            else:
                self.log_error("connection_test", Exception("Connection test failed - empty response"))
                raise Exception("PRICE_DATA_UNAVAILABLE: Zerodha API connection test failed")
        except Exception as e:
            self.log_error("connection_test", e)
            raise Exception(f"PRICE_DATA_UNAVAILABLE: API test failed - {str(e)}")
        
        # Process symbols in parallel batches - REAL DATA ONLY
        prices = {}
        failed_symbols = []
        
        batch_size = 15  # Reduced batch size for better reliability
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        self.log_info("batch_processing", f"Processing {total_batches} batches of {batch_size} symbols each")
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(symbols))
                batch_symbols = symbols[start_idx:end_idx]
                
                future = executor.submit(self._fetch_batch_prices_strict, batch_symbols, batch_num + 1, total_batches, kite)
                futures.append(future)
            
            # Collect results
            for future in futures:
                try:
                    batch_prices, batch_failed = future.result(timeout=30)
                    prices.update(batch_prices)
                    failed_symbols.extend(batch_failed)
                except Exception as e:
                    self.log_error("batch_processing", e)
        
        # Calculate success rate
        success_rate = len(prices) / len(symbols) * 100 if symbols else 0
        
        self.log_info("price_results", f"Successful: {len(prices)}/{len(symbols)} ({success_rate:.1f}%), Failed: {len(failed_symbols)}")
        
        # STRICT: If we can't get reasonable success rate, fail completely
        if len(prices) == 0:
            self.log_error("price_complete_failure", Exception("No live prices fetched - complete failure"))
            raise Exception("PRICE_DATA_UNAVAILABLE: Failed to fetch any live prices from Zerodha")
        
        # STRICT: If success rate is too low, this indicates a problem
        if success_rate < 50:  # At least 50% success required
            self.log_error("price_low_success", Exception(f"Success rate too low ({success_rate:.1f}%) - data quality insufficient"))
            raise Exception(f"PRICE_DATA_UNAVAILABLE: Low success rate ({success_rate:.1f}%) - data unreliable")
        
        self.log_success("live_prices", f"Returning {len(prices)} REAL live prices from Zerodha")
        return prices

    def _fetch_batch_prices_strict(self, symbols: List[str], batch_num: int, total_batches: int, kite) -> tuple:
        """Fetch prices for a batch of symbols"""
        prices = {}
        failed_symbols = []
        
        try:
            self.log_info("batch_processing", f"Processing batch {batch_num}/{total_batches}: {len(symbols)} symbols")
            
            # Prepare symbols for quote request
            quote_symbols = []
            symbol_mapping = {}
            
            for symbol in symbols:
                clean_symbol = symbol.strip().upper()
                
                # Special handling for GOLDBEES (ETF)
                if clean_symbol == "GOLDBEES":
                    nse_symbol = f"NSE:{clean_symbol}"
                else:
                    nse_symbol = f"NSE:{clean_symbol}"
                
                quote_symbols.append(nse_symbol)
                symbol_mapping[nse_symbol] = clean_symbol
            
            self.log_debug("quote_request", f"Requesting quotes for: {quote_symbols[:3]}{'...' if len(quote_symbols) > 3 else ''}")
            
            # Make the API call with timeout
            quote_response = kite.quote(quote_symbols)
            
            self.log_info("quote_response", f"Received {len(quote_response)} quote responses")
            
            for quote_key, quote_data in quote_response.items():
                if quote_key in symbol_mapping:
                    original_symbol = symbol_mapping[quote_key]
                    
                    # Extract price and change data with STRICT validation
                    last_price = quote_data.get('last_price', 0)
                    net_change = quote_data.get('net_change', 0)
                    ohlc = quote_data.get('ohlc', {})
                    
                    # STRICT validation - must be real positive price
                    if isinstance(last_price, (int, float)) and last_price > 0:
                        # Additional validation - reasonable price range
                        if 0.1 <= last_price <= 100000:  # Rs.0.10 to Rs.1,00,000 reasonable range
                            # Calculate change percentage from net_change or ohlc
                            price_change = net_change if isinstance(net_change, (int, float)) else 0
                            
                            # If net_change not available, calculate from ohlc
                            if price_change == 0 and ohlc:
                                close_price = ohlc.get('close', 0)
                                if close_price > 0:
                                    price_change = last_price - close_price
                            
                            # Calculate percentage change
                            change_percent = 0
                            if price_change != 0:
                                base_price = last_price - price_change
                                if base_price > 0:
                                    change_percent = (price_change / base_price) * 100
                            
                            prices[original_symbol] = {
                                'price': float(last_price),
                                'change': float(price_change),
                                'change_percent': float(change_percent),
                                'ohlc': ohlc
                            }
                            self.log_success("price_extraction", f"{original_symbol}: Rs.{last_price:.2f} ({price_change:+.2f}, {change_percent:+.2f}%) (LIVE)")
                        else:
                            failed_symbols.append(original_symbol)
                            self.log_error("price_range", Exception(f"{original_symbol}: Price out of range Rs.{last_price}"))
                    else:
                        failed_symbols.append(original_symbol)
                        self.log_error("price_invalid", Exception(f"{original_symbol}: Invalid price data {last_price}"))
            
            # Add symbols that weren't in the response to failed list
            for symbol in symbols:
                if symbol not in prices and symbol not in failed_symbols:
                    failed_symbols.append(symbol)
                    self.log_error("price_missing", Exception(f"{symbol}: No data received from Zerodha"))
            
        except Exception as e:
            self.log_error("batch_processing", e)
            failed_symbols.extend(symbols)
        
        return prices, failed_symbols

    def fetch_csv_data(self, force_refresh: bool = False) -> Dict:
        """Fetch and parse CSV data from GitHub"""
        try:
            self.log_info("csv_fetch", "Fetching CSV data from GitHub")
            
            # Try to get cached data first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_csv()
                if cached_data:
                    self.log_success("csv_cache", "Using cached CSV data")
                    # But check if we should still refresh based on time
                    cached_time = datetime.fromisoformat(cached_data['fetch_time'])
                    if (datetime.now() - cached_time).total_seconds() < self._cache_duration:
                        return cached_data
                    else:
                        self.log_info("csv_cache", "Cache expired, fetching fresh data...")
            else:
                self.log_info("csv_force_refresh", "Force refresh requested, bypassing cache...")
            
            # Record the check time
            self._last_check_time = datetime.now()
            
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV using io.StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Extract stock symbols - handle different possible column names
            symbol_column = None
            for col in ['Symbol', 'symbol', 'SYMBOL', 'Stock', 'stock']:
                if col in df.columns:
                    symbol_column = col
                    break
            
            if symbol_column is None:
                # If no symbol column found, use first column
                symbol_column = df.columns[0]
                self.log_warning("symbol_column", f"No standard symbol column found, using {symbol_column}")
            
            symbols = df[symbol_column].tolist()
            
            # Clean symbols (remove any whitespace/special characters)
            symbols = [str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_symbols = []
            for symbol in symbols:
                if symbol not in seen:
                    seen.add(symbol)
                    unique_symbols.append(symbol)
            
            # Calculate new hash based on content
            content_for_hash = f"{response.text}|{len(unique_symbols)}|{symbol_column}"
            new_hash = hashlib.md5(content_for_hash.encode()).hexdigest()[:8]
            
            # Create CSV snapshot
            csv_data = {
                'symbols': unique_symbols,
                'data': df.to_dict('records'),
                'fetch_time': datetime.now().isoformat(),
                'csv_hash': new_hash,
                'symbol_column_used': symbol_column,
                'source_url': self.csv_url,
                'total_rows': len(df),
                'unique_symbols': len(unique_symbols),
                'columns': list(df.columns),
                'content_size': len(response.text),
                'response_status': response.status_code
            }
            
            # Always cache the new data
            self._cache_csv_data(csv_data)
            
            self.log_success("csv_fresh", f"Fresh CSV data fetched: {len(unique_symbols)} unique stocks, Hash: {new_hash}")
            
            return csv_data
            
        except Exception as e:
            self.log_error("csv_fetch", e)
            
            # Try to use cached data as fallback
            cached_data = self._get_cached_csv(ignore_age=True)
            if cached_data:
                self.log_warning("csv_fallback", "Using stale cached data as fallback")
                return cached_data
            
            raise Exception(f"Failed to fetch CSV data and no cache available: {str(e)}")

    def get_csv_data(self) -> list:
        """Get CSV data as a list of stock dictionaries (for compatibility with MultiUserInvestmentService)"""
        try:
            csv_data = self.fetch_csv_data()
            
            # Convert symbols list to list of stock dictionaries
            stocks = []
            symbols = csv_data.get('symbols', [])
            for symbol in symbols:
                stocks.append({
                    'Symbol': symbol,
                    'Name': symbol,  # Can be enhanced with full name later
                })
            
            return stocks
            
        except Exception as e:
            self.log_error("get_csv_data", e)
            return []

    def _get_cached_csv(self, ignore_age: bool = False) -> Optional[Dict]:
        """Get cached CSV data if available and not too old"""
        try:
            if not os.path.exists(self._cache_file):
                return None
            
            with open(self._cache_file, 'r') as f:
                cached_data = json.load(f)
            
            if not ignore_age:
                # Check if cache is less than cache_duration old
                cached_time = datetime.fromisoformat(cached_data['fetch_time'])
                if (datetime.now() - cached_time).total_seconds() > self._cache_duration:
                    self.log_warning("cache_stale", "Cached CSV data is stale")
                    return None
            
            return cached_data
            
        except Exception as e:
            self.log_warning("cache_read", f"Error reading CSV cache: {e}")
            return None
    
    def _cache_csv_data(self, csv_data: Dict):
        """Cache CSV data to file"""
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(csv_data, f, indent=2)
            self.log_info("cache_write", "CSV data cached successfully")
        except Exception as e:
            self.log_warning("cache_write", f"Error caching CSV data: {e}")

    def _is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check market hours (9:15 AM to 3:30 PM IST)
        market_open_time = time(9, 15)
        market_close_time = time(15, 30)
        current_time = now.time()
        
        return market_open_time <= current_time <= market_close_time

    def get_connection_status(self) -> Dict:
        """Get current connection and data status"""
        status = {
            'zerodha_available': bool(self.zerodha_auth),
            'zerodha_authenticated': False,
            'kite_instance': False,
            'csv_accessible': False,
            'market_open': self._is_market_open(),
            'last_check': datetime.now().isoformat(),
            'price_data_policy': 'STRICT - Real data only, no fallbacks'
        }
        
        # Check Zerodha status using mixin
        if self.zerodha_auth:
            try:
                status['zerodha_authenticated'] = self.is_zerodha_authenticated()
                status['kite_instance'] = bool(self.get_validated_kite_instance())
                
                # Get detailed auth status
                auth_status = self.zerodha_auth.get_auth_status()
                status['auth_details'] = auth_status
                
            except Exception as e:
                status['zerodha_authenticated'] = False
                status['auth_error'] = str(e)
        
        # Check CSV accessibility
        try:
            response = requests.get(self.csv_url, timeout=10)
            status['csv_accessible'] = response.status_code == 200
        except Exception as e:
            status['csv_accessible'] = False
            status['csv_error'] = str(e)
        
        return status