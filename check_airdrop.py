from dotenv import load_dotenv
from substrateinterface import SubstrateInterface, Keypair, ExtrinsicReceipt
import os
import time
import redis
from scalecodec.types import GenericExtrinsic

from redis import Redis
# from db.base import *
# from crawler import *
# from ssl import SSLEOFError, SSLError
# from post_api import *
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy import select, insert, or_
from sqlalchemy.engine.result import ScalarResult
import asyncio
import json
from common_fn import *
from substrateinterface.exceptions import SubstrateRequestException
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException, WebSocketException, WebSocketBadStatusException


load_dotenv()


async def get_asset_hub_batchall_by_block_num(substrate: SubstrateInterface, block_num: int):
    res = []
    try:
        block_hash = substrate.get_block_hash(block_num)
        txs = substrate.get_extrinsics(block_hash=block_hash)
        for index, tx in enumerate(txs):
            issuer = "162aMTRcXF27yNeNE82SfZj5KWH94sBtivvy7a5uef2ry81r"
            # 如果签名地址是singer = tx.value.get("address")
            if tx.value.get("address") == issuer and tx.value.get("call").get("call_function") == "batch_all":

                extrinsic_hash = tx.value["extrinsic_hash"]
                #     print("dest: ", dest)
                receipt = ExtrinsicReceipt(substrate, extrinsic_hash=extrinsic_hash,
                                            block_hash=block_hash,
                                            block_number=block_num,
                                            extrinsic_idx=index, finalized=True)

                if receipt.is_success:
                    batch_all = tx.value.get("call")["call_args"][0]["value"]
                    for mint in batch_all[:-1]:
                        if mint["call_function"] == "mint":
                            call_args = mint["call_args"]
                            dest = call_args[1]["value"]
                            amount = call_args[2]["value"]
                            print(f"user:{dest}, amount: {amount}")
                            async with async_session() as session:
                                async with session.begin():
                                    stmt = insert(Airdrop).where(Airdrop.extrinsic_hash == extrinsic_hash)
                                    rs = await session.scalars(stmt)
                                    for r in rs:
                                        # 把状态改成成功
                                        r.status = 4
                            with open("airdrop.txt", 'a') as file:
                                file.write(f"{dest}, {amount}\n")

                    print("extrinsic_hash:", extrinsic_hash)
                    res.append(extrinsic_hash)

        return res
    except (SubstrateRequestException, WebSocketConnectionClosedException, WebSocketTimeoutException, WebSocketException, WebSocketBadStatusException) as e:
        raise e


async def get_success_hash_but_fail_in_mysql(hash: str):
    r = []
    amt = 0
    async with async_session() as session:
        async with session.begin():
            # 查询异常或者失败的交易
            stmt = select(Airdrop).where(or_(Airdrop.status == 10, Airdrop.status == 3)).where(Airdrop.extrinsic_hash == hash)
            res: ScalarResult = await session.scalars(stmt)
            if len(res.all()) > 0:
                print(f"{hash} 交易在数据库中失败或者异常， 但是在链上已经成功")
                for r in res:
                    print("r:", r)
                    amt += r.amount
                print("该笔交易的总金额是: ", amt)
    if amt > 0:
        return [hash, amt]
    return []


async def main():
    s = connect_substrate()
    result = []
    _range1 = list(range(6033389, 6033657))
    _range2 = list(range(6035918, 6035969))
    _range1.extend(_range2)
    for num in _range1:
        try:
            print("区块高度：", num)
            hashes = await get_asset_hub_batchall_by_block_num(s, num)
            print(hashes)
            for hash in hashes:
                res = await get_success_hash_but_fail_in_mysql(hash)
                if len(res) > 0:
                    result.append(res)
        except (SubstrateRequestException, WebSocketConnectionClosedException, WebSocketTimeoutException, WebSocketException, WebSocketBadStatusException) as e:
            try:
                s = connect_substrate()
            except Exception as e:
                pass
    print("result:", result)
    amount = 0
    for r in result:
        amount += r[1]
    print(f"数据库失败或者异常，但是链上成功的金额有: {amount}")

    # 把状态是10的，全部改成0
    while True:
        async with async_session() as session:
            async with session.begin():
                stmt = select(Airdrop).where(Airdrop.status == 10)
                res = await session.scalar(stmt)
                if res is None:
                    break
                res.status = 0

    # 对账
    async with async_session() as session:
        async with session.begin():
            stmt = select(func.sum(Airdrop.amount)).where(Airdrop.status == 4)
            amount = await session.scalar(stmt)
            if int(amount) == 18312933206:
                print("对账成功")
            else:
                exit("对账失败，请重新对账")


async def test():
    async with async_session() as session:
        async with session.begin():
            stmt = select(func.sum(AlreadyAirdrop.amount)).where(1==1)
            res = await session.scalar(stmt)
            print("res:", res)

if __name__ == "__main__":
    asyncio.run(main(), debug=True)