# LocalStack Development Setup

This project includes LocalStack configuration for testing AWS services locally without incurring cloud costs.

## Quick Start

### Option 1: Full Development Stack
```bash
# Start everything (LocalStack + Backend + Frontend)
start-local-dev.bat

# Stop everything
stop-local-dev.bat
```

### Option 2: LocalStack Only
```bash
# Start only LocalStack services
start-localstack.bat

# Stop LocalStack services  
stop-localstack.bat
```

## Services Available

### LocalStack Services (Port 4566)
- **DynamoDB**: Local DynamoDB instance
- **S3**: Local S3 buckets
- **Additional services**: Can be added as needed

### Management UIs
- **DynamoDB Admin**: http://localhost:8001
- **LocalStack Dashboard**: http://localhost:4566/_localstack/health

## Configuration

### Environment Files
- `.env.local` - LocalStack configuration (auto-loaded in local dev)
- `.env.production` - Production AWS configuration template

### DynamoDB Tables Created
- `InstrumentsCache` - Cache for instrument data
- `AlgoTradingCache` - General application cache

### S3 Buckets Created  
- `algo-trading-data` - Application data storage
- `algo-trading-backups` - Backup storage

## Development Workflow

1. **Start LocalStack**: Run `start-local-dev.bat` for full stack
2. **Develop**: Your app automatically uses LocalStack when `USE_LOCALSTACK=true`
3. **Test**: All AWS calls go to LocalStack instead of real AWS
4. **Deploy**: Switch to production config for real AWS deployment

## Debugging

### Check LocalStack Health
```bash
curl http://localhost:4566/_localstack/health
```

### View DynamoDB Tables
- Open http://localhost:8001 in browser
- Browse tables and data

### Check Logs
```bash
docker-compose -f docker-compose.localstack.yml logs -f
```

## Environment Variables

### LocalStack Mode (.env.local)
```
USE_LOCALSTACK=true
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
LOCALSTACK_ENDPOINT=http://localhost:4566
```

### Production Mode (.env.production)  
```
USE_LOCALSTACK=false
AWS_REGION=us-east-1
# Real AWS credentials via IAM roles
```

## Benefits

- ✅ **Cost Effective**: No AWS charges during development
- ✅ **Fast Iteration**: Instant local deployment  
- ✅ **Offline Development**: Works without internet
- ✅ **Production Parity**: Same AWS APIs locally
- ✅ **Easy Testing**: Reset data anytime
- ✅ **Team Collaboration**: Consistent local environment

## Troubleshooting

### Common Issues

**LocalStack not starting:**
- Check Docker is running
- Ensure ports 4566, 8001 are available

**Tables not found:**
- LocalStack takes ~10 seconds to initialize
- Check initialization logs: `docker-compose -f docker-compose.localstack.yml logs localstack`

**Backend can't connect:**
- Verify `USE_LOCALSTACK=true` in environment
- Check backend logs for connection attempts

**Data persistence:**
- LocalStack data resets on container restart by default  
- Set `PERSISTENCE=1` in .env.local for data persistence
