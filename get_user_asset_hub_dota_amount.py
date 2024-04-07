from substrateinterface.exceptions import SubstrateRequestException
from substrateinterface import SubstrateInterface
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException
from ssl import SSLEOFError, SSLError
from sqlalchemy import select, insert
from base import *
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
import asyncio

import common_fn


# 获取用户链上自由余额
def get_dota_free_amount(user: str, substrate: SubstrateInterface):
    try:
        result = substrate.query(
            module='System',
            storage_function='Account',
            params=[user]
        )
        free = 0
        if result:
            free = result.value['data']['free']
        return free
    except (SubstrateRequestException, WebSocketConnectionClosedException, WebSocketTimeoutException, SSLEOFError,
            SSLError) as e:
        raise e


# 获取mysql中状态是100的数据
# 每次获取一条够了
async def get_status_100_data_from_mysql(session: AsyncSession):
    stmt = select(Airdrop).where(Airdrop.status == 100).with_for_update(read=False, nowait=False)
    return await session.scalar(stmt)


async def main():
    substrate = common_fn.connect_substrate()
    while True:
        try:
            async with async_session() as session:
                async with session.begin():
                    user_info = await get_status_100_data_from_mysql(session)
                    user = user_info.account
                    if user_info:
                        free = get_dota_free_amount(user, substrate)
                        if free > 0:
                            print(f"用户: {user}, 有手续费: {free}")
                            user_info.status = 0
                        else:
                            print(f"用户: {user}, 没有手续费， 需要充值")
                            user_info.status = 1
                    else:
                        print("已经全部核对")
        except (SubstrateRequestException, WebSocketConnectionClosedException, WebSocketTimeoutException, SSLEOFError, SSLError) as e:
            try:
                substrate = common_fn.connect_substrate()
            except Exception as e:
                continue
        except Exception as e:
            print("异常:", e)
            raise e



if __name__ == "__main__":
    # s = common_fn.connect_substrate()
    # user = "16YCoBvDSrDLbi3YsNPBLEmQZMkScz8a1yBQh5N1YsESdhAT"
    # free = get_dota_free_amount(user, s)
    # print(free)
    asyncio.run(main(), debug=False)

