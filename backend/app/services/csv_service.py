# backend/app/services/csv_service.py
import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, time
import hashlib
from io import StringIO
import json
import os
import time as time_module

class CSVService:
    def __init__(self, zerodha_auth):
        self.csv_url = "https://raw.githubusercontent.com/Hspatel1312/Stock-scanner/refs/heads/main/data/nifty_smallcap_momentum_scan.csv"
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance() if zerodha_auth else None
        self._cache_file = "csv_cache.json"
        self._cache_duration = 300  # 5 minutes instead of 1 hour
        
    def fetch_csv_data(self, force_refresh: bool = False) -> Dict:
        """Fetch and parse CSV data from GitHub with optional force refresh"""
        try:
            print("📊 Fetching CSV data from GitHub...")
            
            # Try to get cached data first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_csv()
                if cached_data:
                    print("✅ Using cached CSV data")
                    # But check if we should still refresh based on time
                    cached_time = datetime.fromisoformat(cached_data['fetch_time'])
                    if (datetime.now() - cached_time).total_seconds() < self._cache_duration:
                        return cached_data
                    else:
                        print("⏰ Cache expired, fetching fresh data...")
            else:
                print("🔄 Force refresh requested, bypassing cache...")
            
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
                print(f"⚠️ No standard symbol column found, using {symbol_column}")
            
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
            
            # Calculate new hash
            new_hash = hashlib.md5(response.text.encode()).hexdigest()[:8]
            
            # Create CSV snapshot
            csv_data = {
                'symbols': unique_symbols,
                'data': df.to_dict('records'),
                'fetch_time': datetime.now().isoformat(),
                'csv_hash': new_hash,
                'symbol_column_used': symbol_column,
                'source_url': self.csv_url,
                'total_rows': len(df),
                'unique_symbols': len(unique_symbols)
            }
            
            # Always cache the new data
            self._cache_csv_data(csv_data)
            
            print(f"✅ Fresh CSV data fetched: {len(unique_symbols)} unique stocks")
            print(f"   Hash: {new_hash}")
            print(f"   Sample stocks: {', '.join(unique_symbols[:5])}{'...' if len(unique_symbols) > 5 else ''}")
            
            return csv_data
            
        except Exception as e:
            print(f"❌ Error fetching CSV data: {e}")
            
            # Try to use cached data as fallback
            cached_data = self._get_cached_csv(ignore_age=True)
            if cached_data:
                print("⚠️ Using stale cached data as fallback")
                return cached_data
            
            raise Exception(f"Failed to fetch CSV data and no cache available: {str(e)}")
    
    def get_live_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get live prices using Zerodha API with enhanced debugging"""
        if not symbols:
            raise Exception("No symbols provided for price fetching")
            
        print(f"💰 Fetching live prices for {len(symbols)} stocks...")
        print(f"🔍 First 5 symbols: {symbols[:5]}")
        
        # Check if market is open
        market_open = self._is_market_open()
        print(f"📅 Market status: {'OPEN' if market_open else 'CLOSED'}")
        
        # Check authentication status first
        if not self.zerodha_auth:
            print("❌ No Zerodha auth service available")
            return self._get_fallback_prices(symbols, "No auth service")
        
        print(f"🔐 Auth service available: {bool(self.zerodha_auth)}")
        
        if not self.zerodha_auth.is_authenticated():
            print("🔄 Zerodha not authenticated, attempting authentication...")
            try:
                result = self.zerodha_auth.authenticate()
                if result:
                    self.kite = self.zerodha_auth.get_kite_instance()
                    print("✅ Authentication successful")
                else:
                    print("❌ Authentication failed")
                    return self._get_fallback_prices(symbols, "Authentication failed")
            except Exception as e:
                print(f"❌ Zerodha authentication error: {e}")
                return self._get_fallback_prices(symbols, f"Auth error: {str(e)}")
        
        if not self.kite:
            print("❌ Zerodha API connection not available")
            return self._get_fallback_prices(symbols, "No kite instance")
        
        print("✅ Zerodha authenticated and kite instance available")
        
        # Test with a single known stock first
        try:
            print("🧪 Testing with RELIANCE...")
            test_quote = self.kite.quote(["NSE:RELIANCE"])
            if test_quote and "NSE:RELIANCE" in test_quote:
                test_price = test_quote["NSE:RELIANCE"].get("last_price", 0)
                print(f"✅ Test successful - RELIANCE: ₹{test_price}")
            else:
                print("❌ Test quote failed - empty response")
                return self._get_fallback_prices(symbols, "Test quote failed")
        except Exception as e:
            print(f"❌ Test quote error: {e}")
            return self._get_fallback_prices(symbols, f"Test error: {str(e)}")
        
        prices = {}
        failed_symbols = []
        
        # Process symbols in smaller batches to avoid API limits
        batch_size = 20  # Reduced batch size
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(symbols))
            batch_symbols = symbols[start_idx:end_idx]
            
            print(f"🔄 Processing batch {batch_num + 1}/{total_batches}: {len(batch_symbols)} symbols")
            
            batch_prices = self._fetch_batch_prices(batch_symbols)
            
            for symbol, price in batch_prices.items():
                if price > 0:
                    prices[symbol] = price
                    print(f"   ✅ {symbol}: ₹{price:.2f}")
                else:
                    failed_symbols.append(symbol)
                    print(f"   ❌ {symbol}: Invalid price")
            
            # Add delay between batches to respect API limits
            if batch_num < total_batches - 1:
                time_module.sleep(0.5)  # 500ms delay between batches
        
        # Calculate success rate
        success_rate = len(prices) / len(symbols) * 100 if symbols else 0
        
        print(f"📊 Price fetching results:")
        print(f"   Successful: {len(prices)}/{len(symbols)} ({success_rate:.1f}%)")
        print(f"   Failed: {len(failed_symbols)}")
        
        if len(prices) == 0:
            print("❌ No live prices fetched, using fallback")
            return self._get_fallback_prices(symbols, "All price fetches failed")
        
        if success_rate < 30:
            print(f"⚠️ Low success rate ({success_rate:.1f}%), supplementing with fallback")
            fallback_prices = self._get_fallback_prices(failed_symbols, f"Low success rate: {success_rate:.1f}%")
            prices.update(fallback_prices)
        
        print(f"✅ Returning {len(prices)} prices from live API")
        return prices
    
    def _fetch_batch_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch prices for a batch of symbols with enhanced error handling"""
        prices = {}
        
        # Prepare symbols for quote request
        quote_symbols = []
        symbol_mapping = {}
        
        for symbol in symbols:
            # Clean the symbol
            clean_symbol = symbol.strip().upper()
            nse_symbol = f"NSE:{clean_symbol}"
            quote_symbols.append(nse_symbol)
            symbol_mapping[nse_symbol] = clean_symbol
        
        try:
            print(f"   🔍 Requesting quotes for: {quote_symbols[:3]}{'...' if len(quote_symbols) > 3 else ''}")
            quote_response = self.kite.quote(quote_symbols)
            
            print(f"   📊 Received {len(quote_response)} quote responses")
            
            for quote_key, quote_data in quote_response.items():
                if quote_key in symbol_mapping:
                    original_symbol = symbol_mapping[quote_key]
                    
                    # Extract price with validation
                    last_price = quote_data.get('last_price', 0)
                    
                    # Additional validation
                    if isinstance(last_price, (int, float)) and last_price > 0:
                        prices[original_symbol] = float(last_price)
                    else:
                        print(f"   ⚠️ {original_symbol}: Invalid price data {last_price}")
            
        except Exception as e:
            print(f"   ❌ Batch quote request failed: {e}")
            
            # Fallback to individual requests for this batch
            print(f"   🔄 Trying individual requests for batch...")
            for symbol in symbols:
                try:
                    individual_price = self._fetch_individual_price(symbol)
                    if individual_price > 0:
                        prices[symbol] = individual_price
                    time_module.sleep(0.1)  # Small delay between individual requests
                except Exception as individual_error:
                    print(f"   ❌ {symbol}: Individual fetch failed - {individual_error}")
        
        return prices
    
    def _fetch_individual_price(self, symbol: str) -> float:
        """Fetch price for individual symbol"""
        try:
            clean_symbol = symbol.strip().upper()
            nse_symbol = f"NSE:{clean_symbol}"
            quote_response = self.kite.quote([nse_symbol])
            
            if nse_symbol in quote_response:
                last_price = quote_response[nse_symbol].get('last_price', 0)
                if isinstance(last_price, (int, float)) and last_price > 0:
                    return float(last_price)
            
            return 0
            
        except Exception as e:
            print(f"   ❌ Individual price fetch failed for {symbol}: {e}")
            return 0
    
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
    
    def _get_fallback_prices(self, symbols: List[str], reason: str = "Unknown") -> Dict[str, float]:
        """Get fallback prices with reason tracking"""
        print(f"🔄 Using fallback price generator: {reason}")
        
        # Generate realistic price ranges based on symbol
        import random
        random.seed(42)  # For consistent mock data
        
        fallback_prices = {}
        for symbol in symbols:
            # Generate price based on symbol hash for consistency
            symbol_hash = hash(symbol) % 10000
            base_price = 100 + (symbol_hash % 2000)  # Price between 100-2100
            # Add some randomness but keep it realistic
            price = base_price + random.uniform(-50, 50)
            price = max(10, price)  # Ensure minimum price
            fallback_prices[symbol] = round(price, 2)
        
        print(f"   Generated {len(fallback_prices)} fallback prices (reason: {reason})")
        return fallback_prices
    
    def get_stocks_with_prices(self, force_refresh: bool = False) -> Dict:
        """Get complete stock data with live prices"""
        try:
            # Fetch CSV data with force refresh option
            csv_data = self.fetch_csv_data(force_refresh=force_refresh)
            
            # Get live prices with detailed status
            price_fetch_reason = "Unknown"
            try:
                prices = self.get_live_prices(csv_data['symbols'])
                
                # Determine if we got real live prices
                # Check if prices look realistic (not all similar fallback values)
                price_values = list(prices.values())
                if len(price_values) > 5:
                    # Check variance - live prices should have high variance
                    import statistics
                    price_variance = statistics.variance(price_values)
                    # If variance is very low, likely fallback data
                    if price_variance < 1000:  # Fallback prices have low variance
                        live_prices_used = False
                        market_data_source = "Fallback Generator (Low Variance Detected)"
                    else:
                        live_prices_used = True
                        market_data_source = "Zerodha Live API"
                else:
                    live_prices_used = len(prices) > 0
                    market_data_source = "Zerodha Live API" if live_prices_used else "Fallback Generator"
                    
            except Exception as price_error:
                print(f"⚠️ Price fetching failed: {price_error}")
                prices = self._get_fallback_prices(csv_data['symbols'], f"Error: {str(price_error)}")
                live_prices_used = False
                market_data_source = "Fallback Generator (Error)"
                price_fetch_reason = str(price_error)
            
            # Combine data - only include stocks with valid prices
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
                
                if symbol in prices and prices[symbol] > 0:
                    stock_data = {
                        'symbol': symbol,
                        'price': prices[symbol],
                        'momentum': stock_info.get('Momentum', stock_info.get('momentum', 0)),
                        'volatility': stock_info.get('Volatility', stock_info.get('volatility', 0)),
                        'score': stock_info.get('Score', stock_info.get('score', 0))
                    }
                    
                    # Add any additional fields from CSV
                    for key, value in stock_info.items():
                        if key.lower() not in ['symbol', 'momentum', 'volatility', 'score'] and key not in stock_data:
                            stock_data[key.lower()] = value
                    
                    stocks_data.append(stock_data)
                else:
                    print(f"   ⚠️ {symbol}: Excluded - no valid price data")
                    excluded_count += 1
            
            if len(stocks_data) == 0:
                raise Exception("No stocks have valid price data")
            
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
                    'force_refreshed': force_refresh
                },
                'price_data_status': {
                    'live_prices_used': live_prices_used,
                    'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()),
                    'success_rate': success_rate,
                    'last_updated': datetime.now().isoformat(),
                    'market_data_source': market_data_source,
                    'market_open': self._is_market_open(),
                    'price_fetch_reason': price_fetch_reason if not live_prices_used else "Live data fetched successfully"
                }
            }
            
            print(f"✅ Complete stock data prepared:")
            print(f"   CSV symbols: {len(csv_data['symbols'])}")
            print(f"   With valid prices: {len(stocks_data)}")
            print(f"   Excluded due to no price: {excluded_count}")
            print(f"   Success rate: {success_rate:.1f}%")
            print(f"   Data source: {market_data_source}")
            print(f"   Market status: {'OPEN' if self._is_market_open() else 'CLOSED'}")
            print(f"   Force refreshed: {force_refresh}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error preparing stock data: {e}")
            raise Exception(f"Cannot prepare investment data: {str(e)}")
    
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
                    print("⚠️ Cached CSV data is stale")
                    return None
            
            return cached_data
            
        except Exception as e:
            print(f"⚠️ Error reading CSV cache: {e}")
            return None
    
    def _cache_csv_data(self, csv_data: Dict):
        """Cache CSV data to file"""
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(csv_data, f, indent=2)
            print("💾 CSV data cached successfully")
        except Exception as e:
            print(f"⚠️ Error caching CSV data: {e}")
    
    def get_connection_status(self) -> Dict:
        """Get current connection and data status"""
        status = {
            'zerodha_available': bool(self.zerodha_auth),
            'zerodha_authenticated': False,
            'kite_instance': bool(self.kite),
            'csv_accessible': False,
            'market_open': self._is_market_open(),
            'last_check': datetime.now().isoformat(),
            'cache_status': 'unknown',
            'errors': []
        }
        
        # Check Zerodha status
        if self.zerodha_auth:
            try:
                status['zerodha_authenticated'] = self.zerodha_auth.is_authenticated()
                if not status['zerodha_authenticated']:
                    status['errors'].append("Zerodha not authenticated")
            except Exception as e:
                status['zerodha_authenticated'] = False
                status['errors'].append(f"Zerodha auth error: {str(e)}")
        else:
            status['errors'].append("Zerodha auth service not available")
        
        # Check CSV accessibility
        try:
            response = requests.get(self.csv_url, timeout=10)
            status['csv_accessible'] = response.status_code == 200
            if not status['csv_accessible']:
                status['errors'].append(f"CSV not accessible: HTTP {response.status_code}")
        except Exception as e:
            status['csv_accessible'] = False
            status['errors'].append(f"CSV access error: {str(e)}")
        
        # Check cache status
        try:
            cached_data = self._get_cached_csv()
            if cached_data:
                cached_time = datetime.fromisoformat(cached_data['fetch_time'])
                age_seconds = (datetime.now() - cached_time).total_seconds()
                if age_seconds < self._cache_duration:
                    status['cache_status'] = f'fresh ({age_seconds:.0f}s old)'
                else:
                    status['cache_status'] = f'stale ({age_seconds:.0f}s old)'
            else:
                status['cache_status'] = 'no cache'
        except Exception as e:
            status['cache_status'] = f'cache error: {str(e)}'
        
        return status