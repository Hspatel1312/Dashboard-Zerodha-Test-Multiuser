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
import threading
from concurrent.futures import ThreadPoolExecutor

class CSVService:
    def __init__(self, zerodha_auth):
        self.csv_url = "https://raw.githubusercontent.com/Hspatel1312/Stock-scanner/refs/heads/main/data/nifty_smallcap_momentum_scan.csv"
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance() if zerodha_auth else None
        self._cache_file = "csv_cache.json"
        self._cache_duration = 300  # 5 minutes
        self._change_detection_enabled = True
        self._last_check_time = None
        
    def fetch_csv_data(self, force_refresh: bool = False) -> Dict:
        """Fetch and parse CSV data from GitHub with enhanced change detection"""
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
            
            # Calculate new hash based on content
            content_for_hash = f"{response.text}|{len(unique_symbols)}|{symbol_column}"
            new_hash = hashlib.md5(content_for_hash.encode()).hexdigest()[:8]
            
            # Create CSV snapshot with enhanced metadata
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
                'response_status': response.status_code,
                'change_detection_enabled': self._change_detection_enabled
            }
            
            # Detect changes by comparing with cached data
            change_info = self._detect_changes(cached_data if not force_refresh else None, csv_data)
            csv_data['change_info'] = change_info
            
            # Always cache the new data
            self._cache_csv_data(csv_data)
            
            print(f"✅ Fresh CSV data fetched: {len(unique_symbols)} unique stocks")
            print(f"   Hash: {new_hash}")
            print(f"   Changes detected: {change_info['has_changes']}")
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
    
    def _detect_changes(self, old_data: Optional[Dict], new_data: Dict) -> Dict:
        """Detect changes between old and new CSV data"""
        if not old_data:
            return {
                'has_changes': True,
                'change_type': 'initial_fetch',
                'summary': 'Initial CSV data fetch',
                'details': {}
            }
        
        old_symbols = set(old_data.get('symbols', []))
        new_symbols = set(new_data.get('symbols', []))
        
        added_symbols = new_symbols - old_symbols
        removed_symbols = old_symbols - new_symbols
        
        # Check hash change
        hash_changed = old_data.get('csv_hash') != new_data.get('csv_hash')
        
        # Check content changes
        content_size_changed = old_data.get('content_size', 0) != new_data.get('content_size', 0)
        column_changes = set(old_data.get('columns', [])) != set(new_data.get('columns', []))
        
        has_changes = bool(added_symbols or removed_symbols or hash_changed or content_size_changed or column_changes)
        
        change_info = {
            'has_changes': has_changes,
            'change_type': self._determine_change_type(added_symbols, removed_symbols, hash_changed),
            'summary': self._create_change_summary(added_symbols, removed_symbols, hash_changed),
            'details': {
                'hash_changed': hash_changed,
                'old_hash': old_data.get('csv_hash'),
                'new_hash': new_data.get('csv_hash'),
                'symbols_added': list(added_symbols),
                'symbols_removed': list(removed_symbols),
                'total_symbols_change': len(new_symbols) - len(old_symbols),
                'content_size_change': new_data.get('content_size', 0) - old_data.get('content_size', 0),
                'column_changes': column_changes,
                'fetch_time_old': old_data.get('fetch_time'),
                'fetch_time_new': new_data.get('fetch_time')
            }
        }
        
        return change_info
    
    def _determine_change_type(self, added: set, removed: set, hash_changed: bool) -> str:
        """Determine the type of change detected"""
        if added and removed:
            return 'symbols_modified'
        elif added:
            return 'symbols_added'
        elif removed:
            return 'symbols_removed'
        elif hash_changed:
            return 'content_updated'
        else:
            return 'no_change'
    
    def _create_change_summary(self, added: set, removed: set, hash_changed: bool) -> str:
        """Create a human-readable summary of changes"""
        if not (added or removed or hash_changed):
            return 'No changes detected'
        
        summary_parts = []
        
        if added:
            summary_parts.append(f"{len(added)} symbol(s) added")
        
        if removed:
            summary_parts.append(f"{len(removed)} symbol(s) removed")
        
        if hash_changed and not (added or removed):
            summary_parts.append("Content updated")
        
        return ', '.join(summary_parts)
    
    def get_live_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get live prices using Zerodha API with enhanced error handling and parallel processing"""
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
        
        # Use parallel processing for better performance
        prices = {}
        failed_symbols = []
        
        # Process symbols in parallel batches
        batch_size = 15  # Reduced batch size for better reliability
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        print(f"📊 Processing {total_batches} batches of {batch_size} symbols each")
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(symbols))
                batch_symbols = symbols[start_idx:end_idx]
                
                future = executor.submit(self._fetch_batch_prices_safe, batch_symbols, batch_num + 1, total_batches)
                futures.append(future)
            
            # Collect results
            for future in futures:
                try:
                    batch_prices, batch_failed = future.result(timeout=30)
                    prices.update(batch_prices)
                    failed_symbols.extend(batch_failed)
                except Exception as e:
                    print(f"❌ Batch processing error: {e}")
        
        # Calculate success rate
        success_rate = len(prices) / len(symbols) * 100 if symbols else 0
        
        print(f"📊 Price fetching results:")
        print(f"   Successful: {len(prices)}/{len(symbols)} ({success_rate:.1f}%)")
        print(f"   Failed: {len(failed_symbols)}")
        
        if len(prices) == 0:
            print("❌ No live prices fetched, using fallback")
            return self._get_fallback_prices(symbols, "All price fetches failed")
        
        if success_rate < 40:  # Lower threshold for acceptable success rate
            print(f"⚠️ Low success rate ({success_rate:.1f}%), supplementing with fallback")
            fallback_prices = self._get_fallback_prices(failed_symbols, f"Low success rate: {success_rate:.1f}%")
            prices.update(fallback_prices)
        
        print(f"✅ Returning {len(prices)} prices (live: {len(prices) - len(failed_symbols)}, fallback: {len(failed_symbols)})")
        return prices
    
    def _fetch_batch_prices_safe(self, symbols: List[str], batch_num: int, total_batches: int) -> tuple:
        """Safely fetch prices for a batch of symbols with timeout and error handling"""
        prices = {}
        failed_symbols = []
        
        try:
            print(f"   🔄 Processing batch {batch_num}/{total_batches}: {len(symbols)} symbols")
            
            # Prepare symbols for quote request
            quote_symbols = []
            symbol_mapping = {}
            
            for symbol in symbols:
                clean_symbol = symbol.strip().upper()
                nse_symbol = f"NSE:{clean_symbol}"
                quote_symbols.append(nse_symbol)
                symbol_mapping[nse_symbol] = clean_symbol
            
            print(f"   🔍 Requesting quotes for: {quote_symbols[:3]}{'...' if len(quote_symbols) > 3 else ''}")
            
            # Make the API call with timeout
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
                        print(f"   ✅ {original_symbol}: ₹{last_price:.2f}")
                    else:
                        failed_symbols.append(original_symbol)
                        print(f"   ⚠️ {original_symbol}: Invalid price data {last_price}")
            
            # Add symbols that weren't in the response to failed list
            for symbol in symbols:
                if symbol not in prices and symbol not in failed_symbols:
                    failed_symbols.append(symbol)
            
        except Exception as e:
            print(f"   ❌ Batch {batch_num} quote request failed: {e}")
            failed_symbols.extend(symbols)
        
        return prices, failed_symbols
    
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
        """Get fallback prices with improved realism and reason tracking"""
        print(f"🔄 Using fallback price generator: {reason}")
        
        # Generate more realistic price ranges based on actual Indian stock patterns
        import random
        random.seed(42)  # For consistent mock data
        
        fallback_prices = {}
        for symbol in symbols:
            # Generate price based on symbol characteristics for consistency
            symbol_hash = hash(symbol) % 10000
            
            # Create more realistic price distribution
            if symbol_hash < 2000:  # 20% - penny stocks
                base_price = 20 + (symbol_hash % 180)  # ₹20-₹200
            elif symbol_hash < 5000:  # 30% - small cap
                base_price = 200 + (symbol_hash % 800)  # ₹200-₹1000
            elif symbol_hash < 8000:  # 30% - mid cap
                base_price = 1000 + (symbol_hash % 2000)  # ₹1000-₹3000
            else:  # 20% - large cap
                base_price = 3000 + (symbol_hash % 7000)  # ₹3000-₹10000
            
            # Add some daily variation
            daily_variation = random.uniform(-5, 5)  # ±5%
            final_price = base_price * (1 + daily_variation/100)
            final_price = max(10, final_price)  # Ensure minimum price
            
            fallback_prices[symbol] = round(final_price, 2)
        
        print(f"   Generated {len(fallback_prices)} fallback prices (reason: {reason})")
        return fallback_prices
    
    def get_stocks_with_prices(self, force_refresh: bool = False) -> Dict:
        """Get complete stock data with live prices and enhanced change detection"""
        try:
            # Fetch CSV data with force refresh option
            csv_data = self.fetch_csv_data(force_refresh=force_refresh)
            
            # Get live prices with detailed status
            price_fetch_reason = "Unknown"
            try:
                prices = self.get_live_prices(csv_data['symbols'])
                
                # Determine if we got real live prices by checking variance and patterns
                price_values = list(prices.values())
                live_prices_used = self._detect_live_prices(price_values)
                
                if live_prices_used:
                    market_data_source = "Zerodha Live API"
                else:
                    market_data_source = "Fallback Generator"
                    
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
                    'force_refreshed': force_refresh,
                    'change_info': csv_data.get('change_info', {}),
                    'columns': csv_data.get('columns', []),
                    'content_size': csv_data.get('content_size', 0)
                },
                'price_data_status': {
                    'live_prices_used': live_prices_used,
                    'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()),
                    'success_rate': success_rate,
                    'last_updated': datetime.now().isoformat(),
                    'market_data_source': market_data_source,
                    'market_open': self._is_market_open(),
                    'price_fetch_reason': price_fetch_reason if not live_prices_used else "Live data fetched successfully",
                    'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None
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
            print(f"   Changes detected: {csv_data.get('change_info', {}).get('has_changes', False)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error preparing stock data: {e}")
            raise Exception(f"Cannot prepare investment data: {str(e)}")
    
    def _detect_live_prices(self, price_values: List[float]) -> bool:
        """Detect if prices are likely from live API vs fallback generator"""
        if len(price_values) < 5:
            return len(price_values) > 0
        
        try:
            import statistics
            
            # Live prices should have higher variance and more realistic distribution
            price_variance = statistics.variance(price_values)
            price_mean = statistics.mean(price_values)
            
            # Fallback prices have predictable patterns
            # Live prices should have more natural variance
            variance_ratio = price_variance / (price_mean ** 2) if price_mean > 0 else 0
            
            # Live prices should have variance ratio > 0.1 typically
            # Fallback prices tend to have lower, more uniform variance
            return variance_ratio > 0.05
            
        except Exception:
            # If calculation fails, assume live prices
            return True
    
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
        """Cache CSV data to file with enhanced metadata"""
        try:
            # Add caching metadata
            csv_data['cached_at'] = datetime.now().isoformat()
            csv_data['cache_version'] = '2.0'
            
            with open(self._cache_file, 'w') as f:
                json.dump(csv_data, f, indent=2)
            print("💾 CSV data cached successfully")
        except Exception as e:
            print(f"⚠️ Error caching CSV data: {e}")
    
    def get_connection_status(self) -> Dict:
        """Get current connection and data status with enhanced information"""
        status = {
            'zerodha_available': bool(self.zerodha_auth),
            'zerodha_authenticated': False,
            'kite_instance': bool(self.kite),
            'csv_accessible': False,
            'market_open': self._is_market_open(),
            'last_check': datetime.now().isoformat(),
            'cache_status': 'unknown',
            'change_detection_enabled': self._change_detection_enabled,
            'last_csv_check': self._last_check_time.isoformat() if self._last_check_time else None,
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
            else:
                status['csv_response_size'] = len(response.text)
                status['csv_response_time'] = response.elapsed.total_seconds()
        except Exception as e:
            status['csv_accessible'] = False
            status['errors'].append(f"CSV access error: {str(e)}")
        
        # Check cache status with detailed information
        try:
            cached_data = self._get_cached_csv()
            if cached_data:
                cached_time = datetime.fromisoformat(cached_data['fetch_time'])
                age_seconds = (datetime.now() - cached_time).total_seconds()
                
                if age_seconds < self._cache_duration:
                    status['cache_status'] = f'fresh ({age_seconds:.0f}s old)'
                else:
                    status['cache_status'] = f'stale ({age_seconds:.0f}s old)'
                
                status['cache_info'] = {
                    'hash': cached_data.get('csv_hash'),
                    'symbols_count': len(cached_data.get('symbols', [])),
                    'fetch_time': cached_data.get('fetch_time'),
                    'has_change_info': 'change_info' in cached_data,
                    'cache_version': cached_data.get('cache_version', '1.0')
                }
            else:
                status['cache_status'] = 'no_cache'
                status['cache_info'] = None
        except Exception as e:
            status['cache_status'] = f'cache_error: {str(e)}'
            status['cache_info'] = None
        
        return status
    
    def check_for_changes(self) -> Dict:
        """Explicitly check for CSV changes without forcing a full refresh"""
        try:
            print("🔍 Checking for CSV changes...")
            
            # Get current cached data
            cached_data = self._get_cached_csv()
            old_hash = cached_data.get('csv_hash') if cached_data else None
            
            # Fetch fresh data to compare
            fresh_data = self.fetch_csv_data(force_refresh=True)
            new_hash = fresh_data.get('csv_hash')
            
            # Get change information
            change_info = fresh_data.get('change_info', {})
            
            result = {
                'changes_detected': change_info.get('has_changes', False),
                'change_type': change_info.get('change_type', 'unknown'),
                'change_summary': change_info.get('summary', 'No summary available'),
                'old_hash': old_hash,
                'new_hash': new_hash,
                'check_time': datetime.now().isoformat(),
                'details': change_info.get('details', {}),
                'fresh_data_available': True
            }
            
            print(f"✅ Change check complete:")
            print(f"   Changes detected: {result['changes_detected']}")
            print(f"   Change type: {result['change_type']}")
            print(f"   Summary: {result['change_summary']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error checking for changes: {e}")
            return {
                'changes_detected': False,
                'error': str(e),
                'check_time': datetime.now().isoformat(),
                'fresh_data_available': False
            }
    
    def get_change_history(self, limit: int = 10) -> List[Dict]:
        """Get history of CSV changes from cache files"""
        try:
            # This would typically read from a change log file
            # For now, we'll return mock data based on cache info
            
            cached_data = self._get_cached_csv(ignore_age=True)
            if not cached_data:
                return []
            
            change_info = cached_data.get('change_info', {})
            
            # Return current change as history entry
            if change_info.get('has_changes'):
                return [{
                    'timestamp': cached_data.get('fetch_time'),
                    'hash': cached_data.get('csv_hash'),
                    'change_type': change_info.get('change_type'),
                    'summary': change_info.get('summary'),
                    'details': change_info.get('details', {})
                }]
            
            return []
            
        except Exception as e:
            print(f"⚠️ Error getting change history: {e}")
            return []
    
    def enable_change_detection(self, enabled: bool = True):
        """Enable or disable change detection"""
        self._change_detection_enabled = enabled
        print(f"🔄 Change detection {'enabled' if enabled else 'disabled'}")
    
    def get_csv_metadata(self) -> Dict:
        """Get detailed metadata about the current CSV"""
        try:
            cached_data = self._get_cached_csv()
            if not cached_data:
                return {'available': False}
            
            return {
                'available': True,
                'hash': cached_data.get('csv_hash'),
                'fetch_time': cached_data.get('fetch_time'),
                'source_url': cached_data.get('source_url'),
                'total_symbols': len(cached_data.get('symbols', [])),
                'total_rows': cached_data.get('total_rows', 0),
                'columns': cached_data.get('columns', []),
                'content_size': cached_data.get('content_size', 0),
                'symbol_column': cached_data.get('symbol_column_used'),
                'cache_version': cached_data.get('cache_version', '1.0'),
                'change_detection_enabled': self._change_detection_enabled,
                'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
                'change_info': cached_data.get('change_info', {})
            }
            
        except Exception as e:
            print(f"⚠️ Error getting CSV metadata: {e}")
            return {'available': False, 'error': str(e)}
    
    def clear_cache(self) -> bool:
        """Clear the CSV cache"""
        try:
            if os.path.exists(self._cache_file):
                os.remove(self._cache_file)
                print("🗑️ CSV cache cleared")
                return True
            return False
        except Exception as e:
            print(f"⚠️ Error clearing cache: {e}")
            return False
    
    def get_cache_size(self) -> int:
        """Get the size of the cache file in bytes"""
        try:
            if os.path.exists(self._cache_file):
                return os.path.getsize(self._cache_file)
            return 0
        except Exception as e:
            print(f"⚠️ Error getting cache size: {e}")
            return 0
    
    def validate_csv_structure(self, csv_data: Dict) -> Dict:
        """Validate the structure and content of CSV data"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            symbols = csv_data.get('symbols', [])
            data = csv_data.get('data', [])
            
            # Check if we have symbols
            if not symbols:
                validation_result['valid'] = False
                validation_result['errors'].append("No symbols found in CSV")
                return validation_result
            
            # Check for duplicates
            unique_symbols = set(symbols)
            if len(unique_symbols) != len(symbols):
                duplicate_count = len(symbols) - len(unique_symbols)
                validation_result['warnings'].append(f"{duplicate_count} duplicate symbols found")
            
            # Validate symbol format
            invalid_symbols = []
            for symbol in symbols:
                if not symbol or not isinstance(symbol, str) or len(symbol.strip()) == 0:
                    invalid_symbols.append(symbol)
            
            if invalid_symbols:
                validation_result['warnings'].append(f"{len(invalid_symbols)} invalid symbols found")
            
            # Check data consistency
            if len(data) != csv_data.get('total_rows', 0):
                validation_result['warnings'].append("Data row count mismatch")
            
            # Validate required columns
            required_columns = ['Symbol', 'symbol', 'SYMBOL']
            symbol_column = csv_data.get('symbol_column_used')
            if symbol_column not in csv_data.get('columns', []):
                validation_result['errors'].append(f"Symbol column '{symbol_column}' not found in data")
            
            # Statistics
            validation_result['stats'] = {
                'total_symbols': len(symbols),
                'unique_symbols': len(unique_symbols),
                'duplicate_symbols': len(symbols) - len(unique_symbols),
                'invalid_symbols': len(invalid_symbols),
                'total_columns': len(csv_data.get('columns', [])),
                'data_rows': len(data)
            }
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def export_csv_data(self, format: str = 'json') -> str:
        """Export current CSV data in specified format"""
        try:
            cached_data = self._get_cached_csv()
            if not cached_data:
                raise Exception("No cached CSV data available")
            
            if format.lower() == 'json':
                return json.dumps(cached_data, indent=2)
            elif format.lower() == 'csv':
                import pandas as pd
                df = pd.DataFrame(cached_data['data'])
                return df.to_csv(index=False)
            else:
                raise Exception(f"Unsupported export format: {format}")
                
        except Exception as e:
            print(f"⚠️ Error exporting CSV data: {e}")
            raise
    
    def get_symbol_details(self, symbol: str) -> Optional[Dict]:
        """Get detailed information about a specific symbol"""
        try:
            cached_data = self._get_cached_csv()
            if not cached_data:
                return None
            
            # Find the symbol in the data
            symbol_column = cached_data.get('symbol_column_used', 'Symbol')
            
            for row in cached_data.get('data', []):
                if row.get(symbol_column, '').upper() == symbol.upper():
                    return {
                        'symbol': symbol,
                        'data': row,
                        'csv_hash': cached_data.get('csv_hash'),
                        'fetch_time': cached_data.get('fetch_time'),
                        'found': True
                    }
            
            return {
                'symbol': symbol,
                'found': False,
                'csv_hash': cached_data.get('csv_hash'),
                'fetch_time': cached_data.get('fetch_time')
            }
            
        except Exception as e:
            print(f"⚠️ Error getting symbol details for {symbol}: {e}")
            return None
    
    def compare_with_portfolio(self, portfolio_symbols: List[str]) -> Dict:
        """Compare CSV symbols with current portfolio"""
        try:
            cached_data = self._get_cached_csv()
            if not cached_data:
                return {'error': 'No CSV data available'}
            
            csv_symbols = set(cached_data.get('symbols', []))
            portfolio_symbols_set = set(portfolio_symbols)
            
            return {
                'csv_symbols': list(csv_symbols),
                'portfolio_symbols': portfolio_symbols,
                'symbols_to_add': list(csv_symbols - portfolio_symbols_set),
                'symbols_to_remove': list(portfolio_symbols_set - csv_symbols),
                'common_symbols': list(csv_symbols & portfolio_symbols_set),
                'alignment_percentage': len(csv_symbols & portfolio_symbols_set) / len(csv_symbols | portfolio_symbols_set) * 100 if csv_symbols | portfolio_symbols_set else 0,
                'csv_hash': cached_data.get('csv_hash'),
                'comparison_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️ Error comparing with portfolio: {e}")
            return {'error': str(e)}
    
    def schedule_periodic_check(self, interval_minutes: int = 5):
        """Schedule periodic CSV checks (placeholder for background task)"""
        print(f"📅 Scheduling CSV checks every {interval_minutes} minutes")
        # This would typically integrate with a task scheduler like Celery or APScheduler
        # For now, just log the intent
        self._scheduled_check_interval = interval_minutes
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics for the CSV service"""
        try:
            cached_data = self._get_cached_csv()
            
            stats = {
                'cache_available': bool(cached_data),
                'cache_size_bytes': self.get_cache_size(),
                'last_fetch_time': cached_data.get('fetch_time') if cached_data else None,
                'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
                'change_detection_enabled': self._change_detection_enabled,
                'csv_url': self.csv_url,
                'cache_duration_seconds': self._cache_duration,
                'zerodha_auth_available': bool(self.zerodha_auth),
                'zerodha_authenticated': self.zerodha_auth.is_authenticated() if self.zerodha_auth else False
            }
            
            if cached_data:
                stats.update({
                    'symbols_count': len(cached_data.get('symbols', [])),
                    'data_rows': len(cached_data.get('data', [])),
                    'csv_hash': cached_data.get('csv_hash'),
                    'content_size': cached_data.get('content_size', 0),
                    'columns_count': len(cached_data.get('columns', [])),
                    'cache_age_seconds': (datetime.now() - datetime.fromisoformat(cached_data['fetch_time'])).total_seconds()
                })
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Error getting performance stats: {e}")
            return {'error': str(e)}