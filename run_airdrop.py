# 为状态是0的用户批量提交mint交易

from dotenv import load_dotenv
from substrateinterface import SubstrateInterface, Keypair, ExtrinsicReceipt
import os
import time
import redis
from scalecodec.types import GenericExtrinsic

from redis import Redis
from base import *
from ssl import SSLEOFError, SSLError
import asyncio
from common_fn import connect_substrate
# from crawler import *
# from post_api import *
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy import select, insert
import json
from substrateinterface.exceptions import SubstrateRequestException
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException


def submit_extrinsic(substrate: SubstrateInterface, sign: dict, wait_for_inclusion: bool = False,
                     wait_for_finalization: bool = False) -> "ExtrinsicReceipt":
    """
    Submit an extrinsic to the connected node, with the possibility to wait until the extrinsic is included
     in a block and/or the block is finalized. The receipt returned provided information about the block and
     triggered events

    Parameters
    ----------
    extrinsic: Extrinsic The extrinsic to be sent to the network
    wait_for_inclusion: wait until extrinsic is included in a block (only works for websocket connections)
    wait_for_finalization: wait until extrinsic is finalized (only works for websocket connections)

    Returns
    -------
    ExtrinsicReceipt

    """

    # Check requirements
    # if not isinstance(extrinsic, GenericExtrinsic):
    #     raise TypeError("'extrinsic' must be of type Extrinsics")

    def result_handler(message, update_nr, subscription_id):
        # Check if extrinsic is included and finalized
        if 'params' in message and type(message['params']['result']) is dict:

            # Convert result enum to lower for backwards compatibility
            message_result = {k.lower(): v for k, v in message['params']['result'].items()}

            if 'finalized' in message_result and wait_for_finalization:
                substrate.rpc_request('author_unwatchExtrinsic', [subscription_id])
                return {
                    'block_hash': message_result['finalized'],
                    'extrinsic_hash': sign["extrinsic_hash"],
                    'finalized': True
                }
            elif 'inblock' in message_result and wait_for_inclusion and not wait_for_finalization:
                substrate.rpc_request('author_unwatchExtrinsic', [subscription_id])
                return {
                    'block_hash': message_result['inblock'],
                    'extrinsic_hash': sign["extrinsic_hash"],
                    'finalized': False
                }

    if wait_for_inclusion or wait_for_finalization:
        response = substrate.rpc_request(
            "author_submitAndWatchExtrinsic",
            [sign["data"]],
            result_handler=result_handler
        )

        result = ExtrinsicReceipt(
            substrate=substrate,
            extrinsic_hash=response['extrinsic_hash'],
            block_hash=response['block_hash'],
            finalized=response['finalized']
        )

    else:

        response = substrate.rpc_request("author_submitExtrinsic", [sign["data"]])

        if 'result' not in response:
            raise SubstrateRequestException(response.get('error'))

        result = ExtrinsicReceipt(
            substrate=substrate,
            extrinsic_hash=response['result']
        )

    return result


async def submit_extrinsic_do(session: AsyncSession, substrate: SubstrateInterface, signature: str, extrinsic_hash: str):
    # try:
    # 查询未发送的离线签名
    status = 10
    fail_reason = ""
    try:
        print("extrinsic:", extrinsic_hash)
        receipt = submit_extrinsic(substrate, {"data": signature, "extrinsic_hash":
                    extrinsic_hash}, wait_for_inclusion=True, wait_for_finalization=True)
        print("回执是: ", receipt)
        print(receipt.triggered_events)

        if receipt.is_success:
            status = 4
        else:
            status = 3
            fail_reason = str(receipt.error_message)[:40]
            print("交易回执错误信息:", receipt.error_message)

    except (WebSocketConnectionClosedException, WebSocketTimeoutException, SSLEOFError, SSLError) as e:
        print(e)
        raise e

    except KeyboardInterrupt as e:

        print("离线提交出现异常：", e)
        stmt = select(Airdrop).where(Airdrop.extrinsic_hash == extrinsic_hash).with_for_update(read=False, nowait=False)
        result = await session.scalars(stmt)
        for r in result:
            r.fail_reason = str(e)[:40]
            r.status = status
        exit(0)
    except SubstrateRequestException as e:
        print("离线提交出现异常：", e)
        stmt = select(Airdrop).where(Airdrop.extrinsic_hash == extrinsic_hash).with_for_update(read=False, nowait=False)
        result = await session.scalars(stmt)
        for r in result:
            r.fail_reason = str(e)[:40]
            r.status = status
        return None
    except Exception as e:
        print("未知异常:", e)
        raise e

    stmt = select(Airdrop).where(Airdrop.extrinsic_hash == extrinsic_hash).with_for_update(read=False, nowait=False)
    result = await session.scalars(stmt)
    for r in result:
        r.fail_reason = fail_reason
        r.status = status


async def main():
    substrate = connect_substrate()
    while True:

        try:
            async with async_session() as session:
                async with session.begin():
                    stmt = select(Airdrop).where(Airdrop.status == 101).with_for_update(read=False, nowait=False)
                    extrinsic = await session.scalar(stmt)
                    if extrinsic is None:
                        print("没有等待发送的签名交易")
                        time.sleep(6)
                        continue
                    extrinsic_hash = extrinsic.extrinsic_hash
                    data = extrinsic.signature

            async with async_session() as session:
                async with session.begin():
                    await submit_extrinsic_do(session, substrate, signature=data, extrinsic_hash=extrinsic_hash)

        except (WebSocketConnectionClosedException, WebSocketTimeoutException, SSLEOFError, SSLError) as e:
            try:
                substrate = connect_substrate()
            except Exception as e:
                continue
        except Exception as e:
            # print("异常:", e)
            # raise e
            pass
        time.sleep(6)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)