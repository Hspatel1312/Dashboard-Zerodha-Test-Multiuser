# Multi-User Investment Rebalancing WebApp

A professional multi-user investment portfolio management and rebalancing system with Zerodha integration.

## Features

- **Multi-User Authentication**: Secure user registration and login
- **Zerodha Integration**: Direct API connection for live trading
- **Portfolio Management**: Real-time holdings tracking and analysis
- **Automatic Rebalancing**: Smart portfolio rebalancing based on CSV targets
- **Order Management**: Comprehensive order tracking with retry system
- **Live Price Data**: Real-time stock prices from Zerodha
- **Professional UI**: Modern React-based frontend with Material-UI

## Quick Start

### Prerequisites
- Python 3.7+
- Node.js 16+
- Java 11+
- Maven 3.6+

### 1. Start Backend
```bash
./START-MULTIUSER-BACKEND-SIMPLE.bat
```
Backend will be available at: http://127.0.0.1:8000

### 2. Start Frontend
```bash
./START-DIRECT-FRONTEND.bat
```
Frontend will be available at: http://localhost:3000

### 3. Register & Login
1. Open http://localhost:3000
2. Click "Register" to create new account
3. Login with your credentials
4. Connect your Zerodha account

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Main application entry
│   │   ├── models.py       # Database models
│   │   ├── auth_multiuser.py # Authentication system
│   │   └── services/       # Business logic services
│   ├── requirements_multiuser.txt
│   └── users.db            # SQLite database
├── frontend-java/          # React frontend + Java wrapper
│   └── src/main/frontend/  # React application
├── archive/                # Legacy and test files
│   ├── legacy-singleuser/  # Single-user version
│   ├── test-scripts/       # Testing utilities
│   └── docs/              # Additional documentation
└── *.bat                  # Startup scripts
```

## Usage

1. **Portfolio Setup**: Upload your stock allocation CSV
2. **Initial Investment**: Calculate and execute initial investment plan
3. **Rebalancing**: Automatically detect when rebalancing is needed
4. **Order Tracking**: Monitor all orders with detailed status information
5. **Holdings View**: View your current portfolio holdings and performance

## API Documentation

Once backend is running, visit: http://127.0.0.1:8000/docs

## Support

For detailed documentation and troubleshooting, see `archive/docs/`

---

*Built with FastAPI, React, and Zerodha API*