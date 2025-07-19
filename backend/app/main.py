# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

from .config import settings
from .auth import ZerodhaAuth
from .services.portfolio_service import PortfolioService

app = FastAPI(title="Investment Rebalancing WebApp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Zerodha authentication
print("🔄 Initializing Zerodha connection...")
zerodha_auth = ZerodhaAuth()
kite = zerodha_auth.authenticate()

# Initialize portfolio service
portfolio_service = PortfolioService(zerodha_auth)

if zerodha_auth.is_authenticated():
    print("🎉 Zerodha authentication successful!")
else:
    print("❌ Zerodha authentication failed - using sample data")

@app.get("/")
async def root():
    return {"message": "Investment Rebalancing WebApp API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "zerodha_connected": zerodha_auth.is_authenticated(),
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT
    }

@app.get("/api/portfolio/summary/{user_id}")
async def get_portfolio_summary(user_id: int):
    # Try to get real data first
    real_data = portfolio_service.get_portfolio_data()
    if real_data:
        print(f"📊 Returning real portfolio data with {len(real_data['holdings'])} holdings")
        return real_data
    
    # Fallback to sample data
    print("📊 Returning sample portfolio data")
    return portfolio_service.get_sample_data()

@app.get("/api/portfolio/performance/{user_id}")
async def get_portfolio_performance(user_id: int):
    # Sample performance data
    base_date = datetime.now().date() - timedelta(days=30)
    performance_data = []
    
    base_value = 450000
    for i in range(31):
        date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        value = base_value + (i * 1000) + (i % 3 * 500)
        performance_data.append({
            "date": date_str,
            "value": value
        })
    
    return {
        "performance_data": performance_data,
        "period": "30_days"
    }

@app.post("/api/auth/login")
async def login(credentials: dict):
    """Simple login for demo"""
    return {
        "access_token": "demo_token_123",
        "user": {"user_id": 1, "email": credentials.get("email", "demo@example.com")}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)