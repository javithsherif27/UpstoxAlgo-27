-- PostgreSQL Database Initialization Script
-- This runs automatically when the Docker container starts for the first time

\echo 'Creating trading database schema...'

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create additional schemas if needed
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS backups;

-- Grant permissions to trading_user
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO trading_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO trading_user;

\echo 'Database initialization completed successfully!'