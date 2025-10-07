@echo off
echo Starting full local development stack with LocalStack...
echo.

REM Start LocalStack first
echo [1/3] Starting LocalStack services...
call start-localstack.bat

REM Wait a bit more for full initialization
timeout /t 5

REM Start backend
echo [2/3] Starting backend server...
start "Backend Server" cmd /c "cd backend && pip install -r requirements.txt && python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 3

REM Start frontend
echo [3/3] Starting frontend development server...
start "Frontend Server" cmd /c "cd frontend && npm run dev"

echo.
echo ===========================================
echo  Local Development Stack Started!
echo ===========================================
echo Backend API: http://localhost:8000
echo Frontend: http://localhost:5173
echo LocalStack: http://localhost:4566
echo DynamoDB Admin: http://localhost:8001
echo ===========================================
echo.
echo Press any key to view logs or close this window...
pause