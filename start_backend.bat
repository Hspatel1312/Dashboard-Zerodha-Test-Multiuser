REM =============================================================================
REM File: start_backend.bat
REM =============================================================================
@echo off
echo 🔧 Starting Backend Server...

REM Check if we're in the right directory
if not exist "backend\app\main.py" (
    echo ❌ Please run this script from the project root directory
    pause
    exit /b 1
)

REM Activate virtual environment and start backend
call venv\Scripts\activate.bat
cd backend
echo ✅ Starting backend with uvicorn...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

REM =============================================================================
REM File: start_frontend.bat  
REM =============================================================================
@echo off
echo 🎨 Starting Frontend Dashboard...

REM Check if we're in the right directory
if not exist "frontend\streamlit_app.py" (
    echo ❌ Please run this script from the project root directory
    pause
    exit /b 1
)

REM Activate virtual environment and start frontend
call venv\Scripts\activate.bat
cd frontend
echo ✅ Starting frontend with streamlit...
python -m streamlit run streamlit_app.py

REM =============================================================================
REM File: install_deps.bat
REM =============================================================================
@echo off
echo 📦 Installing All Dependencies...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install backend dependencies
echo 📦 Installing backend dependencies...
cd backend
pip install -r requirements.txt

REM Install frontend dependencies  
echo 📦 Installing frontend dependencies...
cd ..\frontend
pip install -r requirements.txt

REM Go back to root
cd ..

echo ✅ All dependencies installed!
echo.
echo 🚀 Now you can run:
echo    - startup.bat (starts both)
echo    - start_backend.bat (backend only)
echo    - start_frontend.bat (frontend only)
echo.
pause