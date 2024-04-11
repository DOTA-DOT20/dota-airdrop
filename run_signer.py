from dotenv import load_dotenv
from substrateinterface import SubstrateInterface, Keypair, ExtrinsicReceipt
import os
import time
import redis
from scalecodec.types import GenericExtrinsic
from ssl import SSLEOFError, SSLError
import getpass
from redis import Redis
from base import *
import asyncio
from common_fn import connect_substrate
# from crawler import *
# from post_api import *
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy import select, insert
from sqlalchemy.engine.result import ScalarResult
import json
from substrateinterface.exceptions import SubstrateRequestException
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException


def get_keypair(substrate: SubstrateInterface, seed):
    try:
        keypair = Keypair.create_from_seed(seed, ss58_format=substrate.ss58_format)
        return keypair
    except Exception as e:
        raise e


# 签名用户提币交易并入库
# user_withdra 必须有值
async def get_extrinsic(keypair: Keypair, session: AsyncSession, user_withdraws, substrate: SubstrateInterface):
    calls = []
    users = []
    try:
        for user_withdraw in user_withdraws:
            print("user: ", user_withdraw.account)

            user_transfer_call = substrate.compose_call(
                call_module="Assets",
                call_function="mint",
                call_params= {
                    "id": 18,
                    "beneficiary": user_withdraw.account,
                    "amount": int(user_withdraw.amount * 10000)
                }
            )

            users.append(user_withdraw.account)
            calls.append(user_transfer_call)

        if len(calls) > 0:
            user_remark_call = substrate.compose_call(
                call_module='System',
                call_function='remark',
                call_params={
                    'remark': "airdrop"
                })
            calls.append(user_remark_call)

            call = substrate.compose_call(
                call_module="Utility",
                call_function="batch_all",
                call_params={
                    "calls": calls
                }
            )

            # 对call进行签名
            extrinsic = substrate.create_signed_extrinsic(
                call=call,
                keypair=keypair,
            )

            # user_withdraws不能多次复用
            for user in users:
                stmt = select(Airdrop).where(Airdrop.account == user).with_for_update(read=False, nowait=False)
                user_withdraw = await session.scalar(stmt)
                user_withdraw.extrinsic_hash = "0x" + extrinsic.extrinsic_hash.hex()
                user_withdraw.signature = str(extrinsic.data)
                user_withdraw.signer = user
                # 有手续费并且已经签名
                user_withdraw.status = 101

        else:
            print("没有需要签名的交易")

    except (SubstrateRequestException, WebSocketConnectionClosedException, WebSocketTimeoutException, SSLEOFError, SSLError) as e:
        raise e

    except Exception as e:
        raise e


async def main():
    # asset_hub链
    seed = getpass.getpass("请输入issuer私钥: ")
    substrate = connect_substrate()
    keypair = get_keypair(substrate, seed)
    while True:
        try:
            async with async_session() as session:
                async with session.begin():
                    stmt = select(Airdrop).where(Airdrop.status == 101)
                    if await session.scalar(stmt):
                        print("该用户已经有签名的交易，需要等待发送")
                        continue

            async with async_session() as session:
                async with session.begin():
                    stmt = select(Airdrop).where(Airdrop.status == 0) \
                        .offset(0) \
                        .limit(25) \
                        .with_for_update(read=False, nowait=False)
                    user_withdraws = await session.scalars(stmt)
                    await get_extrinsic(keypair, session, user_withdraws, substrate)

            await session.close()
        except (SubstrateRequestException, WebSocketConnectionClosedException, WebSocketTimeoutException, SSLEOFError, SSLError) as e:
                    substrate = connect_substrate()
        except Exception as e:
            pass
        finally:
            time.sleep(6)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)