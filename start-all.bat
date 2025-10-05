@echo off
echo Starting both Frontend and Backend servers...
echo.
echo Opening two new command prompt windows:
echo - Backend (FastAPI) on http://localhost:8000
echo - Frontend (Vite) on http://localhost:5173
echo.

start "Backend Server" cmd /c "cd /d %~dp0 && D:/source-code/UpstoxAlgo-27/.venv/Scripts/python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
start "Frontend Server" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit this window (servers will continue running)
pause >nul