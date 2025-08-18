@echo off
title Investment Dashboard - FAST MODE (Skip Frontend Build)

echo.
echo ================================================
echo   INVESTMENT REBALANCING DASHBOARD - FAST MODE
echo   Professional Java Frontend (Uses Existing Build)
echo ================================================
echo.

echo [INFO] Starting Dashboard in FAST MODE...
echo [INFO] This skips the React build process for faster startup
echo [INFO] Make sure Python backend is running on port 8000
echo.

cd frontend-java

echo [INFO] Setting JAVA_HOME automatically...
for /f "tokens=*" %%i in ('where java 2^>nul') do (
    for %%j in ("%%i") do set JAVA_HOME=%%~dpj..\
    goto :start_app
)

echo [ERROR] Java not found in PATH. Please install Java 17 or higher.
echo Press any key to exit...
pause >nul
exit /b 1

:start_app
echo [INFO] JAVA_HOME set to: %JAVA_HOME%
echo [INFO] Starting Spring Boot application (FAST MODE - No React Build)...
echo.

.\mvnw.cmd spring-boot:run -Dskip.npm.build=true

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo   SUCCESS! Professional Dashboard is running at:
    echo   http://localhost:8080
    echo.
    echo   FAST MODE: Using existing React build
    echo   If you made frontend changes, use START-DASHBOARD.bat instead
    echo ================================================
) else (
    echo.
    echo [ERROR] Application failed to start
    echo [ERROR] Check the error messages above
)

echo.
echo Press any key to exit...
pause >nul