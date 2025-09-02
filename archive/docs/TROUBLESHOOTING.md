# Multi-User System Troubleshooting

## 🔧 Common Issues & Solutions

### **Issue 1: Database File Locked**
```
❌ [WinError 32] The process cannot access the file because it is being used by another process: 'users.db'
```

**Solutions:**
1. **Close any running backend servers** (Ctrl+C in command prompts)
2. **Close database browsers** (DB Browser for SQLite, etc.)
3. **Use simple startup**: `START-MULTIUSER-BACKEND-SIMPLE.bat`
4. **Manual fix**:
   ```bash
   cd backend
   python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

### **Issue 2: Import Errors**
```
❌ ModuleNotFoundError: No module named 'app.something'
```

**Solutions:**
1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements_multiuser.txt
   ```
2. **Check Python path**: Make sure you're in the `backend` directory

### **Issue 3: Login Screen Shows Old Fields**
```
❌ Still seeing Zerodha ID/TOTP fields after login
```

**Solutions:**
1. **Clear browser cache** and refresh
2. **Check you're using the right frontend**: `START-DASHBOARD-FAST.bat`
3. **Rebuild frontend**:
   ```bash
   REBUILD-FRONTEND-ONLY.bat
   START-DASHBOARD-FAST.bat
   ```

### **Issue 4: Registration Fails**
```
❌ Username already exists / Email already exists
```

**Solutions:**
1. **Use different username/email**
2. **Reset database** (if testing):
   ```bash
   cd backend
   python reset_database.py
   ```

### **Issue 5: API Key/Secret Not Working**
```
❌ Authentication failed / Invalid API credentials
```

**Solutions:**
1. **Check API credentials** at https://developers.zerodha.com/
2. **Verify API key format**: Should be alphanumeric (e.g., `abc123def456`)
3. **Check API secret**: Usually longer alphanumeric string
4. **Ensure app is active** in Zerodha developer console

### **Issue 6: Port Already in Use**
```
❌ Port 8000 is already in use
```

**Solutions:**
1. **Find and kill process**:
   ```bash
   netstat -ano | findstr :8000
   taskkill /PID [PID_NUMBER] /F
   ```
2. **Use different port**: Edit the startup script to use port 8001

### **Issue 7: Frontend Won't Connect to Backend**
```
❌ Network Error / Connection refused
```

**Solutions:**
1. **Check backend is running** at http://localhost:8000/health
2. **Check frontend proxy** in `package.json`: should be `"proxy": "http://localhost:8000"`
3. **Restart both services**

## 🚀 Quick Start (When Things Break)

### **Clean Restart:**
1. **Close all command prompts**
2. **Delete files** (if needed):
   - `backend/users.db`
   - `backend/encryption.key`
   - `backend/user_data/` folder
3. **Start fresh**:
   ```bash
   START-MULTIUSER-BACKEND-SIMPLE.bat
   START-DASHBOARD-FAST.bat
   ```

### **Emergency Manual Start:**
```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements_multiuser.txt
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
python -c "from app.main_multiuser_v2 import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"

# Terminal 2 - Frontend
START-DASHBOARD-FAST.bat
```

## 🔍 Debug Information

### **Check System Status:**
```bash
# Backend health
curl http://localhost:8000/health

# Database status
cd backend
python test_multiuser_system.py
```

### **Verify Setup:**
1. **Backend**: http://localhost:8000 should show API info
2. **Frontend**: http://localhost:8080 should show login screen
3. **API Docs**: http://localhost:8000/docs should show API documentation

## 📞 Getting Help

### **Log Information to Include:**
1. **Full error messages** from command prompt
2. **Browser console errors** (F12 → Console)
3. **Python version**: `python --version`
4. **Node version**: `node --version`
5. **Which startup script you used**

### **Quick Diagnostic:**
```bash
cd backend
python test_multiuser_system.py
```

This will test all major components and show which parts are working/failing.