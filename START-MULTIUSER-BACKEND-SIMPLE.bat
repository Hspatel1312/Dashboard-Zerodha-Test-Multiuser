@echo off
title Multi-User Investment Backend - Simple Start

echo.
echo ================================================
echo   STARTING MULTI-USER BACKEND (SIMPLE MODE)
echo ================================================
echo.

echo [INFO] Setting UTF-8 encoding environment...
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1

echo [INFO] Changing to backend directory...
cd backend

echo [INFO] Installing required packages...
pip install -r requirements_multiuser.txt

echo [INFO] Ensuring database exists (no reset)...
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine); print('Database ready!')"

echo [INFO] Starting Multi-User Backend...
echo [INFO] Backend will be available at: http://127.0.0.1:8000
echo [INFO] API documentation: http://127.0.0.1:8000/docs
echo [INFO] Register new users via the web interface
echo.

python -c "from app.main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000, reload=True)"

echo.
echo Press any key to exit...
pause >nul