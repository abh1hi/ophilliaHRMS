import asyncio
from app.db.session import AsyncSessionLocal
from app.models.attendance_policy import AttendancePolicy
from sqlalchemy import update

async def fix():
    async with AsyncSessionLocal() as session:
        await session.execute(update(AttendancePolicy).values(max_shifts_per_day=2))
        await session.commit()
    print('Successfully updated all existing policies to 2 shifts.')

if __name__ == '__main__':
    asyncio.run(fix())
