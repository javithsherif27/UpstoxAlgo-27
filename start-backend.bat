@echo off
cd /d "%~dp0"
echo Starting FastAPI backend server with LocalStack...
set PORT=8000
set RELOAD_ARG=--reload

REM Usage: start-backend.bat [noreload] [port]
if /I "%1"=="noreload" (
    set RELOAD_ARG=
    if not "%2"=="" set PORT=%2
) else (
    if not "%1"=="" set PORT=%1
)

echo Backend will be available at: http://localhost:%PORT%
echo.
echo Checking LocalStack availability...
curl -s http://localhost:4566/_localstack/health >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: LocalStack not detected. Starting backend without LocalStack.
    echo To use LocalStack, run: start-localstack.bat first
    echo.
) else (
    echo LocalStack detected and ready!
    echo Using local AWS services at http://localhost:4566
    echo.
)

echo Starting backend server...
if "%RELOAD_ARG%"=="" echo Reload disabled by argument. Running without --reload.

REM Keep-alive timeout modest to reduce lingering sockets; no server header for cleanliness
D:/source-code/UpstoxAlgo-27/.venv/Scripts/python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port %PORT% %RELOAD_ARG% --no-server-header --timeout-keep-alive 15
pause