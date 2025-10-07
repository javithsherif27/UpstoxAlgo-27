@echo off
cd /d "%~dp0"
:start
echo.
echo ================================================
echo       UpstoxAlgo Development Launcher
echo ================================================
echo.
echo Choose your development environment:
echo.
echo [1] Full Stack with LocalStack (Recommended)
echo     - LocalStack + Backend + Frontend
echo     - Complete local AWS services
echo     - Best for development and testing
echo.
echo [2] LocalStack Only
echo     - Start/Stop LocalStack services
echo     - DynamoDB, S3 locally available
echo     - Manual backend/frontend start
echo.  
echo [3] Backend Only
echo     - FastAPI server on port 8000
echo     - Auto-detects LocalStack if running
echo     - Manual database setup required
echo.
echo [4] Frontend Only  
echo     - Vite dev server on port 5173
echo     - Requires backend to be running
echo     - UI development mode
echo.
echo [5] Legacy Mode (No LocalStack)
echo     - Backend + Frontend only
echo     - Uses production AWS or local cache
echo     - Original start-all.bat behavior
echo.
echo [0] Exit
echo.
set /p choice="Enter your choice (0-5): "

if "%choice%"=="1" (
    echo Starting Full Stack with LocalStack...
    call "%~dp0start-local.bat"
) else if "%choice%"=="2" (
    echo.
    echo [A] Start LocalStack
    echo [B] Stop LocalStack  
    echo [C] LocalStack Status
    set /p sub="Choose action (A/B/C): "
    if /i "%sub%"=="A" call "%~dp0start-localstack.bat"
    if /i "%sub%"=="B" call "%~dp0stop-localstack.bat"
    if /i "%sub%"=="C" (
        echo Checking LocalStack status...
        curl -s http://localhost:4566/_localstack/health
        echo.
        pause
    )
) else if "%choice%"=="3" (
    call "%~dp0start-backend.bat"
) else if "%choice%"=="4" (
    call "%~dp0start-frontend.bat"
) else if "%choice%"=="5" (
    call "%~dp0start-all.bat"
) else if "%choice%"=="0" (
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    pause
    goto start
)

echo.
echo Press any key to show menu again or close window to exit...
pause >nul
goto start