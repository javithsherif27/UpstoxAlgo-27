@echo off
echo Stopping local development stack...

REM Kill backend and frontend processes
echo Stopping backend and frontend servers...
taskkill /f /im "python.exe" 2>nul
taskkill /f /im "node.exe" 2>nul

REM Stop LocalStack
echo Stopping LocalStack...
call stop-localstack.bat

echo.
echo Local development stack stopped.
pause