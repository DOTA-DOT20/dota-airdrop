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
from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException, WebSocketException, WebSocketBadStatusException


def get_user_dota_amount(user: str, substrate: SubstrateInterface):
    result = substrate.query(
        module='Assets',
        storage_function='Account',
        params=[18, user]
    )
    print(result.value["balance"])


if __name__ == "__main__":
    user = "16YCoBvDSrDLbi3YsNPBLEmQZMkScz8a1yBQh5N1YsESdhAT"
    s = connect_substrate()
    get_user_dota_amount(user, s)