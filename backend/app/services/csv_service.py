# backend/app/services/csv_service.py
import requests
import pandas as pd
from typing import List, Dict
from datetime import datetime
import hashlib
from io import StringIO

class CSVService:
    def __init__(self, zerodha_auth):
        self.csv_url = "https://raw.githubusercontent.com/Hspatel1312/Stock-scanner/refs/heads/main/data/nifty_smallcap_momentum_scan.csv"
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance() if zerodha_auth else None
        
    def fetch_csv_data(self) -> Dict:
        """Fetch and parse CSV data from GitHub"""
        try:
            print("📊 Fetching CSV data from GitHub...")
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV using io.StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Extract stock symbols - handle different possible column names
            if 'Symbol' in df.columns:
                symbols = df['Symbol'].tolist()
            elif 'symbol' in df.columns:
                symbols = df['symbol'].tolist()
            elif 'SYMBOL' in df.columns:
                symbols = df['SYMBOL'].tolist()
            else:
                # If no symbol column found, use first column
                symbols = df.iloc[:, 0].tolist()
            
            # Clean symbols (remove any whitespace/special characters)
            symbols = [str(symbol).strip() for symbol in symbols if str(symbol).strip()]
            
            # Create CSV snapshot
            csv_data = {
                'symbols': symbols,
                'data': df.to_dict('records'),
                'fetch_time': datetime.now().isoformat(),
                'csv_hash': hashlib.md5(response.text.encode()).hexdigest()[:8]
            }
            
            print(f"✅ CSV data fetched: {len(symbols)} stocks")
            print(f"   Stocks: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")
            
            return csv_data
            
        except Exception as e:
            print(f"❌ Error fetching CSV data: {e}")
            raise Exception(f"Failed to fetch CSV data: {str(e)}")
    
    def get_live_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get live prices using CORRECT Zerodha API format"""
        if not symbols:
            raise Exception("No symbols provided for price fetching")
            
        print(f"💰 Fetching live prices for {len(symbols)} stocks...")
        print(f"   Symbols to fetch: {symbols}")
        
        # Check authentication status first
        if not self.zerodha_auth:
            print("❌ No Zerodha auth service available")
            raise Exception("Zerodha authentication service not available")
        
        if not self.zerodha_auth.is_authenticated():
            print("🔄 Attempting to authenticate with Zerodha...")
            try:
                self.zerodha_auth.authenticate()
                self.kite = self.zerodha_auth.get_kite_instance()
            except Exception as e:
                print(f"❌ Zerodha authentication failed: {e}")
                raise Exception(f"Unable to authenticate with Zerodha: {str(e)}")
        
        if not self.kite:
            raise Exception("Zerodha API connection not available after authentication")
        
        print("✅ Zerodha authenticated, fetching live prices...")
        
        prices = {}
        failed_symbols = []
        
        # Prepare symbols for batch quote request
        # Try both NSE and BSE for each symbol
        quote_symbols = []
        symbol_mapping = {}  # Maps "NSE:SYMBOL" -> "SYMBOL"
        
        for symbol in symbols:
            nse_symbol = f"NSE:{symbol}"
            bse_symbol = f"BSE:{symbol}"
            
            quote_symbols.extend([nse_symbol, bse_symbol])
            symbol_mapping[nse_symbol] = symbol
            symbol_mapping[bse_symbol] = symbol
        
        print(f"   📝 Prepared {len(quote_symbols)} quote requests for {len(symbols)} symbols")
        
        # Batch quote request using CORRECT API format
        try:
            print("   🔍 Making batch quote request...")
            # Using the correct format: kite.quote(['NSE:SYMBOL', 'BSE:SYMBOL', ...])
            quote_response = self.kite.quote(quote_symbols)
            
            print(f"   📊 Quote response received for {len(quote_response)} symbols")
            
            # Process the response
            for quote_key, quote_data in quote_response.items():
                if quote_key in symbol_mapping:
                    original_symbol = symbol_mapping[quote_key]
                    
                    # Extract last_price from the response
                    last_price = quote_data.get('last_price', 0)
                    
                    if last_price and last_price > 0:
                        # If we already have a price for this symbol, skip (prefer NSE over BSE)
                        if original_symbol not in prices:
                            prices[original_symbol] = float(last_price)
                            exchange = quote_key.split(':')[0]
                            print(f"   ✅ {original_symbol}: ₹{last_price:.2f} ({exchange})")
                    else:
                        print(f"   ⚠️ {quote_key}: Invalid price {last_price}")
            
            # Check which symbols failed
            for symbol in symbols:
                if symbol not in prices:
                    failed_symbols.append(symbol)
                    print(f"   ❌ {symbol}: No valid price found")
            
        except Exception as e:
            print(f"   ❌ Batch quote request failed: {e}")
            print(f"   🔍 Trying individual quote requests...")
            
            # Fallback: Try individual requests
            for symbol in symbols:
                try:
                    # Try NSE first
                    nse_symbol = f"NSE:{symbol}"
                    quote_response = self.kite.quote([nse_symbol])
                    
                    if nse_symbol in quote_response:
                        last_price = quote_response[nse_symbol].get('last_price', 0)
                        if last_price and last_price > 0:
                            prices[symbol] = float(last_price)
                            print(f"   ✅ {symbol}: ₹{last_price:.2f} (NSE)")
                            continue
                    
                    # Try BSE if NSE failed
                    bse_symbol = f"BSE:{symbol}"
                    quote_response = self.kite.quote([bse_symbol])
                    
                    if bse_symbol in quote_response:
                        last_price = quote_response[bse_symbol].get('last_price', 0)
                        if last_price and last_price > 0:
                            prices[symbol] = float(last_price)
                            print(f"   ✅ {symbol}: ₹{last_price:.2f} (BSE)")
                            continue
                    
                    # If both failed
                    failed_symbols.append(symbol)
                    print(f"   ❌ {symbol}: No price from NSE or BSE")
                    
                except Exception as symbol_error:
                    failed_symbols.append(symbol)
                    print(f"   ❌ {symbol}: Error - {symbol_error}")
        
        # Calculate success rate
        success_rate = len(prices) / len(symbols) * 100 if symbols else 0
        
        print(f"📊 Price fetching results:")
        print(f"   Successful: {len(prices)}/{len(symbols)} ({success_rate:.1f}%)")
        print(f"   Failed: {len(failed_symbols)}")
        
        if len(prices) == 0:
            raise Exception("Unable to fetch live prices for any stocks. Please check:\n1. Zerodha connection\n2. Market hours (9:15 AM - 3:30 PM IST)\n3. Internet connectivity\n4. Symbol names in CSV")
        
        if success_rate < 50:
            print(f"⚠️ Low success rate ({success_rate:.1f}%). This may indicate:")
            print("   - Market is closed")
            print("   - Some symbols may be incorrect or delisted")
            print("   - Network connectivity issues")
        
        if failed_symbols:
            print(f"⚠️ Failed symbols: {', '.join(failed_symbols[:10])}{'...' if len(failed_symbols) > 10 else ''}")
        
        return prices
    
    def get_stocks_with_prices(self) -> Dict:
        """Get complete stock data with live prices"""
        try:
            # Fetch CSV data
            csv_data = self.fetch_csv_data()
            
            # Get live prices using corrected API
            prices = self.get_live_prices(csv_data['symbols'])
            
            # Combine data - only include stocks with valid prices
            stocks_data = []
            excluded_count = 0
            
            for stock_info in csv_data['data']:
                # Handle different column name possibilities
                if 'Symbol' in stock_info:
                    symbol = stock_info['Symbol']
                elif 'symbol' in stock_info:
                    symbol = stock_info['symbol']
                elif 'SYMBOL' in stock_info:
                    symbol = stock_info['SYMBOL']
                else:
                    # Skip if no symbol found
                    excluded_count += 1
                    continue
                
                symbol = str(symbol).strip()
                
                if symbol in prices:
                    stocks_data.append({
                        'symbol': symbol,
                        'price': prices[symbol],
                        'momentum': stock_info.get('Momentum', stock_info.get('momentum', 0)),
                        'volatility': stock_info.get('Volatility', stock_info.get('volatility', 0)),
                        'fitp': stock_info.get('FITP', stock_info.get('fitp', 0)),
                        'score': stock_info.get('Score', stock_info.get('score', 0))
                    })
                else:
                    print(f"   ⚠️ {symbol}: Excluded - no valid price data")
                    excluded_count += 1
            
            if len(stocks_data) == 0:
                raise Exception("No stocks have valid live price data. This could mean:\n1. Market is closed\n2. All symbols failed to fetch prices\n3. Network connectivity issues\nPlease try again during market hours or check symbol names.")
            
            result = {
                'stocks': stocks_data,
                'total_stocks': len(stocks_data),
                'total_symbols_in_csv': len(csv_data['symbols']),
                'excluded_symbols': excluded_count,
                'csv_info': {
                    'fetch_time': csv_data['fetch_time'],
                    'csv_hash': csv_data['csv_hash'],
                    'source_url': self.csv_url
                },
                'price_data_status': {
                    'live_prices_used': True,
                    'zerodha_connected': True,
                    'success_rate': (len(stocks_data) / len(csv_data['symbols'])) * 100,
                    'last_updated': datetime.now().isoformat(),
                    'market_data_source': 'Zerodha Live API'
                }
            }
            
            print(f"✅ Complete stock data prepared:")
            print(f"   CSV symbols: {len(csv_data['symbols'])}")
            print(f"   With valid live prices: {len(stocks_data)}")
            print(f"   Excluded due to no price: {excluded_count}")
            print(f"   Success rate: {result['price_data_status']['success_rate']:.1f}%")
            
            return result
            
        except Exception as e:
            print(f"❌ Error preparing stock data: {e}")
            raise Exception(f"Cannot prepare investment data: {str(e)}")
    
    def compare_csv_with_portfolio(self, current_symbols: List[str]) -> Dict:
        """Compare current CSV stocks with current portfolio"""
        try:
            csv_data = self.fetch_csv_data()
            csv_symbols = set(csv_data['symbols'])
            portfolio_symbols = set(current_symbols)
            
            # Find differences
            new_stocks = csv_symbols - portfolio_symbols  # In CSV but not in portfolio
            removed_stocks = portfolio_symbols - csv_symbols  # In portfolio but not in CSV
            common_stocks = csv_symbols & portfolio_symbols  # In both
            
            rebalancing_needed = len(new_stocks) > 0 or len(removed_stocks) > 0
            
            comparison = {
                'rebalancing_needed': rebalancing_needed,
                'csv_stocks': list(csv_symbols),
                'portfolio_stocks': current_symbols,
                'new_stocks': list(new_stocks),
                'removed_stocks': list(removed_stocks),
                'common_stocks': list(common_stocks),
                'csv_info': {
                    'fetch_time': csv_data['fetch_time'],
                    'csv_hash': csv_data['csv_hash']
                }
            }
            
            if rebalancing_needed:
                print(f"🔄 Rebalancing needed!")
                print(f"   New stocks to add: {list(new_stocks)}")
                print(f"   Stocks to remove: {list(removed_stocks)}")
            else:
                print(f"✅ Portfolio matches CSV - no rebalancing needed")
            
            return comparison
            
        except Exception as e:
            print(f"❌ Error comparing CSV with portfolio: {e}")
            raise Exception(f"Failed to compare CSV with portfolio: {str(e)}")
    
    def get_connection_status(self) -> Dict:
        """Get current connection and data status"""
        status = {
            'zerodha_available': bool(self.zerodha_auth),
            'zerodha_authenticated': False,
            'kite_instance': bool(self.kite),
            'csv_accessible': False,
            'last_check': datetime.now().isoformat(),
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
        
        return status