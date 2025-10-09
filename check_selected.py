import sys
sys.path.append('backend')
import asyncio
from backend.lib.database import db_manager

async def check_selected():
    await db_manager.initialize()
    result = await db_manager.execute_query('SELECT * FROM selected_instruments LIMIT 5')
    await db_manager.close()
    print('Selected instruments:', result)

if __name__ == "__main__":
    asyncio.run(check_selected())