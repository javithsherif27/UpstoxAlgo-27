@echo off
echo 🛑 Stopping PostgreSQL Docker Containers
echo ========================================

REM Stop all containers
echo 🛑 Stopping containers...
docker compose down

if %errorlevel% equ 0 (
    echo ✅ PostgreSQL containers stopped successfully
) else (
    echo ⚠️ Some containers may not have been running
)

REM Show status
echo.
echo 📊 Container status:
docker compose ps

echo.
echo 💡 To start again: start-postgres-docker.bat
echo 💡 To remove all data: docker compose down -v
pause