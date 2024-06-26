from sqlalchemy import Column, String, Integer
from os import environ
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from grpc import aio
from unary.posts import unaryposts_pb2 as pb2, unaryposts_pb2_grpc as pb2_grpc
import logging
import asyncio

Base = declarative_base()
async_session = None


def start_connection():
    global async_session
    DATABASE_URL = environ.get('DB_URL')
    try:
        engine = create_async_engine(DATABASE_URL)
    except:
        engine = create_async_engine('postgresql+asyncpg://grpc:grpc@sn-postgresql:5432/grpc')
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        return session


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String, nullable=False)
    text = Column(String, nullable=False)


class UnaryPostService(pb2_grpc.UnaryPostsServicer):
    def __init__(self, *args, **kwargs):
        pass

    async def create_post(self, request, context):
        a_session = await get_session()
        user = request.user
        text = request.text
        new_post = Post(username=user, text=text)
        try:
            a_session.add(new_post)
            await a_session.commit()
            result = {'message': "Post created"}
        except:
            result = {'message': "Error updating post"}
        return pb2.MessageResponse(**result)

    async def update_post(self, request, context):
        a_session = await get_session()
        user = request.user
        id = request.id
        text = request.text
        try:
            result = await a_session.execute(select(Post).where(Post.id == id))
            post = result.scalars().one_or_none()
            if post is not None:
                if user != post.username:
                    result = {'message': "Access denied"}
                    return pb2.MessageResponse(**result)
                post.text = text
                await a_session.commit()
                result = {'message': "Post updated"}
                return pb2.MessageResponse(**result)
            else:
                result = {'message': "Post not exists"}
                return pb2.MessageResponse(**result)
        except:
            result = {'message': "Error updating post"}
        return pb2.MessageResponse(**result)

    async def delete_post(self, request, context):
        a_session = await get_session()
        user = request.user
        id = request.id
        result = await a_session.execute(select(Post).where(Post.id == id))
        post = result.scalars().one_or_none()
        if post is not None:
            if user != post.username:
                result = {'message': "Access denied"}
                return pb2.MessageResponse(**result)
            await a_session.delete(post)
            await a_session.commit()
            result = {'message': "Post deleted"}
            return pb2.MessageResponse(**result)
        else:
            result = {'message': "Post not exists"}
            return pb2.MessageResponse(**result)

    async def get_post(self, request, context):
        a_session = await get_session()
        id = request.id
        result = await a_session.execute(select(Post).where(Post.id == id))
        post = result.scalars().one_or_none()
        if post is not None:
            result = {'message': post.text, 'user': post.username}
            return pb2.PostResponse(**result)
        else:
            result = {'message': "Post not exists"}
            return pb2.MessageResponse(**result)

    async def get_posts(self, request, context):
        a_session = await get_session()
        user = request.user
        result = await a_session.execute(select(Post).where(Post.username == user))
        posts = result.scalars().all()
        result = {'posts': [{'id': p.id, 'text': p.text} for p in posts]}
        return pb2.PostsResponse(**result)


async def serve():
    server = aio.server()
    pb2_grpc.add_UnaryPostsServicer_to_server(UnaryPostService(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    start_connection()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
