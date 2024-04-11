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


def get_asset_hub_batchall_by_block_num(substrate: SubstrateInterface, block_num: int):
    res = []
    try:
        block_hash = substrate.get_block_hash(block_num)
        txs = substrate.get_extrinsics(block_hash=block_hash)
        for index, tx in enumerate(txs):
            issuer = "162aMTRcXF27yNeNE82SfZj5KWH94sBtivvy7a5uef2ry81r"
            # 如果签名地址是singer = tx.value.get("address")
            if tx.value.get("address") == issuer and tx.value.get("call").get("call_function") == "batch_all":
                    # and tx.value.get("call").get("call_module") == "Assets":
                # 是dota转账 fixme 还有其他资产
                # asset_id = int(tx.value.get("call")["call_args"][0]["value"])
                # if asset_id == 1984 or asset_id == 1337 or asset_id == 18:
                    # 目标地址
                    # dest = tx.value.get("call")["call_args"][1]["value"]
                    # # 金额
                    # amt = tx.value.get("call")["call_args"][2]["value"]
                    # 金额必须大于0
                    # if amt > 0:
                    #     singer = tx.value.get("address")
                extrinsic_hash = tx.value["extrinsic_hash"]
                #     print("dest: ", dest)
                receipt = ExtrinsicReceipt(substrate, extrinsic_hash=extrinsic_hash,
                                            block_hash=block_hash,
                                            block_number=block_num,
                                            extrinsic_idx=index, finalized=True)
                    # if asset_id == 18:
                    #     tick = "dota"
                    # elif asset_id == 1984:
                    #     tick = "usdt"
                    # elif asset_id == 1337:
                    #     tick = "usdc"
                    # else:
                    #     raise Exception("不是支持的tick")
                    # print(receipt.is_success)
                    # print(os.getenv("BROKER_ADDRESS"))
                if receipt.is_success:
                    print("extrinsic_hash:", extrinsic_hash)
                    res.append(extrinsic_hash)

                    # r = {"block_num": block_num, "tx_hash": extrinsic_hash,
                    #  "extrinsic_index": index, "from": singer, "to": dest, "tick": tick,
                    #  "amt": amt, "status": 0}
                    # res.append(r)
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
    num = 6033389
    end = 6035968
    result = []
    while num <= end:
        try:
            print("区块高度：", num)
            hashes = get_asset_hub_batchall_by_block_num(s, num)
            print(hashes)
            for hash in hashes:
                res = await get_success_hash_but_fail_in_mysql(hash)
                if len(res) > 0:
                    result.append(res)
            # 查询该交易hash有没有在数据库中，并且状态是10或者3
            num += 1
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


if __name__ == "__main__":
    asyncio.run(main(), debug=True)