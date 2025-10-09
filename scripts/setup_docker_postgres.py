#!/usr/bin/env python3
"""
Docker PostgreSQL Setup and Test Script
Sets up and verifies PostgreSQL running in Docker
"""
import subprocess
import sys
import time
import asyncio
import os

# Add backend to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def run_command(cmd, shell=True, capture_output=True):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=capture_output, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Check if Docker is installed and running"""
    print("🐳 Checking Docker...")
    success, stdout, stderr = run_command("docker --version")
    if success:
        print(f"  ✅ Docker found: {stdout.strip()}")
        
        # Check if Docker daemon is running
        success, _, _ = run_command("docker info")
        if success:
            print("  ✅ Docker daemon is running")
            return True
        else:
            print("  ❌ Docker daemon is not running. Please start Docker Desktop.")
            return False
    else:
        print(f"  ❌ Docker not found: {stderr}")
        print("  💡 Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
        return False

def setup_postgres_container():
    """Set up PostgreSQL container using docker-compose"""
    print("\n📦 Setting up PostgreSQL container...")
    
    # Stop any existing containers
    print("  🛑 Stopping existing containers...")
    run_command("docker compose down", capture_output=False)
    
    # Pull the latest images
    print("  📥 Pulling PostgreSQL image...")
    success, stdout, stderr = run_command("docker compose pull postgres")
    if not success:
        print(f"  ⚠️ Failed to pull image: {stderr}")
    
    # Start PostgreSQL container
    print("  🚀 Starting PostgreSQL container...")
    success, stdout, stderr = run_command("docker compose up -d postgres", capture_output=False)
    if not success:
        print(f"  ❌ Failed to start container: {stderr}")
        return False
    
    print("  ✅ PostgreSQL container started")
    
    # Wait for PostgreSQL to be ready
    print("  ⏳ Waiting for PostgreSQL to be ready...")
    max_retries = 30
    for i in range(max_retries):
        success, _, _ = run_command("docker compose exec postgres pg_isready -U trading_user -d trading_db")
        if success:
            print(f"  ✅ PostgreSQL is ready (took {i+1} seconds)")
            return True
        
        print(f"    ⏳ Waiting... ({i+1}/{max_retries})")
        time.sleep(1)
    
    print("  ❌ PostgreSQL failed to start within timeout")
    return False

def verify_database_connection():
    """Verify database connection and run basic tests"""
    print("\n🔍 Verifying database connection...")
    
    # Test connection using psql in container
    test_query = "SELECT version();"
    success, stdout, stderr = run_command(
        f'docker compose exec postgres psql -U trading_user -d trading_db -c "{test_query}"'
    )
    
    if success:
        print("  ✅ Database connection successful")
        version_line = [line for line in stdout.split('\n') if 'PostgreSQL' in line]
        if version_line:
            print(f"  📊 {version_line[0].strip()}")
        return True
    else:
        print(f"  ❌ Database connection failed: {stderr}")
        return False

async def test_python_connection():
    """Test Python asyncpg connection"""
    print("\n🐍 Testing Python database connection...")
    
    try:
        # Set environment for testing
        os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password_2024@localhost:5432/trading_db'
        
        from backend.lib.database import init_database, db_manager, close_database
        
        # Initialize database schema
        await init_database()
        print("  ✅ Database schema initialized")
        
        # Test basic query
        async with db_manager.get_connection() as conn:
            result = await conn.fetchval('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = $1', 'public')
            print(f"  📊 Found {result} tables in public schema")
        
        await close_database()
        print("  ✅ Python database connection successful")
        return True
        
    except Exception as e:
        print(f"  ❌ Python connection failed: {e}")
        return False

def show_connection_info():
    """Show connection information"""
    print("\n📋 Connection Information:")
    print("  🔗 Database URL: postgresql://trading_user:trading_password_2024@localhost:5432/trading_db")
    print("  🐳 Container name: trading-postgres")
    print("  🎯 Host: localhost")
    print("  🚪 Port: 5432")
    print("  👤 Username: trading_user")
    print("  🔑 Password: trading_password_2024")
    print("  🗄️ Database: trading_db")

def show_management_commands():
    """Show useful management commands"""
    print("\n🔧 Useful Commands:")
    print("  Start PostgreSQL:     docker compose up -d postgres")
    print("  Stop PostgreSQL:      docker compose down")
    print("  View logs:            docker compose logs -f postgres")
    print("  Connect to DB:        docker compose exec postgres psql -U trading_user -d trading_db")
    print("  Restart:              docker compose restart postgres")
    print("  
    print("  Start with pgAdmin:   docker compose --profile admin up -d")
    print("  pgAdmin URL:          http://localhost:5050 (admin@trading.local / admin123)")

async def main():
    """Main setup function"""
    print("🚀 PostgreSQL Docker Setup for Trading Application")
    print("=" * 60)
    
    # Check prerequisites
    if not check_docker():
        return False
    
    # Setup PostgreSQL container
    if not setup_postgres_container():
        return False
    
    # Verify connection
    if not verify_database_connection():
        return False
    
    # Test Python connection
    if not await test_python_connection():
        return False
    
    # Show information
    show_connection_info()
    show_management_commands()
    
    print("\n" + "=" * 60)
    print("🎉 PostgreSQL Docker setup completed successfully!")
    print("\n💡 Next steps:")
    print("  1. Copy backend/.env.docker to backend/.env")
    print("  2. Start your backend: start-backend.bat noreload")
    print("  3. Your application will now use PostgreSQL instead of SQLite")
    print("  4. Monitor with: docker compose logs -f postgres")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed: {e}")
        sys.exit(1)