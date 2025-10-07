@echo off
echo ===============================================
echo   Node.js Installation & Frontend Setup
echo ===============================================
echo.

echo Checking Node.js installation...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed or not in PATH.
    echo.
    echo OPTION 1: Install Node.js manually
    echo 1. Go to: https://nodejs.org/
    echo 2. Download LTS version
    echo 3. Run installer and restart terminal
    echo.
    echo OPTION 2: Install via winget (run as administrator):
    echo    winget install OpenJS.NodeJS
    echo.
    echo OPTION 3: Install via Chocolatey:
    echo    choco install nodejs
    echo.
    echo After installation, restart your terminal and run this script again.
    echo.
    pause
    exit /b 1
)

echo Node.js found! Version:
node --version

echo npm version:
npm --version

echo.
echo Installing frontend dependencies...
cd /d "%~dp0frontend"

if not exist package.json (
    echo ERROR: package.json not found in frontend directory
    echo Current directory: %cd%
    pause
    exit /b 1
)

echo Running npm install...
npm install

if %errorlevel% neq 0 (
    echo ERROR: npm install failed
    echo Try running: npm install --legacy-peer-deps
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   Frontend dependencies installed successfully!
echo ===============================================
echo.
echo You can now run:
echo   npm run dev     (development server)
echo   npm run build   (production build)
echo.
pause