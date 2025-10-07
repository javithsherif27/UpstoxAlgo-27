@echo off
echo Starting LocalStack services...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop:
    echo 1. Open Docker Desktop from Start menu
    echo 2. Wait for it to fully start (whale icon should be steady)
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo Docker is running, starting LocalStack...
docker-compose -f docker-compose.localstack.yml up -d

REM Wait for services to be ready
echo Waiting for LocalStack to be ready...
timeout /t 15

REM Check if LocalStack is running
echo Checking LocalStack health...
curl -s http://localhost:4566/_localstack/health

echo.
echo =========================================
echo  LocalStack is ready!
echo =========================================
echo DynamoDB Admin UI: http://localhost:8001
echo LocalStack endpoint: http://localhost:4566
echo Health check: http://localhost:4566/_localstack/health
echo =========================================
echo.