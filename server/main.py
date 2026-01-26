import asyncio
from infrastructure.postgres_connector import AsyncPostgresConnector

# Global state
browser: Optional[webdriver.Chrome] = None
current_page = 1
db: Optional[AsyncPostgresConnector] = None


async def main():
    async with AsyncPostgresConnector(
        host="localhost",
        port=5432,
        dbname="real_estate_db",   # default when POSTGRES_DB not set
        user="postgres",     # default when POSTGRES_USER not set
        password="12345",
    ) as db:
        result = await db.fetch_one("SELECT * from properties LIMIT 1;")
        print(f"Connected!\n{result}")

asyncio.run(main())