@echo off
echo ========================================
echo Investment Dashboard - Push All Changes
echo ========================================
echo.

echo [INFO] Adding ALL files except build/installation directories...

:: Add everything from the directory
git add .

:: Remove build and installation directories from staging
echo [INFO] Excluding build and installation directories...
git reset HEAD frontend-java/src/main/frontend/node_modules/ 2>nul
git reset HEAD frontend-java/src/main/frontend/build/ 2>nul
git reset HEAD frontend-java/src/main/frontend/node/ 2>nul
git reset HEAD frontend-java/target/ 2>nul
git reset HEAD .vscode/ 2>nul

echo.
echo [INFO] What will be committed:
git status --short

echo.
echo [INFO] Creating commit...
git commit -m "Update investment dashboard - automated push" -m "All latest changes to the investment dashboard" -m "Backend calculations and services updates" -m "Frontend configuration and source updates" -m "Generated with Claude Code"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Changes committed successfully!
    echo [INFO] Getting current branch name...
    for /f %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
    echo [INFO] Current branch: %CURRENT_BRANCH%
    echo [INFO] Pushing to GitHub branch %CURRENT_BRANCH%...
    git push origin %CURRENT_BRANCH%
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] All changes pushed to GitHub branch %CURRENT_BRANCH% successfully!
        echo [INFO] Repository is now up to date.
        echo [INFO] View changes at: https://github.com/Hspatel1312/Dashboard-Zerodha-Test-Multiuser/tree/%CURRENT_BRANCH%
    ) else (
        echo.
        echo [ERROR] Failed to push to GitHub. Check your internet connection.
        echo [INFO] You may need to set upstream: git push -u origin %CURRENT_BRANCH%
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