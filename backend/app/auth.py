# backend/app/auth.py
import os
import json
import pyotp
import requests
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
from .config import settings

class ZerodhaAuth:
    def __init__(self):
        self.api_key = settings.ZERODHA_API_KEY
        self.api_secret = settings.ZERODHA_API_SECRET
        self.user_id = settings.ZERODHA_USER_ID
        self.password = settings.ZERODHA_PASSWORD
        self.totp_key = settings.ZERODHA_TOTP_KEY
        self.access_token_file = settings.ZERODHA_ACCESS_TOKEN_FILE
        self.kite = None
        self._authenticated = False
        self.zerodha_profile_name = None
        
    def authenticate(self):
        """EXACTLY like your notebook - simple and working"""
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            
            # Try existing token
            if os.path.exists(self.access_token_file):
                with open(self.access_token_file, "r") as f:
                    access_token = f.read().strip()
                if access_token:
                    self.kite.set_access_token(access_token)
                    try:
                        profile = self.kite.profile()
                        self.zerodha_profile_name = profile['user_name']
                        self._authenticated = True
                        print(f"✅ Zerodha Profile: {self.zerodha_profile_name}")
                        return self.kite
                    except Exception:
                        print("⚠️ Saved Zerodha token invalid, generating new one")

            # Generate new token - EXACTLY like your notebook
            http_session = requests.Session()
            url = http_session.get(url=f'https://kite.trade/connect/login?v=3&api_key={self.api_key}').url
            
            response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={'user_id': self.user_id, 'password': self.password}
            )
            resp_dict = json.loads(response.content)
            if resp_dict.get("status") != "success":
                raise Exception(f"❌ Zerodha login failed: {resp_dict.get('message', 'Unknown error')}")

            totp_value = pyotp.TOTP(self.totp_key).now()
            twofa_response = http_session.post(
                url='https://kite.zerodha.com/api/twofa',
                data={
                    'user_id': self.user_id,
                    'request_id': resp_dict["data"]["request_id"],
                    'twofa_value': totp_value
                }
            )

            url = url + "&skip_session=true"
            final_response = http_session.get(url=url, allow_redirects=True).url
            parsed_url = urlparse(final_response)
            query_params = parse_qs(parsed_url.query)
            if 'request_token' not in query_params:
                raise Exception(f"❌ Zerodha request token not found: {final_response}")

            request_token = query_params['request_token'][0]
            data = self.kite.generate_session(request_token, self.api_secret)
            access_token = data["access_token"]
            self.kite.set_access_token(access_token)

            os.makedirs(os.path.dirname(self.access_token_file), exist_ok=True)
            with open(self.access_token_file, "w") as f:
                f.write(access_token)
            print(f"✅ Zerodha Access Token Saved: {access_token}")

            profile = self.kite.profile()
            self.zerodha_profile_name = profile['user_name']
            self._authenticated = True
            print(f"✅ Zerodha Profile: {self.zerodha_profile_name}")
            return self.kite
            
        except Exception as e:
            print(f"❌ Zerodha authentication failed: {e}")
            self._authenticated = False
            return None
    
    def get_kite_instance(self):
        return self.kite if self._authenticated else None
    
    def is_authenticated(self):
        return self._authenticated
    
    @property
    def profile_name(self):
        return self.zerodha_profile_name


# backend/app/services/portfolio_service.py
from ..auth import ZerodhaAuth

class PortfolioService:
    def __init__(self, zerodha_auth: ZerodhaAuth):
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance()
    
    def get_portfolio_data(self):
        """Get real portfolio data from Zerodha - NO SAMPLE DATA"""
        if not self.kite:
            print("❌ No Zerodha connection available")
            return None
        
        try:
            print("📊 Fetching live data from Zerodha...")
            holdings = self.kite.holdings()
            margins = self.kite.margins()
            print(f"📈 Retrieved {len(holdings)} holdings from Zerodha")
            
            portfolio_holdings = []
            total_investment = 0
            current_value = 0
            
            for holding in holdings:
                symbol = holding['tradingsymbol']
                regular_qty = holding.get('quantity', 0)
                t1_qty = holding.get('t1_quantity', 0)  
                collateral_qty = holding.get('collateral_quantity', 0)
                total_quantity = regular_qty + t1_qty + collateral_qty
                
                if total_quantity > 0:
                    avg_price = holding['average_price']
                    current_price = holding['last_price']
                    holding_value = total_quantity * current_price
                    investment_value = total_quantity * avg_price
                    pnl = holding_value - investment_value
                    pnl_percent = (pnl / investment_value) * 100 if investment_value > 0 else 0
                    
                    portfolio_holdings.append({
                        "symbol": symbol,
                        "quantity": total_quantity,
                        "avg_price": avg_price,
                        "current_price": current_price,
                        "current_value": holding_value,
                        "allocation_percent": 0,
                        "pnl": pnl,
                        "pnl_percent": pnl_percent
                    })
                    
                    total_investment += investment_value
                    current_value += holding_value
            
            if len(portfolio_holdings) == 0:
                print("❌ No holdings found")
                return None
            
            # Calculate allocation percentages
            for holding in portfolio_holdings:
                holding["allocation_percent"] = (holding["current_value"] / current_value) * 100 if current_value > 0 else 0
            
            total_returns = current_value - total_investment
            returns_percentage = (total_returns / total_investment) * 100 if total_investment > 0 else 0
            available_cash = margins['equity']['available']['cash']
            
            print(f"✅ Portfolio: {len(portfolio_holdings)} holdings, ₹{current_value:,.2f} value")
            
            return {
                "user_id": 1,
                "current_value": current_value,
                "invested_value": total_investment,
                "total_returns": total_returns,
                "returns_percentage": returns_percentage,
                "available_cash": available_cash,
                "holdings": portfolio_holdings,
                "allocation": portfolio_holdings,
                "total_invested": total_investment,
                "total_holdings": len(portfolio_holdings),
                "zerodha_connected": True,
                "zerodha_profile": self.zerodha_auth.profile_name
            }
            
        except Exception as e:
            print(f"❌ Error getting portfolio data: {e}")
            return None


# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="Investment Rebalancing WebApp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

zerodha_auth = None
portfolio_service = None

try:
    from .config import settings
    from .auth import ZerodhaAuth
    from .services.portfolio_service import PortfolioService
    
    zerodha_auth = ZerodhaAuth()
    portfolio_service = PortfolioService(zerodha_auth)
    print("✅ Services initialized")
except Exception as e:
    print(f"❌ Initialization error: {e}")

@app.get("/")
async def root():
    return {"message": "Investment Rebalancing WebApp API"}

@app.get("/health")
async def health_check():
    zerodha_connected = False
    if zerodha_auth:
        try:
            kite = zerodha_auth.authenticate()
            zerodha_connected = zerodha_auth.is_authenticated()
        except Exception as e:
            print(f"❌ Health check auth error: {e}")
    
    return {
        "status": "healthy", 
        "zerodha_connected": zerodha_connected,
        "zerodha_profile": zerodha_auth.profile_name if zerodha_connected else None,
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/api/test-auth")
async def test_auth():
    if not zerodha_auth:
        return {"error": "ZerodhaAuth not initialized"}
    
    try:
        kite = zerodha_auth.authenticate()
        if zerodha_auth.is_authenticated():
            return {
                "success": True,
                "message": "Zerodha authentication successful!",
                "profile_name": zerodha_auth.profile_name
            }
        else:
            return {"success": False, "message": "Authentication failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/portfolio/summary/{user_id}")
async def get_portfolio_summary(user_id: int):
    print(f"🔍 Portfolio summary requested for user {user_id}")
    
    if not zerodha_auth or not portfolio_service:
        return {"error": "Services not initialized"}
    
    try:
        # Authenticate first
        kite = zerodha_auth.authenticate()
        if not zerodha_auth.is_authenticated():
            return {"error": "Zerodha authentication failed"}
        
        # Get real portfolio data
        portfolio_data = portfolio_service.get_portfolio_data()
        if portfolio_data:
            return portfolio_data
        else:
            return {"error": "Could not fetch portfolio data"}
        
    except Exception as e:
        print(f"❌ Portfolio error: {e}")
        return {"error": str(e)}

@app.get("/api/debug/holdings")
async def debug_holdings():
    if not zerodha_auth:
        return {"error": "ZerodhaAuth not available"}
    
    try:
        kite = zerodha_auth.authenticate()
        if not zerodha_auth.is_authenticated():
            return {"error": "Authentication failed"}
        
        kite_instance = zerodha_auth.get_kite_instance()
        holdings = kite_instance.holdings()
        margins = kite_instance.margins()
        
        return {
            "profile_name": zerodha_auth.profile_name,
            "holdings_count": len(holdings),
            "holdings": holdings[:3] if holdings else [],
            "margins_cash": margins['equity']['available']['cash'] if margins else 0,
            "authentication_working": True
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)