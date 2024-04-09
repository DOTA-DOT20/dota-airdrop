
from base import *
from sqlalchemy import select, insert,func
import asyncio

async def main():
    while True:
        async with async_session() as session:
            async with session.begin():
                stmt = select(Airdrop).where(Airdrop.status != 1).where(Airdrop.status != 0)
                res = await session.scalar(stmt)

                if res == None:
                    print("结束")
                    break
                res.status = 0
                res.signer = None
                res.signature = None
                res.extrinsic_hash  = None
                res.fail_reason = None


if __name__ == "__main__":
    asyncio.run(main(), debug=True)