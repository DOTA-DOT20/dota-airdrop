# 获取用户asset_hub上dot余额
from dotenv import load_dotenv
from substrateinterface import SubstrateInterface, Keypair, ExtrinsicReceipt
import os
import time
import redis
from scalecodec.types import GenericExtrinsic

from redis import Redis
from base import *
import random
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy import select, insert
import json
from substrateinterface.exceptions import SubstrateRequestException
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException


load_dotenv()


def connect_substrate() -> SubstrateInterface:
    urls = list({"wss://polkadot-asset-hub-rpc.polkadot.io", "wss://statemint-rpc.dwellir.com",
                 "wss://rpc-asset-hub-polkadot.luckyfriday.io", os.getenv("URL")})
    try:
        url = random.choice(urls)
        substrate = SubstrateInterface(
            url=url,
        )
        print("connect to {}".format(url))
        print(f"chain: {substrate.chain}, format: {substrate.ss58_format}, token symbol: {substrate.token_symbol}")
        if substrate.chain != os.getenv("CHAIN"):
            raise Exception(f"The connected node is not {os.getenv('CHAIN')}")
    except Exception as e:
        print(f"connect fail {e}, retry...")
        time.sleep(3)
        return connect_substrate()
    return substrate