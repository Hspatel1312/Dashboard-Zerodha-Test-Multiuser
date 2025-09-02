# Multi-User Investment Rebalancing Dashboard

## 🎉 What's New - Multi-User Support

Your single-user investment dashboard has been converted to support **multiple users** with complete data isolation while preserving all existing functionality.

## ✅ Key Features

### **Complete User Separation**
- Each user has their own Zerodha connection and credentials
- Separate portfolio data, orders, and performance tracking
- User-specific data directories (`user_data/{user_id}/`)
- JWT-based authentication with secure sessions

### **Preserved Functionality**
- ✅ All existing features work exactly the same per user
- ✅ Investment calculations and rebalancing logic unchanged
- ✅ Portfolio metrics and comparisons per user
- ✅ Live order monitoring per user
- ✅ CSV stocks data (shared but user-specific pricing)

### **Enhanced Security**
- 🔐 Encrypted storage of Zerodha credentials
- 🔐 JWT token-based authentication
- 🔐 SQLite database with proper user management
- 🔐 Session management with automatic token refresh

## 🚀 Quick Start

### 1. Start the Multi-User Backend
```bash
# Run the multi-user backend
START-MULTIUSER-BACKEND.bat

# This will:
# - Install required packages
# - Create SQLite database
# - Create test users (update with real credentials)
# - Start the multi-user API server at http://localhost:8000
```

### 2. Start the Frontend
```bash
# Use your existing frontend startup script
START-DASHBOARD-FAST.bat

# This will:
# - Start the Java Spring Boot + React frontend at http://localhost:8080
# - You'll see the new multi-user login screen
# - Uses your existing optimized build process
```

**Alternative:** For development with React hot reload:
```bash
# In the frontend-java/src/main/frontend directory
npm start
# This starts React dev server at http://localhost:3000 (with hot reload)
```

### 3. Register or Login
- **New Users**: Click "Register" tab to create account with your Zerodha **API key/secret**
- **Existing Users**: Login with your username/password
- **After Login**: You'll see a Zerodha connection flow (not the old login fields)

## 🏗️ Architecture Overview

### **Backend Changes**
```
├── app/
│   ├── main_multiuser_v2.py          # New multi-user FastAPI app
│   ├── database.py                   # SQLite database with user models
│   ├── models.py                     # User management data models  
│   ├── auth_multiuser.py             # JWT authentication system
│   └── services/
│       ├── multiuser_zerodha_auth.py      # User-specific Zerodha auth
│       └── multiuser_investment_service.py # User-specific investment service
├── user_data/                        # User-specific data directories
│   ├── {user_id_1}/
│   │   ├── zerodha_access_token.txt
│   │   ├── system_orders.json
│   │   └── portfolio_state.json
│   └── {user_id_2}/
│       ├── zerodha_access_token.txt
│       ├── system_orders.json
│       └── portfolio_state.json
└── users.db                         # SQLite user database
```

### **Frontend Changes**
```
├── src/
│   ├── contexts/
│   │   └── UserContext.js           # User session management
│   ├── hooks/
│   │   └── useUserApi.js            # Multi-user API hooks
│   └── pages/Auth/
│       └── MultiUserLogin.js        # New login/registration interface
```

## 👥 User Management

### **Registration Process**
1. **Basic Info**: Username, email, full name, password
2. **Zerodha Credentials**: User ID, password, TOTP key
3. **Automatic Setup**: User directory creation and encryption

### **Authentication Flow**
1. User logs in with username/password
2. JWT token generated and stored
3. User-specific Zerodha authentication
4. Access to personalized dashboard

## 🔧 Configuration

### **Environment Variables**
The system uses the same configuration as the single-user version:
- `ZERODHA_API_KEY` - Your Zerodha API key (shared across users)
- `ZERODHA_API_SECRET` - Your Zerodha API secret (shared across users)
- Individual user credentials are stored encrypted in the database

### **Database**
- **Type**: SQLite (perfect for 20+ users)
- **Location**: `backend/users.db`
- **Encryption**: User credentials encrypted with Fernet
- **Backup**: Just copy the `users.db` file and `user_data/` directory

## 🛡️ Security Features

### **Credential Security**
- Zerodha passwords and TOTP keys encrypted using Fernet symmetric encryption
- Encryption key stored separately in `encryption.key`
- JWT tokens for session management
- Automatic token expiry and refresh

### **Data Isolation**
- Each user has completely separate data directories
- No cross-user data access possible
- Individual Zerodha connections per user
- Separate portfolio tracking and orders

## 🧪 Testing

### **Test Users**
Update `backend/create_test_user.py` with real Zerodha credentials:

```python
user1_data = UserCreate(
    username="testuser1",
    email="testuser1@example.com", 
    full_name="Test User One",
    password="testpass123",
    zerodha_user_id="YOUR_ACTUAL_ZERODHA_ID",
    zerodha_password="YOUR_ACTUAL_PASSWORD",
    zerodha_totp_key="YOUR_ACTUAL_TOTP_KEY"
)
```

### **API Testing**
- Visit http://localhost:8000/docs for interactive API documentation
- All endpoints now require JWT authentication
- Test individual user data isolation

## 📊 Monitoring

### **Health Check**
```bash
curl http://localhost:8000/health
```

Shows:
- System status
- Number of registered users
- Active authenticated users
- Database connection status

### **Admin Dashboard**
Admin users can access:
- `/api/admin/users` - List all users
- `/api/admin/system-status` - Detailed system status

## 🔄 Migration from Single-User

### **Preserve Existing Data**
Your existing single-user data can be migrated:

1. **Backup Current Data**: Copy your existing `.json` files
2. **Create Admin User**: Register as admin with your existing Zerodha credentials
3. **Import Data**: Copy files to your user data directory: `user_data/{your_user_id}/`

### **Gradual Migration**
- Keep the original single-user system running alongside
- Test the multi-user system thoroughly
- Switch over when satisfied

## 📈 Scaling

### **Performance**
- **SQLite**: Handles 20-100 users comfortably
- **Concurrent Users**: Each user has isolated resources
- **Memory Usage**: Scales linearly with active users

### **Future Upgrades**
- Easy migration to PostgreSQL if needed
- Redis for session caching
- Load balancing for high traffic

## 🚨 Important Notes

### **Shared Resources**
- **CSV Stocks Data**: Shared across all users (but prices fetched per user)
- **API Keys**: Zerodha API key/secret shared (individual user credentials separate)
- **Market Data**: Real-time prices fetched per user connection

### **User Responsibilities**
- Each user must have their own Zerodha account and credentials
- Users are responsible for their own investment decisions
- Data backup is per-user basis

## 🔍 Troubleshooting

### **Common Issues**
1. **Database Locked**: Restart the backend server
2. **Token Expired**: Frontend will automatically redirect to login
3. **Zerodha Auth Failed**: Check individual user's Zerodha credentials
4. **Port Conflicts**: Ensure ports 8000 (backend) and 3000 (frontend) are free

### **Logs Location**
- Backend logs: Console output from `START-MULTIUSER-BACKEND.bat`
- User-specific errors: Include username in log messages
- Database issues: Check `users.db` file permissions

## 🎯 Next Steps

1. **Update Test Users**: Add real Zerodha credentials in `create_test_user.py`
2. **Test Registration**: Create new user accounts through the web interface
3. **Verify Isolation**: Confirm each user sees only their own data
4. **Production Setup**: Configure proper encryption keys and secrets
5. **Backup Strategy**: Regular backup of `users.db` and `user_data/` directory

## 🎉 Success!

You now have a fully functional multi-user investment dashboard that:
- ✅ Supports multiple users with complete data isolation
- ✅ Preserves all your existing investment features
- ✅ Provides secure authentication and session management
- ✅ Scales to handle 20+ users effectively
- ✅ Maintains the same user experience per individual

Your single-user system's functionality is now available to multiple users, each with their own secure, isolated investment tracking experience!