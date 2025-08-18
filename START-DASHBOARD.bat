@echo off
title Investment Dashboard - Professional Java Frontend

echo.
echo ================================================
echo   INVESTMENT REBALANCING DASHBOARD
echo   Professional Java Frontend with Automatic Authentication
echo ================================================
echo.

echo [INFO] Starting Professional Java Frontend Dashboard...
echo [INFO] Features: Automatic Zerodha Authentication, Modern UI, Real-time Data
echo [INFO] Make sure Python backend is running on port 8000
echo.

cd frontend-java

echo [INFO] Setting JAVA_HOME automatically...
for /f "tokens=*" %%i in ('where java 2^>nul') do (
    for %%j in ("%%i") do set JAVA_HOME=%%~dpj..\\
    goto :start_app
)

echo [ERROR] Java not found in PATH. Please install Java 17 or higher.
echo Press any key to exit...
pause >nul
exit /b 1

:start_app
echo [INFO] JAVA_HOME set to: %JAVA_HOME%
echo [INFO] Starting Spring Boot application...
echo.

.\mvnw.cmd spring-boot:run -Dspring-boot.run.jvmArguments="-Xmx1024m"

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo   SUCCESS! Professional Dashboard is running at:
    echo   http://localhost:8080
    echo.
    echo   Features Available:
    echo   - Modern Professional UI Design
    echo   - Automatic Zerodha Authentication (No Manual Token Required!)
    echo   - Real-time Investment Planning and Rebalancing
    echo   - Live Portfolio Tracking and Analytics
    echo   - Advanced Risk Management
    echo ================================================
) else (
    echo.
    echo [ERROR] Application failed to start
    echo [ERROR] Check the error messages above
    echo [INFO] Common issues:
    echo   - Make sure Python backend is running on port 8000
    echo   - Check if port 8080 is already in use
    echo   - Verify Java 17+ is installed
)

echo.
echo Press any key to exit...
pause >nul