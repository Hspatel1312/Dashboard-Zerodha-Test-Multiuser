# 🚀 Investment Dashboard - Premium UI

A modern investment rebalancing dashboard with Apple/Tesla-inspired design.

## ⚡ Quick Start

### 1. Start Python Backend
```bash
cd backend
python -c "import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8001, reload=True)"
```

### 2. Start Java Frontend
**Double-click `START-DASHBOARD.bat`** or run:
```bash
cd frontend-java
.\mvnw.cmd spring-boot:run -Dskip.npm=true
```

### 3. Open Dashboard
http://localhost:8080

## 🎯 Features

- ✨ **Premium Dark UI** - Apple/Tesla inspired design
- 🔐 **Zerodha Integration** - Secure authentication flow  
- 📊 **Live Portfolio Tracking** - Real-time data and charts
- 📱 **Responsive Design** - Works on all devices
- ⚡ **Fast Performance** - Optimized for speed

## 🛠️ Requirements

- **Java 17+** - [Download from Adoptium](https://adoptium.net/)
- **Python 3.9+** - For backend API
- **Internet Connection** - For Maven dependencies

## 📋 Project Structure

```
├── backend/                    # Python FastAPI backend
├── frontend-java/             # Java Spring Boot + React frontend
│   ├── src/main/java/        # Java controllers and services
│   ├── src/main/resources/   # Static web resources
│   └── mvnw.cmd             # Maven wrapper (no Maven install needed)
└── START-DASHBOARD.bat       # One-click startup script
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
- Ensure Python backend is running on port 8001
- Check http://localhost:8001 shows API response

**Build failures?**
- The startup script uses `-Dskip.npm=true` to avoid React build issues
- This provides a functional dashboard with premium styling

## 📞 Support

- Check that both Python (port 8001) and Java (port 8080) services are running
- Use `START-DASHBOARD.bat` for the simplest startup experience
- The dashboard will guide you through Zerodha authentication

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

## 🤖 **Claude Code Context & Paths**

### **For Future Claude Code Sessions:**

**Quick Context to Provide:**
> "This is an investment dashboard with Python FastAPI backend (port 8001) and Java Spring Boot frontend (port 8080). All dependencies are installed and configured. Use START-DASHBOARD.bat to start the complete system."

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
- Backend runs on port 8001 (not 8000)
- React dependencies fixed (use-gesture → @use-gesture/react)
- Portfolio icon fixed (Portfolio → AccountBalance)
- All missing React components created
- Maven wrapper properly configured
- Disk space requirements: ~3GB for full build

**Troubleshooting:**
- If npm install hangs: Use `-Dskip.npm=true` flag
- If React build fails: Dependencies are pre-installed
- If Maven wrapper fails: Use system Maven or run directly
- If ports conflict: Backend must be on 8001, frontend on 8080

### **Working URLs:**
- **Dashboard:** http://localhost:8080
- **Backend API:** http://127.0.0.1:8001
- **API Docs:** http://127.0.0.1:8001/docs
- **Health Check:** http://127.0.0.1:8001/health