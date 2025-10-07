@echo off
echo Starting Local Development Environment...
echo.
echo This script starts services in optimal order:
echo 1. LocalStack (AWS services)
echo 2. Backend API
echo 3. Frontend UI
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Start LocalStack
echo [Step 1/3] Starting LocalStack...
call start-localstack.bat

echo.
echo [Step 2/3] Installing backend dependencies...
cd /d "%~dp0"
D:/source-code/UpstoxAlgo-27/.venv/Scripts/pip.exe install -r backend/requirements.txt

REM Check Node.js availability
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Node.js not found. Frontend will not start.
    echo Please install Node.js from: https://nodejs.org/
    echo Or run: setup-frontend.bat for guided setup
    echo.
    echo Starting backend only...
    set FRONTEND_AVAILABLE=false
) else (
    echo Node.js found: 
    node --version
    set FRONTEND_AVAILABLE=true
)

REM Start backend
echo [Step 3/3] Starting application servers...
start "Backend API" cmd /c "cd /d %~dp0 && D:/source-code/UpstoxAlgo-27/.venv/Scripts/python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"

REM Wait and start frontend if available
timeout /t 3 /nobreak >nul
if "%FRONTEND_AVAILABLE%"=="true" (
    start "Frontend UI" cmd /c "cd /d %~dp0 && call start-frontend.bat"
) else (
    echo Skipping frontend start - Node.js not available
)

echo.
echo ====================================
echo   LOCAL DEVELOPMENT READY!
echo ====================================
echo Frontend:       http://localhost:5173
echo Backend API:    http://localhost:8000
echo LocalStack:     http://localhost:4566  
echo DynamoDB Admin: http://localhost:8001
echo ====================================
echo.
echo All services started successfully!
echo Press any key to close this window...
pause >nul