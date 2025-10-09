# PostgreSQL Setup Instructions for Trading Application

## Overview
This guide helps you migrate from SQLite to PostgreSQL for better performance, scalability, and AWS compatibility.

## 🚀 Quick Start

### 1. Install PostgreSQL

#### Windows (recommended):
```powershell
# Download and install from https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql

# Or use winget:
winget install PostgreSQL.PostgreSQL
```

#### Docker (cross-platform):
```bash
# Run PostgreSQL in Docker
docker run --name postgres-trading \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=trading_db \
  -p 5432:5432 \
  -d postgres:15

# Connect to verify
docker exec -it postgres-trading psql -U postgres -d trading_db
```

#### Linux/macOS:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install postgresql postgresql-contrib

# macOS with Homebrew
brew install postgresql
brew services start postgresql
```

### 2. Create Database
```sql
-- Connect as postgres user
CREATE DATABASE trading_db;
CREATE USER trading_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
```

### 3. Configure Environment
```bash
# Copy and edit configuration
cp backend/.env.example backend/.env

# Edit backend/.env with your database details:
DATABASE_URL=postgresql://trading_user:your_secure_password@localhost:5432/trading_db
```

### 4. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 5. Run Migration (Optional)
```bash
# If you have existing SQLite data:
python scripts/migrate_to_postgresql.py
```

## 🛠️ AWS RDS Setup (Production)

### Create RDS Instance
1. Go to AWS RDS Console
2. Click "Create Database"
3. Choose PostgreSQL
4. Select "Free tier" template
5. Configure:
   - DB instance identifier: `trading-db`
   - Master username: `postgres`
   - Master password: `your-secure-password`
   - DB instance class: `db.t3.micro` (free tier)
   - Storage: 20 GB (free tier limit)
   - VPC: Default
   - Public access: Yes (for development)
   - Security group: Allow 5432 from your IP

### Configure for AWS
```bash
# Set environment variable in your deployment
DATABASE_URL=postgresql://postgres:password@your-instance.abc123.us-east-1.rds.amazonaws.com:5432/postgres
```

## 📊 Performance Features

### Optimized Indexes Created:
- **Instruments**: symbol, exchange, type lookups
- **Market Ticks**: time-series queries, latest price lookups
- **Candles**: interval-based chart queries, OHLCV analysis
- **Composite**: multi-column queries for complex analytics

### Performance Views:
- `latest_prices`: Real-time price lookups
- `daily_stats`: Daily statistics with change calculations
- `active_instruments`: Recently traded instruments

### Batch Operations:
- Bulk tick inserts for high-frequency data
- Batch candle updates with conflict resolution
- Optimized query patterns for trading workloads

## 🔧 Configuration Options

### Environment Variables:
```bash
# Connection
DATABASE_URL=postgresql://user:pass@host:port/db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=password

# Connection Pool (for high concurrency)
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
DB_TIMEOUT=30.0
```

### Connection Pool Benefits:
- **Min 5 connections**: Always ready for queries
- **Max 20 connections**: Handles concurrent requests
- **30s timeout**: Prevents hanging queries
- **Async operations**: Non-blocking database I/O

## 🔍 Monitoring & Maintenance

### Database Statistics:
```sql
-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity;
```

### Cleanup Operations:
```sql
-- Clean old ticks (built into the service)
DELETE FROM market_ticks WHERE timestamp < NOW() - INTERVAL '7 days';

-- Vacuum and analyze for performance
VACUUM ANALYZE market_ticks;
VACUUM ANALYZE candles;
```

## 🚨 Troubleshooting

### Common Issues:

1. **Connection Refused**:
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   # Or for Docker:
   docker ps | grep postgres
   ```

2. **Authentication Failed**:
   ```sql
   -- Reset password
   ALTER USER postgres PASSWORD 'new_password';
   ```

3. **Permission Denied**:
   ```sql
   -- Grant permissions
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
   ```

4. **Migration Errors**:
   ```bash
   # Check logs
   tail -f backend/logs/app.log
   
   # Test connection
   python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('your_database_url'))"
   ```

## 🎯 Performance Benefits vs SQLite

| Feature | SQLite | PostgreSQL |
|---------|---------|------------|
| Concurrent Writes | ❌ Limited | ✅ Excellent |
| Connection Pooling | ❌ No | ✅ Built-in |
| Advanced Indexes | ❌ Basic | ✅ GIN, BTREE, etc. |
| JSON/JSONB Support | ❌ Limited | ✅ Native |
| Full-text Search | ❌ Basic | ✅ Advanced |
| Partitioning | ❌ No | ✅ Native |
| Replication | ❌ No | ✅ Built-in |
| AWS RDS Support | ❌ No | ✅ Managed |
| Vacuum/Cleanup | ❌ Manual | ✅ Automatic |
| Analytics | ❌ Limited | ✅ Window Functions |

## ✅ Verification

### Test Your Setup:
```bash
# 1. Start backend
python -m uvicorn backend.app:app --reload

# 2. Check health
curl http://localhost:8000/health

# 3. Check database connection in logs
tail -f backend/logs/app.log

# 4. Test trading operations
# Use your frontend to start market data collection
```

### Expected Performance:
- **Tick Storage**: >10,000 ticks/second
- **Candle Queries**: <100ms for 1000 candles
- **Latest Price**: <10ms response time
- **Concurrent Users**: 50+ simultaneous connections

## 🔄 Rollback Plan

If you need to revert to SQLite:
1. Stop the application
2. Update `backend/.env` to comment out `DATABASE_URL`
3. Ensure `market_data.db` exists in the root
4. Restart the application

The code automatically falls back to SQLite if PostgreSQL connection fails.

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)