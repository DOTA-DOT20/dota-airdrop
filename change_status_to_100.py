
from base import *
import asyncio
from sqlalchemy import select, insert,func


async def main():
    while True:
        async with async_session() as session:
            async with session.begin():
                stmt = select(Airdrop).where(Airdrop.status == 1)
                res = await session.scalar(stmt)
                if res is None:
                    break
                res.status = 100


async def get_no_fee_amount():
    async with async_session() as session:
        async with session.begin():
            stmt = select(func.sum(Airdrop.amount)).where(Airdrop.status == 1)
            res = await session.scalar(stmt)
            print("*"*100)
            print(res)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)