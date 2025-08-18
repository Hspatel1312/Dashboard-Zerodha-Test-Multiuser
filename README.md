# 🚀 Investment Dashboard - Premium UI with GOLDBEES Integration

A modern investment rebalancing dashboard with Apple/Tesla-inspired design and advanced GOLDBEES ETF support.

## ⚡ Quick Start

### 1. Start Python Backend
```bash
START-PYTHON-BACKEND.bat
```
Or manually:
```bash
cd backend
python -c "import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)"
```

### 2. Start Java Frontend
**Double-click `START-DASHBOARD.bat`** or run:
```bash
cd frontend-java
.\mvnw.cmd spring-boot:run -Dskip.npm=true
```

### 3. Open Dashboard
http://localhost:8080

## 🎯 Key Features

- ✨ **Premium Dark UI** - Apple/Tesla inspired design
- 🥇 **GOLDBEES Integration** - Automatic 50% gold allocation when GOLDBEES ETF is present
- 🔐 **Zerodha Integration** - Manual & automatic authentication flows  
- 📊 **Dynamic Portfolio Allocation** - Smart allocation based on stock composition
- 🔄 **Order Retry System** - Individual and batch retry for failed orders
- 📱 **Responsive Design** - Works on all devices
- ⚡ **Fast Performance** - Optimized for speed
- 🎯 **Smart Rebalancing** - Only triggers on stock list changes, not drift

## 🛠️ Requirements

- **Java 17+** - [Download from Adoptium](https://adoptium.net/)
- **Python 3.9+** - For backend API
- **Internet Connection** - For Maven dependencies

## 📋 Project Structure

```
├── backend/                    # Python FastAPI backend
│   ├── app/services/          # Core business logic
│   │   ├── investment_calculator.py  # GOLDBEES & dynamic allocation logic
│   │   ├── csv_service.py            # Stock data with NaN handling
│   │   └── investment_service.py     # Investment & rebalancing engine
│   └── main.py               # API endpoints & authentication
├── frontend-java/             # Java Spring Boot + React frontend
│   ├── src/main/java/        # Java controllers and services  
│   ├── src/main/frontend/    # React.js components
│   └── mvnw.cmd             # Maven wrapper (no Maven install needed)
└── START-DASHBOARD.bat       # One-click startup script
```

## 🥇 GOLDBEES Integration

### **Automatic Portfolio Allocation:**
- **With GOLDBEES:** 50% GOLDBEES ETF + remaining 50% equally distributed among other stocks
- **Without GOLDBEES:** Traditional equal-weight allocation (e.g., 5% per stock)

### **Example Scenarios:**
```
📊 Portfolio with GOLDBEES (21 stocks total):
├── GOLDBEES: 50% allocation
└── Other 20 stocks: 2.5% each (50% ÷ 20)

📊 Portfolio without GOLDBEES (20 stocks):
└── All 20 stocks: 5% each (100% ÷ 20)
```

### **Smart Features:**
- **NaN Handling:** GOLDBEES ETF data automatically cleaned and processed
- **±2% Flexibility:** Smart allocation flexibility for expensive stocks
- **Optimized Minimum Investment:** Only ₹3.95L required (down from ₹17.8L)
- **Dynamic Calculation:** Minimum investment adjusts based on portfolio composition
- **Live Pricing:** Real-time ETF prices via Zerodha API

### **💡 Allocation Flexibility (±2%):**
```
📊 GOLDBEES Portfolio Allocation Ranges:
├── GOLDBEES: 48% - 52% (target: 50%)
└── Other stocks: 0.5% - 4.5% each (target: 2.5%)

📊 No GOLDBEES Portfolio Allocation Ranges:
└── All stocks: 3% - 7% each (target: 5%)

💰 Minimum Investment Examples:
├── With expensive stocks (₹17,798): ₹3,95,511 total
├── For ₹5,00,000 investment: 99.93% utilization
└── Every stock gets at least 1 share guaranteed
```

## 🔄 **System Working Logic**

### **Initial Investment Flow:**
1. **Minimum Investment Check** - Uses ±2% flexibility to determine minimum (₹3.95L)
2. **Stock List Fetch** - Retrieves 21 stocks from CSV including GOLDBEES
3. **Dynamic Allocation** - GOLDBEES: 50%, Other 20 stocks: 2.5% each
4. **Order Generation** - Creates buy orders ensuring every stock gets ≥1 share
5. **Portfolio Creation** - Stores system orders and creates portfolio state

### **Rebalancing Decision Logic:**
```
🔍 Rebalancing Trigger = Stock List Changes ONLY

✅ TRIGGERS Rebalancing:
├── New stock added to CSV
├── Stock removed from CSV  
└── Stock symbol changes

❌ DOES NOT Trigger Rebalancing:
├── Price fluctuations
├── Allocation drift (2.1% vs 2.5%)
├── Portfolio value changes
└── Market movements
```

### **Rebalancing Execution Flow:**
1. **Stock List Comparison** - Compare CSV stocks vs Portfolio stocks
2. **Portfolio Value Calculation** - Calculate current portfolio worth
3. **Target Allocation** - Determine new allocation based on GOLDBEES presence
4. **Order Generation** - Create buy/sell orders to match target allocation
5. **Execution** - Execute orders and update portfolio state

### **Error Handling & User Experience:**
```
💡 Below Minimum Investment (< ₹3.95L):
├── Structured error response with suggestions
├── Shows exact shortfall amount
├── Provides recommended minimum with buffer
└── Explains why minimum is required

✅ Valid Investment (≥ ₹3.95L):
├── High utilization (99%+ capital deployed)
├── Balanced allocation across all stocks
├── Every stock gets at least 1 share
└── Optimal risk distribution
```

## 🎨 UI Preview

The dashboard features:
- **Dark glass morphism** effects
- **Smooth animations** and transitions  
- **Professional charts** and metrics
- **Intuitive navigation** and workflow
- **Premium typography** and spacing

## 🔧 Troubleshooting

**Java not found?**
- Install Java 17+ from https://adoptium.net/
- Make sure "Add to PATH" is checked during installation

**Backend connection issues?**
- Ensure Python backend is running on port 8000 (not 8001)
- Check http://localhost:8000 shows API response
- Check http://localhost:8000/api/investment/status for health

**GOLDBEES not showing?**
- Ensure GOLDBEES is present in your CSV stock list
- System automatically detects and applies 50% allocation
- Check logs for NaN handling messages

**Authentication issues?**
- Use manual authentication flow if automatic fails
- CAPTCHA errors require manual token flow
- Check that API credentials are configured in config.py

**Build failures?**
- The startup script uses `-Dskip.npm=true` to avoid React build issues
- This provides a functional dashboard with premium styling

## 📞 Support

- Check that both Python (port 8000) and Java (port 8080) services are running
- Use `START-DASHBOARD.bat` for the simplest startup experience
- The dashboard will guide you through Zerodha authentication
- GOLDBEES support is automatic when present in stock data

---

**Built with Spring Boot + Premium UI Design** 🎉

## 🧹 **Project Cleaned & Optimized**

✅ **Removed unnecessary files:**
- Duplicate batch scripts
- Unused package.json files  
- Empty directories (docs, scripts, tests)
- Virtual environment (using system Python)
- Embedded Node.js (using system Node)
- Legacy frontend directory
- Unrelated notebooks

✅ **Kept essential files:**
- Working startup scripts
- Compiled React build
- Java application files
- Backend API services
- Configuration files

## 🤖 **Claude Code Context & Recent Updates**

### **For Future Claude Code Sessions:**

**Quick Context to Provide:**
> "This is an investment dashboard with Python FastAPI backend (port 8000) and Java Spring Boot frontend (port 8080). Features GOLDBEES ETF integration with 50% allocation, dynamic portfolio allocation, and smart rebalancing. All dependencies are installed and configured. Use START-DASHBOARD.bat to start the complete system."

### **🥇 Recent Major Updates (Latest Session):**

**GOLDBEES Integration (Completed):**
- ✅ **Dynamic Allocation System:** 50% GOLDBEES + equal distribution of remaining 50%
- ✅ **NaN Value Handling:** Proper JSON serialization for GOLDBEES ETF data
- ✅ **Investment Calculator:** Updated for mixed allocation strategies
- ✅ **Authentication:** Manual token flow with callback endpoint
- ✅ **Rebalancing Logic:** Stock list change triggers (not allocation drift)

**Allocation Flexibility Optimization:**
- ✅ **±2% Flexibility:** Upgraded from ±1.5% to ±2% allocation flexibility
- ✅ **78% Reduction in Minimum Investment:** From ₹17.8L to ₹3.95L required
- ✅ **Maximum Allocation Strategy:** Uses 4.5% max allocation for expensive stocks
- ✅ **Affordable for Retail Investors:** Under ₹4L minimum investment
- ✅ **High Utilization:** 99.93% capital utilization with ₹5L investment

**Order Retry System (New):**
- ✅ **Failed Order Detection:** Automatic identification of failed orders
- ✅ **Individual Retry:** Per-order retry buttons with real-time updates
- ✅ **Batch Retry All:** Single-click retry for all failed orders
- ✅ **Retry Limits:** Maximum 3 attempts per order with smart status tracking
- ✅ **Enhanced UI:** Red failed status, failure reasons, and retry controls
- ✅ **No Duplicates:** Fixed retry logic to update existing orders, not create new ones
- ✅ **Production Ready:** Artificial failure simulation removed for production use

**System Logic & Error Handling (Latest):**
- ✅ **Simplified Rebalancing:** Only triggers on stock list changes, not allocation drift
- ✅ **Improved Error Handling:** Structured responses for below-minimum investment
- ✅ **Consistent Status:** Investment status and rebalancing check now aligned
- ✅ **User-Friendly Messages:** Clear explanations and actionable suggestions
- ✅ **Portfolio Status Logic:** BALANCED when stock symbols match CSV

**Key Files Modified:**
- `backend/app/services/investment_calculator.py` - ±2% flexibility & GOLDBEES allocation logic
- `backend/app/services/investment_service.py` - Retry system & simplified rebalancing logic (symbols-only)
- `backend/app/routers/investment.py` - Retry endpoints & improved error handling
- `backend/app/services/csv_service.py` - NaN handling for ETF data  
- `backend/app/main.py` - Auth callback endpoint
- `backend/app/auth.py` - Manual authentication support
- `frontend-java/src/main/java/com/investment/service/InvestmentApiService.java` - Retry API methods
- `frontend-java/src/main/java/com/investment/controller/ApiController.java` - Retry endpoints
- `frontend-java/src/main/frontend/src/hooks/useApi.js` - Retry React hooks
- `frontend-java/src/main/frontend/src/pages/Orders/Orders.js` - Retry UI components

### **Important Paths & Installations:**

**Java & Maven:**
- Java Version: `21.0.8` (Eclipse Adoptium)
- Maven Location: `C:\Users\hspat\scoop\apps\maven\current\`
- Maven Installed Via: Scoop package manager
- Maven Wrapper: Fixed and working in `frontend-java\.mvn\wrapper\`

**Python Dependencies:**
- Python Version: `3.13.5` (System installation)
- All backend dependencies: Installed globally
- Virtual Environment: Not used (removed)

**Node.js & React:**
- Node Version: `v20.10.0` (embedded via Maven)
- React Build: Pre-compiled and cached
- Build Location: `frontend-java\src\main\frontend\build\`

**Project Structure:**
```
📁 Backend (Python FastAPI): backend\
   ├── Port: 8001
   ├── Entry: start_server.py
   └── Dependencies: All installed globally

📁 Frontend (Java Spring Boot + React): frontend-java\
   ├── Port: 8080  
   ├── Maven: mvnw.cmd (wrapper works)
   ├── React: Pre-built in src\main\frontend\build\
   └── Entry: InvestmentDashboardApplication.java
```

**Startup Commands:**
- **Complete Dashboard:** `START-DASHBOARD.bat`
- **Backend Only:** `START-PYTHON-BACKEND.bat`
- **Manual Maven:** `cd frontend-java && mvnw.cmd spring-boot:run`

**Known Working Configurations:**
- Backend runs on port 8000 (corrected from 8001)
- GOLDBEES ETF integration fully working
- React dependencies fixed (use-gesture → @use-gesture/react)
- Portfolio icon fixed (Portfolio → AccountBalance)
- All missing React components created
- Maven wrapper properly configured
- NaN value handling implemented for ETF data
- Authentication supports both manual and automatic flows
- Disk space requirements: ~3GB for full build

**Troubleshooting:**
- If npm install hangs: Use `-Dskip.npm=true` flag
- If React build fails: Dependencies are pre-installed
- If Maven wrapper fails: Use system Maven or run directly
- If ports conflict: Backend must be on 8000, frontend on 8080

### **Working URLs:**
- **Dashboard:** http://localhost:8080
- **Backend API:** http://127.0.0.1:8000
- **API Docs:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health
- **Investment Status:** http://127.0.0.1:8000/api/investment/status
- **CSV Stocks (with GOLDBEES):** http://127.0.0.1:8000/api/investment/csv-stocks

## 🔄 **Order Retry System**

### **Comprehensive Failed Order Management:**
```
🔧 Order Retry Features:
├── Individual Order Retry - Retry specific failed orders
├── Batch Retry All - Retry all failed orders at once
├── Retry Limits - Maximum 3 attempts per order
├── Status Tracking - Real-time retry count and timestamps
└── Failure Analysis - Detailed failure reasons and suggestions
```

### **Retry UI Components:**
- **Failed Orders Summary** - Count and status in dashboard
- **Individual Retry Buttons** - Per-order retry controls
- **"Retry All" Button** - Batch retry for multiple failures
- **Enhanced Status Display** - Red failed status with failure reasons
- **Real-time Updates** - Automatic UI refresh after retry attempts

### **Order Status Lifecycle:**
```
📊 Order States:
├── EXECUTED_SYSTEM ✅ - Successfully executed (PAPER trading)
├── EXECUTED_LIVE ✅ - Successfully executed (Live trading)
├── FAILED ❌ - Order failed, can be retried
└── FAILED_MAX_RETRIES ⚠️ - Exceeded retry limit
```

### **Failure Simulation (Testing Only):**
- **15% Failure Rate** - Configurable for testing retry functionality
- **Multiple Failure Types** - Network timeout, insufficient funds, market closed
- **Production Ready** - Failure simulation disabled in production builds

### **🔧 Key Implementation Details:**

**Authentication Flow:**
- Manual authentication via callback: `http://localhost:8000/auth/callback`
- Automatic authentication (may fail with CAPTCHA)
- Token validation without full re-authentication on startup

**Portfolio Allocation Logic:**
- GOLDBEES detection: Automatic when "GOLDBEES" symbol found in CSV
- Dynamic allocation: 50% GOLDBEES + equal split for remaining stocks
- **±2% Flexibility:** Target ±2% range for optimal allocation (e.g., 2.5% target = 0.5% to 4.5%)
- **Minimum investment:** Uses maximum allocation (4.5%) for expensive stocks = ₹3.95L total
- **Utilization:** Achieves 99.93% capital utilization with optimized allocation
- **Rebalancing trigger:** ONLY stock list changes (add/remove stocks), NOT allocation drift
- **Status logic:** Portfolio is BALANCED if stock symbols match CSV, regardless of allocations

**Order Execution & Retry Logic:**
- **PAPER Trading:** All orders succeed by default (simulation)
- **LIVE Trading:** Ready for Zerodha API integration with real failure handling
- **Retry Mechanism:** Updates existing orders instead of creating duplicates
- **Failure Tracking:** Comprehensive retry count, timestamps, and failure reasons
- **Smart Updates:** Uses `_update_system_orders()` to prevent duplicate orders

**Data Processing:**
- NaN handling: GOLDBEES ETF data cleaned (momentum=0, volatility=0, score=0)
- Live prices: All stocks including GOLDBEES fetched via Zerodha API
- JSON serialization: NaN → null conversion for proper API responses