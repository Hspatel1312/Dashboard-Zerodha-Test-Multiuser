@echo off
title Python Backend - UTF-8 Encoding

echo.
echo ================================================
echo   STARTING PYTHON BACKEND (UTF-8 ENCODING)
echo ================================================
echo.

echo [INFO] Setting UTF-8 encoding environment...
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1

echo [INFO] Changing to backend directory...
cd backend

echo [INFO] Starting Python backend with UTF-8 encoding...
echo [INFO] Backend will be available at: http://127.0.0.1:8000
echo [INFO] API documentation: http://127.0.0.1:8000/docs
echo.

python -c "import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)"

echo.
echo Press any key to exit...
pause >nul