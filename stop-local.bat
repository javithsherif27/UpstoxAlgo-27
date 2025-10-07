@echo off
echo Stopping Local Development Environment...
echo.

REM Stop application servers
echo [1/2] Stopping Backend and Frontend servers...
taskkill /f /fi "WINDOWTITLE eq Backend*" 2>nul
taskkill /f /fi "WINDOWTITLE eq Frontend*" 2>nul  
taskkill /f /im "python.exe" 2>nul
taskkill /f /im "node.exe" 2>nul

REM Stop LocalStack
echo [2/2] Stopping LocalStack services...
call stop-localstack.bat

echo.
echo ====================================
echo   LOCAL DEVELOPMENT STOPPED
echo ====================================
echo All services have been terminated.
echo.
pause