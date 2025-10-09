@echo off
echo 🐳 Starting PostgreSQL with Docker Compose
echo ========================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Start PostgreSQL container
echo 🚀 Starting PostgreSQL container...
docker compose up -d postgres

if %errorlevel% neq 0 (
    echo ❌ Failed to start PostgreSQL container
    pause
    exit /b 1
)

echo ✅ PostgreSQL container started

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
:wait_loop
docker compose exec postgres pg_isready -U trading_user -d trading_db >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_loop
)

echo ✅ PostgreSQL is ready!

REM Show connection info
echo.
echo 📋 Connection Information:
echo   🔗 URL: postgresql://trading_user:trading_password_2024@localhost:5432/trading_db
echo   🐳 Container: trading-postgres
echo   🎯 Host: localhost:5432
echo   👤 User: trading_user
echo   🗄️ Database: trading_db
echo.
echo 💡 To connect: docker compose exec postgres psql -U trading_user -d trading_db
echo 💡 To stop: docker compose down
echo 💡 To view logs: docker compose logs -f postgres
echo.

REM Copy environment file if it doesn't exist
if not exist "backend\.env" (
    if exist "backend\.env.docker" (
        echo 📁 Copying Docker environment configuration...
        copy "backend\.env.docker" "backend\.env"
        echo ✅ Environment configured for Docker PostgreSQL
    )
)

echo 🎉 PostgreSQL Docker setup complete!
echo 💡 You can now start your backend with: start-backend.bat noreload
pause