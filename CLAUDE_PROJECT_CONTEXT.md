# Claude Project Context - Multi-User Investment Dashboard

> **PURPOSE**: This file provides complete context for Claude to understand the project structure, functionality, and technical details without requiring additional context.

## 🎯 PROJECT OVERVIEW

**Name**: Multi-User Investment Rebalancing WebApp  
**Type**: Professional investment portfolio management system  
**Architecture**: FastAPI (Python) backend + React (TypeScript/JavaScript) frontend  
**Purpose**: Automated portfolio rebalancing with Zerodha broker integration  
**Users**: Multiple users with individual accounts and portfolios  

## 🏗️ CURRENT PROJECT STRUCTURE

```
investment-rebalancing-webapp - java/
├── README.md                          # Main documentation
├── CLAUDE_PROJECT_CONTEXT.md          # This file - complete project context
├── PUSH-CHANGES.bat                   # Git automation script
├── START-MULTIUSER-BACKEND-SIMPLE.bat # Backend startup (PORT 8000)
├── START-DIRECT-FRONTEND.bat          # Frontend startup (PORT 3000)
│
├── 🚀 backend/                        # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py                    # PRIMARY ENTRY POINT (was main_multiuser_v2.py)
│   │   ├── models.py                  # Pydantic models for API
│   │   ├── database.py                # SQLAlchemy database setup
│   │   ├── auth_multiuser.py          # JWT authentication system
│   │   ├── config.py                  # Configuration settings
│   │   ├── routers/
│   │   │   └── investment.py          # API endpoints (legacy, most in main.py)
│   │   └── services/                  # Business logic services
│   │       ├── multiuser_investment_service.py    # CORE: User investment logic
│   │       ├── multiuser_zerodha_auth.py          # Zerodha API authentication
│   │       ├── csv_service.py                     # CSV data processing
│   │       ├── investment_calculator.py           # Portfolio calculations
│   │       ├── portfolio_metrics_service.py       # Portfolio analytics
│   │       ├── live_order_service.py             # Order execution & monitoring
│   │       └── portfolio_comparison_service.py    # Portfolio analysis
│   ├── requirements_multiuser.txt     # Python dependencies
│   ├── users.db                      # SQLite database (user accounts)
│   ├── csv_cache.json               # Cached stock data from CSV
│   └── user_data/                   # User-specific data storage
│       └── {user-uuid}/             # Individual user folders
│           ├── system_orders.json   # User's investment orders
│           ├── zerodha_access_token.txt # User's Zerodha token
│           └── *.json              # Other user-specific files
│
├── 📱 frontend-java/                  # React Frontend (Java Maven wrapper)
│   ├── pom.xml                       # Maven configuration
│   └── src/main/
│       ├── java/                     # Java wrapper (minimal)
│       └── frontend/                 # MAIN REACT APPLICATION
│           ├── package.json          # Node.js dependencies
│           ├── src/
│           │   ├── App.js           # Main React app
│           │   ├── components/      # Reusable React components
│           │   │   ├── Auth/        # Authentication components
│           │   │   └── Layout/      # Layout components
│           │   ├── contexts/        # React contexts
│           │   │   └── UserContext.js # User state management
│           │   ├── hooks/           # Custom React hooks
│           │   │   ├── useUserApi.js    # MAIN API hooks for multiuser
│           │   │   └── useApi.js        # Legacy API hooks
│           │   └── pages/           # Main application pages
│           │       ├── Auth/        # Login/Registration
│           │       ├── Dashboard/   # Main dashboard
│           │       ├── Portfolio/   # Portfolio management
│           │       ├── Orders/      # Order tracking
│           │       └── Stocks/      # Stock data display
│           └── public/              # Static assets
│
└── 📦 archive/                       # Organized legacy & tools
    ├── legacy-singleuser/           # Old single-user version
    ├── test-scripts/                # Testing utilities & mock data
    └── docs/                        # Detailed technical documentation
```

## 🔑 KEY TECHNICAL DETAILS

### **Backend Architecture**
- **Framework**: FastAPI 3.0.0
- **Database**: SQLAlchemy + SQLite (`users.db`)
- **Authentication**: JWT tokens with bcrypt password hashing
- **API Integration**: Zerodha Kite API for live trading
- **Data Storage**: User-isolated JSON files in `user_data/{uuid}/`
- **Ports**: Backend runs on 8000 (startup script) or 8002 (manual)

### **Frontend Architecture**
- **Framework**: React with Material-UI components
- **State Management**: React Context + React Query for API calls
- **Authentication**: JWT tokens stored in browser
- **API Communication**: Axios-based hooks in `useUserApi.js`
- **Styling**: Material-UI with custom dark theme
- **Build System**: Node.js + Maven wrapper

### **Key API Endpoints** (in `main.py`):
```
POST /api/register                    # User registration
POST /api/login                       # User login
GET  /api/auth-status                 # Check authentication
GET  /api/investment/status           # Portfolio status
GET  /api/investment/portfolio-status # Detailed portfolio data
GET  /api/investment/orders-with-retries # Order management
POST /api/investment/calculate-rebalancing # Rebalancing calculation
POST /api/investment/execute-rebalancing   # Execute rebalancing
```

## 🎯 CORE FUNCTIONALITY

### **1. Multi-User System**
- Individual user accounts with secure authentication
- Isolated data storage per user (UUID-based folders)
- Individual Zerodha connections per user
- Separate portfolios and order history

### **2. Investment Flow**
1. **Registration/Login**: User creates account and logs in
2. **Zerodha Connection**: User connects their Zerodha account via API key/token
3. **CSV Target Setup**: System fetches stock targets from GitHub CSV
4. **Initial Investment**: Calculate and execute initial portfolio
5. **Monitoring**: Track portfolio performance and holdings
6. **Rebalancing**: Detect when portfolio needs rebalancing based on CSV changes
7. **Order Management**: Execute and track all buy/sell orders

### **3. Portfolio Management**
- **Live Data**: Real-time stock prices from Zerodha API
- **Holdings Display**: Current portfolio holdings with P&L
- **Rebalancing Logic**: Automatic detection of portfolio drift
- **Order Tracking**: Complete order history with retry mechanism
- **Performance Analytics**: Portfolio metrics and comparisons

## 🔧 CURRENT WORKING STATUS

### **✅ Fully Working Features**:
- Multi-user registration and authentication
- Zerodha API integration and authentication
- Portfolio holdings display and calculation
- Order management with detailed status tracking
- Rebalancing detection and calculation
- Live price fetching from Zerodha
- Professional UI with all pages functional

### **⚠️ Known Technical Notes**:
- **Cache Management**: Python bytecode cache can cause issues - clear with `rm -rf __pycache__`
- **Token Issues**: Zerodha tokens need periodic refresh
- **Order Execution**: Orders show PENDING status due to Zerodha API limitations in development
- **Data Structure**: Holdings exposed at `data.holdings` level for frontend compatibility

### **🎯 Recent Major Changes** (Sept 2024):
- Converted from single-user to multi-user architecture
- Fixed frontend-backend data structure alignment for holdings display
- Cleaned and professionalized project structure
- Moved legacy code to organized archive structure
- Standardized entry points (`main.py` is primary)

## 🚀 HOW TO START THE SYSTEM

### **Method 1: Use Startup Scripts**
```bash
# Start backend (port 8000)
./START-MULTIUSER-BACKEND-SIMPLE.bat

# Start frontend (port 3000) - separate terminal
./START-DIRECT-FRONTEND.bat
```

### **Method 2: Manual Start**
```bash
# Backend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

# Frontend
cd frontend-java/src/main/frontend
npm start
```

### **Access Points**:
- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8000 or 8002
- API Docs: http://127.0.0.1:8000/docs

## 🔍 DEBUGGING TIPS FOR CLAUDE

### **Common Issues & Solutions**:
1. **Holdings Not Displaying**: Check data structure alignment between backend (`portfolio_summary.holdings`) and frontend (`data.holdings`)
2. **Cache Issues**: Clear Python cache: `rm -rf __pycache__ app/__pycache__ app/services/__pycache__`
3. **Port Conflicts**: Backend can run on 8000 (scripts) or 8002 (manual)
4. **Authentication Issues**: Check JWT token validity and user session state
5. **API Connection**: Verify Zerodha token is valid and not expired

### **Key Files to Check**:
- **Backend Logic**: `backend/app/services/multiuser_investment_service.py`
- **API Endpoints**: `backend/app/main.py`
- **Frontend API**: `frontend-java/src/main/frontend/src/hooks/useUserApi.js`
- **User Data**: `backend/user_data/{uuid}/system_orders.json`

### **Logging Locations**:
- Backend logs appear in terminal running uvicorn
- Frontend logs in browser console
- User data stored in JSON files in `backend/user_data/`

## 📚 ADDITIONAL CONTEXT

### **Data Flow**:
```
CSV GitHub → Backend Cache → Investment Calculator → Portfolio Status → Frontend Display
                ↓
Zerodha API → Live Prices → Order Execution → Order Tracking → Status Updates
```

### **File Naming Conventions**:
- `main.py` = Primary backend entry (multi-user)
- `*_multiuser.py` = Multi-user specific files
- `useUserApi.js` = Frontend hooks for multi-user API
- `{uuid}/` folders = User-specific data isolation

### **Technology Stack**:
- **Backend**: Python 3.7+, FastAPI, SQLAlchemy, bcrypt, requests
- **Frontend**: React 18, Material-UI, React Query, Axios
- **Database**: SQLite for users, JSON files for user data
- **Integration**: Zerodha Kite API for live trading
- **Build**: Maven (wrapper), Node.js, Python pip

---

**This file contains everything Claude needs to understand and work with this project effectively. Refer to this file at the start of any new session for complete context.**