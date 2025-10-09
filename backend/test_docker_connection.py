#!/usr/bin/env python3
"""
Simple test for Docker PostgreSQL connection
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.lib.database import init_database, db_manager, close_database


async def main():
    try:
        print('🔌 Testing PostgreSQL Docker connection...')
        print(f'DATABASE_URL: {os.getenv("DATABASE_URL", "Not set")}')
        
        # Initialize database
        await init_database()
        print('✅ Database initialized successfully')
        
        # Test connection
        async with db_manager.get_connection() as conn:
            # Get table count
            tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = $1", 'public')
            table_names = [t['table_name'] for t in tables]
            print(f'📊 Created {len(tables)} tables: {table_names}')
            
            # Test basic query
            version = await conn.fetchval('SELECT version()')
            print(f'📋 PostgreSQL version: {version.split(",")[0]}')
            
        await close_database()
        print('🎉 All tests passed! PostgreSQL Docker setup is working.')
        
    except Exception as e:
        print(f'❌ Test failed: {e}')
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)