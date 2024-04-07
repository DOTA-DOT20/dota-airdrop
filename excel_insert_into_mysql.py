
# 把excel表的数据导入mysql中 插入的时候状态是100
import pandas as pd
from base import *
from sqlalchemy import select, insert
import asyncio


async def insert_data_into_mysql():
    # 从excel中获取数据
    df = pd.read_csv("balances.csv")
    for index, row in df.iterrows():
        async with async_session() as session:
            async with session.begin():
                print(index, type(row), row.get("user_address"), row.get("available"))
                stmt = insert(Airdrop).values({"account": row.get("user_address"), "amount": row.get("available"), "status": 100})
                await session.execute(stmt)


if __name__ == "__main__":
    asyncio.run(insert_data_into_mysql(), debug=True)