@echo off
echo Starting Full Stack with LocalStack...
echo.
echo This will start:
echo - LocalStack (AWS services locally)
echo - Backend (FastAPI) on http://localhost:8000
echo - Frontend (Vite) on http://localhost:5173
echo.

REM Start LocalStack first
echo [1/3] Starting LocalStack services...
call start-localstack.bat

REM Wait for LocalStack to initialize
timeout /t 8 /nobreak >nul

REM Start backend with LocalStack environment
echo [2/3] Starting Backend server...
start "Backend Server" cmd /c "cd /d %~dp0 && D:/source-code/UpstoxAlgo-27/.venv/Scripts/python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo [3/3] Starting Frontend server...
start "Frontend Server" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo ==========================================
echo  FULL STACK STARTED WITH LOCALSTACK!
echo ==========================================
echo Frontend:        http://localhost:5173
echo Backend API:     http://localhost:8000  
echo LocalStack:      http://localhost:4566
echo DynamoDB Admin:  http://localhost:8001
echo ==========================================
echo.
echo Press any key to exit this window (servers will continue running)
pause >nul