@echo off
cd /d "%~dp0"
echo Starting FastAPI backend server...
echo Backend will be available at: http://localhost:8000
echo.
D:/source-code/UpstoxAlgo-27/.venv/Scripts/python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
pause