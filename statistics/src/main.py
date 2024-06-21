from fastapi import FastAPI, Response, Depends
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer
import json
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, select
from os import environ
from pydantic import BaseModel
from unary.stats import unarystats_pb2 as pb2, unarystats_pb2_grpc as pb2_grpc
from grpc import aio

loop = asyncio.get_event_loop()
consumer = None

Base = declarative_base()
async_session = None


def start_connection(lp=loop):
    global async_session, consumer
    DATABASE_URL = environ.get('DB_URL')
    KAFKA = environ.get('KAFKA')
    try:
        consumer = AIOKafkaConsumer("statistics", bootstrap_servers=KAFKA, loop=lp)
        engine = create_async_engine(DATABASE_URL)
    except:
        engine = create_async_engine('postgresql+asyncpg://stats:stats@sn-postgresql:5432/stats')
        consumer = AIOKafkaConsumer("statistics", bootstrap_servers='kafka:29092', loop=lp)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        return session


class Statistics(Base):
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    post_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)
    author = Column(String, nullable=False)


class StatsModel(BaseModel):
    post_id: int
    username: str
    action: str
    author: str

    @classmethod
    def from_dao(cls, dao):
        return StatsModel(
            post_id=dao.post_id,
            username=dao.username,
            action=dao.action,
            author=dao.author
        )


class UnaryStatsService(pb2_grpc.UnaryStatsServicer):
    def __init__(self, *args, **kwargs):
        pass

    async def get_post_stats(self, request, context):
        a_session = await get_session()
        id = request.id
        try:
            result = await a_session.execute(select(Statistics).where(Statistics.post_id == id))
            stats = result.scalars().all()
            if stats:
                likes = 0
                views = 0
                used_l = []
                used_v = []
                for s in stats:
                    if s.action == 'LIKED' and s.username not in used_l:
                        likes += 1
                        used_l.append(s.username)
                    elif s.action == 'WATCHED' and s.username not in used_v:
                        views += 1
                        used_v.append(s.username)
                result = {'message': "Post id: {} Likes: {} Views: {}".format(id, likes, views)}
            else:
                result = {'message': "Post has no stats"}
        except:
            result = {'message': "Error getting posts"}
        return pb2.MessageResponse(**result)

    async def get_post_top_likes(self, request, context):
        a_session = await get_session()
        result = await a_session.execute(select(Statistics).where(Statistics.action == 'LIKED'))
        stats = result.scalars().all()
        top = {}
        used = {}
        author = {}
        for s in stats:
            if s.post_id not in used:
                used[s.post_id] = set()
            used[s.post_id].add(s.username)
            author[s.post_id] = s.username
        for k in used:
            top[k] = len(used[k])
        i = 0
        res = []
        for k, v in sorted(top.items(), key=lambda item: item[1]):
            if i == 5:
                break
            res.append({'id': k, 'author': author[k], 'count': v})
            i += 1
        result = {'top': res}
        return pb2.TopPostResponse(**result)

    async def get_post_top_views(self, request, context):
        a_session = await get_session()
        result = await a_session.execute(select(Statistics).where(Statistics.action == 'WATCHED'))
        stats = result.scalars().all()
        top = {}
        used = {}
        author = {}
        for s in stats:
            if s.post_id not in used:
                used[s.post_id] = set()
            used[s.post_id].add(s.username)
            author[s.post_id] = s.username
        for k in used:
            top[k] = len(used[k])
        i = 0
        res = []
        for k, v in sorted(top.items(), key=lambda item: item[1]):
            if i == 5:
                break
            res.append({'id': k, 'author': author[k], 'count': v})
            i += 1
        result = {'top': res}
        return pb2.TopPostResponse(**result)

    async def get_user_top(self, request, context):
        a_session = await get_session()
        try:
            result = await a_session.execute(select(Statistics).where(Statistics.action == 'LIKED'))
            stats = result.scalars().all()
            top = {}
            used = {}
            for s in stats:
                if s.author not in used:
                    used[s.author] = set()
                used[s.author].add(s.username)
            for k in used:
                top[k] = len(used[k])
            i = 0
            res = []
            for k, v in sorted(top.items(), key=lambda item: item[1]):
                if i == 3:
                    break
                res.append({'author': k, 'count': v})
                i += 1
            result = {'top': res}
            return pb2.TopUserResponse(**result)
        except:
            result = {'message': "Error getting posts"}
            return pb2.MessageResponse(**result)


async def serve():
    server = aio.server()
    pb2_grpc.add_UnaryStatsServicer_to_server(UnaryStatsService(), server)
    server.add_insecure_port('[::]:50052')
    await server.start()
    await server.wait_for_termination()


async def consume():
    await consumer.start()
    session = await get_session()
    # ПОЧЕМУ???
    a = consumer.assignment()
    t = await consumer.topics()
    await consumer.seek_to_beginning()
    # КАК???
    try:
        # Вот до сюда доходит программа, но застревает на async for
        async for msg in consumer:
            data = json.loads(msg.value.decode("ascii"))
            session.add(Statistics(post_id=data["post_id"], username=data["username"], action=data["action"], author=data["author"]))
            await session.commit()
    finally:
        await consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_connection()
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(serve())
    asyncio.create_task(consume())
    yield
    await consumer.stop()

app = FastAPI(lifespan=lifespan)


@app.post('/')
async def ok():
    return Response(status_code=200)


@app.get('/admin/stats')
async def get_stats(a_session: AsyncSession = Depends(get_session)) -> list[StatsModel]:
    result = await a_session.execute(select(Statistics))
    stats = result.scalars().all()
    return [StatsModel.from_dao(stat) for stat in stats]
