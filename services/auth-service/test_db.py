import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings

async def main():
    print("CONNECTION URL:", settings.DATABASE_URL)
    try:
        async with engine.begin() as conn:
            res = await conn.execute(text("SELECT * FROM users LIMIT 1;"))
            print("USERS RESULT:", res.all())
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
