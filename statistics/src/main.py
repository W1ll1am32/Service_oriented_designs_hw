from fastapi import FastAPI, Response
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer
import json
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from clickhouse_sqlalchemy import engines
from sqlalchemy import DDL, Column, Integer, String
from os import environ

loop = asyncio.get_event_loop()
consumer = AIOKafkaConsumer("statistics", bootstrap_servers='kafka:29092', loop=loop)

DATABASE_URL = environ.get('DB_URL')
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
database = 'statistics'

conn = engine.connect()
conn.execute("commit")
conn.execute(DDL(f'CREATE DATABASE IF NOT EXISTS {database}'))
conn.close()


Base = declarative_base()


class Statistics(Base):
    __tablename__ = 'statistics'
    __table_args__ = (
        engines.MergeTree(order_by=['id']),
        {'schema': database},
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer)
    user = Column(String)
    action = Column(String)
    author = Column(String)


Statistics.__table__.create(engine)


async def consume():
    await consumer.start()
    with async_session() as session:
        try:
            async for msg in consumer:
                data = json.loads(msg.value.decode("ascii"))
                session.add(Statistics(post_id=data["post_id"], user=data["user"], action=data["action"], author=data["author"]))
                await session.commit()
        finally:
            await consumer.stop()

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(consume())
    yield
    await consumer.stop()


@app.post('/')
async def ok():
    return Response(200)
