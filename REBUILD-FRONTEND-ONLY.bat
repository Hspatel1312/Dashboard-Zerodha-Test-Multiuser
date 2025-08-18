@echo off
title Rebuild Frontend Only - React Build

echo.
echo ================================================
echo   REBUILD FRONTEND ONLY
echo   Fast React Build with Optimizations
echo ================================================
echo.

echo [INFO] Building React frontend with optimizations...
echo [INFO] This will take 30-60 seconds (much faster than full build)
echo.

cd frontend-java\src\main\frontend

echo [INFO] Running optimized React build...
call npm run build:fast

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo   SUCCESS! Frontend build completed
    echo   You can now use START-DASHBOARD-FAST.bat for quick startup
    echo ================================================
) else (
    echo.
    echo [ERROR] Frontend build failed
    echo [ERROR] Check the error messages above
)

echo.
echo Press any key to exit...
pause >nul