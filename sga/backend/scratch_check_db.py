import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db

async def main():
    await db.connect()
    try:
        async with db.connection().acquire() as conn:
            print("--- CAT_TIPO_CONDICION ---")
            rows = await conn.fetch("SELECT * FROM cat_tipo_condicion")
            for row in rows:
                print(dict(row))

            print("\n--- TENANTS ---")
            tenants = await conn.fetch("SELECT * FROM tenants")
            for t in tenants:
                print(dict(t))
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
