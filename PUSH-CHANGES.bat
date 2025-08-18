@echo off
echo ========================================
echo Investment Dashboard - Push Changes
echo ========================================
echo.

echo [INFO] Adding all source code and configuration files...

:: Add all important source files
git add backend/app/
git add backend/*.py
git add backend/*.json
git add backend/*.txt
git add backend/requirements.txt
git add *.md
git add *.bat
git add frontend-java/src/main/java/
git add frontend-java/src/main/resources/
git add frontend-java/pom.xml
git add frontend-java/README.md
git add frontend-java/mvnw.cmd

:: Add frontend React source files (not build artifacts)
git add frontend-java/src/main/frontend/src/
git add frontend-java/src/main/frontend/public/
git add frontend-java/src/main/frontend/package.json

echo.
echo [INFO] Checking what will be committed...
git status --porcelain

echo.
echo [INFO] Creating commit with timestamp...
set timestamp=%date:~10,4%-%date:~4,2%-%date:~7,2% %time:~0,2%:%time:~3,2%
set "commit_msg=Update investment dashboard - %timestamp%

- Latest changes to backend services and calculations
- Frontend updates and configuration changes
- Updated documentation and scripts

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "%commit_msg%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Changes committed successfully!
    echo [INFO] Pushing to GitHub...
    git push origin main
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] All changes pushed to GitHub successfully!
        echo [INFO] Repository is now up to date.
    ) else (
        echo.
        echo [ERROR] Failed to push to GitHub. Check your internet connection.
    )
) else (
    echo.
    echo [INFO] No changes to commit or commit failed.
)

echo.
echo [INFO] Current repository status:
git status --short

echo.
echo ========================================
echo Push operation completed!
echo ========================================
pause