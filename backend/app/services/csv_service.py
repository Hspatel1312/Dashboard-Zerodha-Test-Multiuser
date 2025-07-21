# backend/app/services/csv_service.py
import requests
import pandas as pd
from typing import List, Dict
from datetime import datetime
import hashlib
from io import StringIO  # Import StringIO from io module instead

class CSVService:
    def __init__(self, zerodha_auth):
        self.csv_url = "https://raw.githubusercontent.com/Hspatel1312/Stock-scanner/refs/heads/main/data/nifty_smallcap_momentum_scan.csv"
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance()
        
    def fetch_csv_data(self) -> Dict:
        """Fetch and parse CSV data from GitHub"""
        try:
            print("📊 Fetching CSV data from GitHub...")
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV using io.StringIO instead of pd.StringIO
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
        """Get live prices for all symbols from Zerodha"""
        try:
            print(f"💰 Fetching live prices for {len(symbols)} stocks...")
            print(f"   Symbols to fetch: {symbols}")
            
            # Ensure authentication first
            if not self.zerodha_auth.is_authenticated():
                print("🔄 Authenticating with Zerodha...")
                self.zerodha_auth.authenticate()
                self.kite = self.zerodha_auth.get_kite_instance()
            
            if not self.kite:
                raise Exception("Zerodha authentication failed")
            
            prices = {}
            failed_symbols = []
            
            # Get quotes for all symbols
            for symbol in symbols:
                try:
                    print(f"   🔍 Trying to get price for {symbol}...")
                    
                    # Try NSE first
                    quote_symbol = f"NSE:{symbol}"
                    print(f"      Trying {quote_symbol}...")
                    quote_data = self.kite.quote(quote_symbol)
                    
                    if quote_data and quote_symbol in quote_data:
                        prices[symbol] = quote_data[quote_symbol]['last_price']
                        print(f"   ✅ {symbol}: ₹{prices[symbol]:.2f} (NSE)")
                        continue
                    else:
                        print(f"      NSE failed for {symbol}")
                    
                    # Try BSE if NSE fails
                    quote_symbol = f"BSE:{symbol}"
                    print(f"      Trying {quote_symbol}...")
                    quote_data = self.kite.quote(quote_symbol)
                    
                    if quote_data and quote_symbol in quote_data:
                        prices[symbol] = quote_data[quote_symbol]['last_price']
                        print(f"   ✅ {symbol}: ₹{prices[symbol]:.2f} (BSE)")
                        continue
                    else:
                        print(f"      BSE also failed for {symbol}")
                    
                    # If both fail, try common variations
                    variations = [
                        f"NSE:{symbol}-EQ",
                        f"BSE:{symbol}-EQ",
                        f"NSE:{symbol}",
                        f"BSE:{symbol}"
                    ]
                    
                    price_found = False
                    for variation in variations:
                        try:
                            print(f"      Trying variation {variation}...")
                            quote_data = self.kite.quote(variation)
                            if quote_data and variation in quote_data:
                                prices[symbol] = quote_data[variation]['last_price']
                                print(f"   ✅ {symbol}: ₹{prices[symbol]:.2f} ({variation})")
                                price_found = True
                                break
                        except Exception as var_e:
                            print(f"      Variation {variation} failed: {var_e}")
                            continue
                    
                    if not price_found:
                        failed_symbols.append(symbol)
                        print(f"   ❌ {symbol}: All attempts failed")
                            
                except Exception as e:
                    failed_symbols.append(symbol)
                    print(f"   ❌ {symbol}: Error - {str(e)}")
            
            if failed_symbols:
                print(f"⚠️ Failed to get prices for: {', '.join(failed_symbols)}")
            
            print(f"✅ Successfully fetched {len(prices)} out of {len(symbols)} prices")
            print(f"   Success rate: {len(prices)}/{len(symbols)} ({(len(prices)/len(symbols)*100):.1f}%)")
            
            return prices
            
        except Exception as e:
            print(f"❌ Error fetching live prices: {e}")
            raise Exception(f"Failed to fetch live prices: {str(e)}")
    
    def get_stocks_with_prices(self) -> Dict:
        """Get complete stock data with live prices"""
        try:
            # Fetch CSV data
            csv_data = self.fetch_csv_data()
            
            # Try to get live prices first
            try:
                prices = self.get_live_prices(csv_data['symbols'])
            except Exception as price_error:
                print(f"⚠️ Live price fetching failed: {price_error}")
                print("🔄 Using sample prices for development...")
                
                # Fallback to sample prices for development
                prices = self._get_sample_prices(csv_data['symbols'])
            
            # Combine data
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
                    print(f"   ⚠️ {symbol}: No price data available, skipping")
            
            result = {
                'stocks': stocks_data,
                'total_stocks': len(stocks_data),
                'total_symbols_in_csv': len(csv_data['symbols']),
                'csv_info': {
                    'fetch_time': csv_data['fetch_time'],
                    'csv_hash': csv_data['csv_hash'],
                    'source_url': self.csv_url
                }
            }
            
            print(f"✅ Complete stock data prepared:")
            print(f"   CSV symbols: {len(csv_data['symbols'])}")
            print(f"   With prices: {len(stocks_data)}")
            print(f"   Success rate: {len(stocks_data)}/{len(csv_data['symbols'])} ({(len(stocks_data)/len(csv_data['symbols'])*100):.1f}%)")
            
            if len(stocks_data) == 0:
                raise Exception("No stocks have valid price data")
            
            return result
            
        except Exception as e:
            print(f"❌ Error preparing stock data: {e}")
            raise Exception(f"Failed to prepare stock data: {str(e)}")
    
    def _get_sample_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Generate sample prices for development when live prices fail"""
        import random
        
        print(f"🎯 Generating sample prices for {len(symbols)} symbols...")
        
        sample_prices = {}
        for symbol in symbols:
            # Generate realistic random prices between ₹100 and ₹3000
            price = round(random.uniform(100, 3000), 2)
            sample_prices[symbol] = price
            print(f"   📊 {symbol}: ₹{price:.2f} (sample)")
        
        print(f"✅ Sample prices generated for all {len(symbols)} symbols")
        return sample_prices
    
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