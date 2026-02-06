import asyncio
from services.seed_data import seed_all

async def main():
    await seed_all()

asyncio.run(main())