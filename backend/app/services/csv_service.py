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
            
            # Extract stock symbols
            symbols = df['Symbol'].tolist()
            
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
        """Get live prices for all symbols from Zerodha - NO FAKE DATA"""
        try:
            print(f"💰 Fetching live prices for {len(symbols)} stocks...")
            print(f"   Symbols to fetch: {symbols}")
            
            # Check authentication status
            if not self.zerodha_auth:
                print("❌ No Zerodha authentication service available")
                raise Exception("Zerodha authentication service not available")
            
            if not self.zerodha_auth.is_authenticated():
                print("🔄 Attempting to authenticate with Zerodha...")
                try:
                    self.zerodha_auth.authenticate()
                    self.kite = self.zerodha_auth.get_kite_instance()
                except Exception as e:
                    print(f"❌ Zerodha authentication failed: {e}")
                    raise Exception(f"Zerodha authentication failed: {str(e)}")
            
            if not self.kite:
                print("❌ Zerodha KiteConnect instance not available")
                raise Exception("Zerodha API connection not available")
            
            print("✅ Zerodha authenticated, fetching live prices...")
            
            prices = {}
            failed_symbols = []
            
            # Get quotes for all symbols
            for symbol in symbols:
                try:
                    print(f"   🔍 Fetching price for {symbol}...")
                    
                    # Try NSE first
                    quote_symbol = f"NSE:{symbol}"
                    print(f"      Trying {quote_symbol}...")
                    quote_data = self.kite.quote(quote_symbol)
                    
                    if quote_data and quote_symbol in quote_data:
                        price = quote_data[quote_symbol]['last_price']
                        if price and price > 0:
                            prices[symbol] = float(price)
                            print(f"   ✅ {symbol}: ₹{prices[symbol]:.2f} (NSE)")
                            continue
                        else:
                            print(f"      Invalid price from NSE for {symbol}: {price}")
                    else:
                        print(f"      NSE failed for {symbol} - no data returned")
                    
                    # Try BSE if NSE fails
                    quote_symbol = f"BSE:{symbol}"
                    print(f"      Trying {quote_symbol}...")
                    quote_data = self.kite.quote(quote_symbol)
                    
                    if quote_data and quote_symbol in quote_data:
                        price = quote_data[quote_symbol]['last_price']
                        if price and price > 0:
                            prices[symbol] = float(price)
                            print(f"   ✅ {symbol}: ₹{prices[symbol]:.2f} (BSE)")
                            continue
                        else:
                            print(f"      Invalid price from BSE for {symbol}: {price}")
                    else:
                        print(f"      BSE failed for {symbol} - no data returned")
                    
                    # If both fail, add to failed list
                    failed_symbols.append(symbol)
                    print(f"   ❌ {symbol}: Could not fetch price from any exchange")
                            
                except Exception as e:
                    failed_symbols.append(symbol)
                    print(f"   ❌ {symbol}: Error fetching price - {str(e)}")
            
            # Check if we got enough valid prices
            success_rate = len(prices) / len(symbols) * 100 if symbols else 0
            
            print(f"📊 Price fetching results:")
            print(f"   Successful: {len(prices)}/{len(symbols)} ({success_rate:.1f}%)")
            print(f"   Failed: {len(failed_symbols)}")
            
            if len(prices) == 0:
                print("❌ Could not fetch any live prices")
                raise Exception("Unable to fetch live prices for any stocks. Please check Zerodha connection and market hours.")
            
            if success_rate < 50:
                print(f"⚠️ Low success rate ({success_rate:.1f}%) for price fetching")
                raise Exception(f"Could only fetch prices for {len(prices)}/{len(symbols)} stocks. Market may be closed or there are connectivity issues.")
            
            if failed_symbols:
                print(f"⚠️ Warning: Could not fetch prices for {len(failed_symbols)} symbols: {', '.join(failed_symbols)}")
            
            return prices
            
        except Exception as e:
            print(f"❌ Error fetching live prices: {e}")
            raise Exception(f"Failed to fetch live market prices: {str(e)}")
    
    def get_stocks_with_prices(self) -> Dict:
        """Get complete stock data with live prices - NO FAKE DATA"""
        try:
            # Fetch CSV data
            csv_data = self.fetch_csv_data()
            
            # Get live prices (will raise exception if fails)
            prices = self.get_live_prices(csv_data['symbols'])
            
            # Combine data - only include stocks with valid prices
            stocks_data = []
            for stock_info in csv_data['data']:
                symbol = stock_info['Symbol']
                if symbol in prices:
                    stocks_data.append({
                        'symbol': symbol,
                        'price': prices[symbol],
                        'momentum': stock_info.get('Momentum', 0),
                        'volatility': stock_info.get('Volatility', 0),
                        'fitp': stock_info.get('FITP', 0),
                        'score': stock_info.get('Score', 0)
                    })
                else:
                    print(f"   ⚠️ {symbol}: Excluded - no valid price data")
            
            if len(stocks_data) == 0:
                raise Exception("No stocks have valid price data. Cannot proceed with investment calculations.")
            
            result = {
                'stocks': stocks_data,
                'total_stocks': len(stocks_data),
                'total_symbols_in_csv': len(csv_data['symbols']),
                'excluded_symbols': len(csv_data['symbols']) - len(stocks_data),
                'csv_info': {
                    'fetch_time': csv_data['fetch_time'],
                    'csv_hash': csv_data['csv_hash'],
                    'source_url': self.csv_url
                },
                'price_data_status': {
                    'live_prices_used': True,
                    'success_rate': (len(stocks_data) / len(csv_data['symbols'])) * 100,
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            print(f"✅ Complete stock data prepared:")
            print(f"   CSV symbols: {len(csv_data['symbols'])}")
            print(f"   With valid prices: {len(stocks_data)}")
            print(f"   Excluded: {result['excluded_symbols']}")
            print(f"   Success rate: {result['price_data_status']['success_rate']:.1f}%")
            
            return result
            
        except Exception as e:
            print(f"❌ Error preparing stock data: {e}")
            # Re-raise the original exception with context
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
            'last_check': datetime.now().isoformat()
        }
        
        # Check Zerodha status
        if self.zerodha_auth:
            try:
                status['zerodha_authenticated'] = self.zerodha_auth.is_authenticated()
            except:
                status['zerodha_authenticated'] = False
        
        # Check CSV accessibility
        try:
            response = requests.get(self.csv_url, timeout=10)
            status['csv_accessible'] = response.status_code == 200
        except:
            status['csv_accessible'] = False
        
        return status