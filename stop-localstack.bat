@echo off
REM Stop LocalStack services
echo Stopping LocalStack services...
docker-compose -f docker-compose.localstack.yml down

echo LocalStack services stopped.