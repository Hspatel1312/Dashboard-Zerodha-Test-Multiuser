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
git commit -m "Update investment dashboard - automated push

- All latest changes to the investment dashboard
- Backend calculations and services updates
- Frontend configuration and source updates
- Documentation and script updates
- Project configuration and cleanup

Generated with Claude Code - Automated Push
Co-Authored-By: Claude <noreply@anthropic.com>"

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