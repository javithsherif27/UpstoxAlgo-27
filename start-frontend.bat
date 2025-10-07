@echo off
cd /d "%~dp0"

echo Checking Node.js installation...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo.
    echo Please install Node.js first:
    echo 1. Go to: https://nodejs.org/
    echo 2. Download LTS version
    echo 3. Run installer
    echo 4. Restart terminal and try again
    echo.
    echo Or run: setup-frontend.bat for guided setup
    pause
    exit /b 1
)

echo Node.js found: 
node --version

cd /d "%~dp0frontend"
echo Starting Vite frontend development server...
echo Frontend will be available at: http://localhost:5173
echo.

if not exist node_modules (
    echo Installing dependencies first...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        echo Try running: npm install --legacy-peer-deps
        pause
        exit /b 1
    )
)

npm run dev
pause