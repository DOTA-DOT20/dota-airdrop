from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
# from sqlalchemy.orm.session import Transaction
from datetime import datetime
from sqlalchemy import CheckConstraint, UniqueConstraint, func
import os
from typing import Optional
from aiomysql import *
from dotenv import load_dotenv

load_dotenv()
user = os.getenv("MYSQLUSER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
database = os.getenv("DATABASE")
async_str = "aiomysql"
sync_str = "pymysql"
# sync_str = "mysqlconnector"
# 异步（用于读取数据）
print(f"mysql+{async_str}://{user}:{password}@{host}/{database}")
async_engine: AsyncEngine = create_async_engine(f"mysql+{async_str}://{user}:{password}@{host}/{database}", echo=True,
                                                pool_size=100, max_overflow=100)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)

# # 同步，更新数据（安全性要求比较高)
# engine = create_engine(f"mysql+{sync_str}://{user}:{password}@{host}/{database}", echo=True,
#                                                 pool_size=10, max_overflow=20)
# LocalSession = sessionmaker(bind=engine, expire_on_commit=False)

# 创建基础模型
Base = declarative_base()


# 异步环境中不能这样创建 应该使用alembic来创建
# Base.metadata.create_all(async_engine)


# 空投表
class Airdrop(Base):
    __tablename__ = "airdrop"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account = Column(String(64), index=True, nullable=False)
    # 空投金额
    amount = Column(Integer, nullable=False)
    # 0是未空投 1是空投中 3是失败 4是成功  10是异常 100是没有asset_hub手续费
    status = Column(Integer, nullable=False, index=True)
    # 签名人
    signer = Column(String(64), index=True, nullable=True)
    # 离线签名
    signature = Column(String(5120), nullable=True)
    # 空投hash
    extrinsic_hash = Column(String(66), nullable=True, index=True)
    fail_reason = Column(String(66), nullable=True)
    creat_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    update_time = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint('extrinsic_hash', name='unique_hash'),
                      UniqueConstraint('account', name='unique_account')
                      )


