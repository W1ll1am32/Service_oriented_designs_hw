from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Optional
from sqlalchemy import Column, String, Integer
from os import environ
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from fastapi_pagination import Page, add_pagination, paginate
import jwt
import grpc
import asyncio
import json
from unary import unary_pb2_grpc as pb2_grpc
from unary import unary_pb2 as pb2
from google.protobuf.json_format import MessageToDict
from aiokafka import AIOKafkaProducer

tags = [
    {
        "name": "user",
        "description": "Operations with user profile"
    },
    {
        "name": "admin",
        "description": "Admin operations"
    }
]

app = FastAPI(openapi_tags=tags)
Base = declarative_base()
DATABASE_URL = environ.get('DB_URL')
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


oauth2 = OAuth2PasswordBearer(tokenUrl="user/login")
hash_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

jwt_secret = 'jwt'
jwt_algorithm = 'HS256'


loop = asyncio.get_event_loop()
producer = AIOKafkaProducer(loop=loop, bootstrap_servers='kafka:29092')


def get_producer() -> AIOKafkaProducer:
    yield producer


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    birthday = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    @classmethod
    def json(cls):
        return {'id': cls.id, 'username': cls.username, 'password': cls.password, 'name': cls.name,
                'surname': cls.surname, 'birthday': cls.birthday, 'email': cls.email, 'phone': cls.phone}


class UserModel(BaseModel):
    username: str
    password: str
    name: Optional[str] = None
    surname: Optional[str] = None
    birthday: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    @classmethod
    def from_dao(cls, dao):
        return UserModel(
            username=dao.username,
            password=dao.password,
            name=dao.name,
            surname=dao.surname,
            birthday=dao.birthday,
            email=dao.email,
            phone=dao.phone
        )


class InputModel(BaseModel):
    username: str
    password: str


class UpdateModel(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    birthday: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class PostModel(BaseModel):
    id: int
    text: str


class UnaryClient(object):
    """
    Client for gRPC functionality
    """
    def __init__(self):
        self.host = 'grpc'
        self.server_port = 50051

        # instantiate a channel
        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, self.server_port))

        # bind the client and the server
        self.stub = pb2_grpc.UnaryStub(self.channel)

    async def create_post(self, user, text):
        request = pb2.Create(user=user, text=text)
        res = self.stub.create_post(request)
        return res

    async def update_post(self, user, id, text):
        request = pb2.Update(user=user, id=id, text=text)
        res = self.stub.update_post(request)
        return res

    async def delete_post(self, user, id):
        request = pb2.Get(user=user, id=id)
        res = self.stub.delete_post(request)
        return res

    async def get_post(self, id):
        request = pb2.Get(id=id)
        res = self.stub.get_post(request)
        return res

    async def get_posts(self, user):
        request = pb2.GetAll(user=user)
        res = self.stub.get_posts(request)
        return res


async def get_client() -> UnaryClient:
    client = UnaryClient()
    yield client


async def get_by_username(session: AsyncSession, username: str):
    result = await session.execute(
        select(User).where(User.username == username))
    user = result.scalars().one_or_none()
    return user


@app.post('/user/register', tags=["user"])
async def register_user(data: InputModel, a_session: AsyncSession = Depends(get_session)) -> JSONResponse:
    check = await get_by_username(session=a_session, username=data.username)
    if check:
        return JSONResponse(content={'message': 'user already exists'}, status_code=401)
    new_user = User(username=data.username, password=hash_pwd.hash(data.password))
    a_session.add(new_user)
    await a_session.commit()
    return JSONResponse(content={'message': 'user created'}, status_code=201)


@app.post('/user/login', tags=["user"])
async def login_user(data: OAuth2PasswordRequestForm = Depends(), a_session: AsyncSession = Depends(get_session)):
    try:
        user = await get_by_username(session=a_session, username=data.username)
        if user and hash_pwd.verify(data.password, user.password):
            token = jwt.encode({'username': user.username}, jwt_secret, algorithm=jwt_algorithm)
            return {"access_token": token, "token_type": "bearer"}
        else:
            return JSONResponse(content={'message': 'wrong login/password'}, status_code=401)
    except:
        return JSONResponse(content={'message': 'error logging in'}, status_code=500)


# get all users
@app.get('/admin/users', tags=["admin"])
async def get_users(a_session: AsyncSession = Depends(get_session)) -> list[UserModel]:
    result = await a_session.execute(select(User))
    users = result.scalars().all()
    return [UserModel.from_dao(user) for user in users]


@app.get('/user/profile', tags=["user"])
async def get_user(token: str = Depends(oauth2), a_session: AsyncSession = Depends(get_session)) -> UserModel | JSONResponse:
    try:
        user = await get_by_username(session=a_session, username=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username'])
        if user:
            return UserModel.from_dao(user)
        return JSONResponse(content={'message': 'user not logged in'}, status_code=401)
    except:
        return JSONResponse(content={'message': 'error getting user'}, status_code=500)


# update a user
@app.put('/user/update', tags=["user"])
async def update_user(data: UpdateModel, token: str = Depends(oauth2), a_session: AsyncSession = Depends(get_session)) -> JSONResponse:
    try:
        user = await get_by_username(session=a_session, username=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username'])
        if user:
            if data.name:
                user.name = data.name
            if data.surname:
                user.surname = data.surname
            if data.birthday:
                user.birthday = data.birthday
            if data.email:
                user.email = data.email
            if data.phone:
                user.phone = data.phone
            await a_session.commit()
            return JSONResponse(content={'message': 'user updated'}, status_code=200)
        return JSONResponse(content={'message': 'user not found'}, status_code=404)
    except:
        return JSONResponse(content={'message': 'error updating user'}, status_code=500)


@app.post('/user/post', tags=["post"])
async def create_post(data: PostModel, token: str = Depends(oauth2), grpc_client: UnaryClient = Depends(get_client)) -> JSONResponse:
    result = await grpc_client.create_post(user=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username'], text=data.text)
    return JSONResponse(content={'message': MessageToDict(result)['message']}, status_code=200)


@app.post('/user/post/{id}', tags=["post"])
async def update_post(id: int, data: PostModel, token: str = Depends(oauth2), grpc_client: UnaryClient = Depends(get_client)) -> JSONResponse:
    result = await grpc_client.update_post(user=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username'], id=id, text=data.text)
    return JSONResponse(content={'message': MessageToDict(result)['message']}, status_code=200)


@app.delete('/user/post/{id}', tags=["post"])
async def delete_post(id: int, token: str = Depends(oauth2), grpc_client: UnaryClient = Depends(get_client)) -> JSONResponse:
    result = await grpc_client.delete_post(user=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username'], id=id)
    return JSONResponse(content={'message': MessageToDict(result)['message']}, status_code=200)


@app.get('/users/like/{post_id}', tags=["users"])
async def like_post(post_id: int, token: str = Depends(oauth2), grpc_client: UnaryClient = Depends(get_client), a_session: AsyncSession = Depends(get_session)) -> JSONResponse:
    if get_user(session=a_session, username=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username']):
        result = await grpc_client.get_post(id=post_id)
        message = MessageToDict(result)['message']
        if message != "Post not exists":
            await producer.send("statistics", json.dumps({"post_id": post_id,
                                                          "user": jwt.decode(token, jwt_secret,
                                                                             algorithms=jwt_algorithm)['username'],
                                                          "action": 'LIKED',
                                                          "author": MessageToDict(result)['user']}).encode("ascii"))
        return JSONResponse(content={'message': 'post liked'}, status_code=200)
    else:
        return JSONResponse(content={'message': 'user not found'}, status_code=404)


@app.get('/users/post/{post_id}', tags=["users"])
async def get_post(post_id: int, token: str = Depends(oauth2), grpc_client: UnaryClient = Depends(get_client), a_session: AsyncSession = Depends(get_session)) -> JSONResponse:
    if get_user(session=a_session, username=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username']):
        result = await grpc_client.get_post(id=post_id)
        message = MessageToDict(result)['message']
        if message != "Post not exists":
            await producer.send("statistics", json.dumps({"post_id": post_id,
                                                          "user": jwt.decode(token, jwt_secret,
                                                                             algorithms=jwt_algorithm)['username'],
                                                          "action": 'WATCHED',
                                                          "author": MessageToDict(result)['user']}).encode("ascii"))
        return JSONResponse(content={'message': message}, status_code=200)
    else:
        return JSONResponse(content={'message': 'user not found'}, status_code=404)


@app.get('/users/posts/{username}', tags=["users"])
async def get_posts(username: str, token: str = Depends(oauth2), grpc_client: UnaryClient = Depends(get_client), a_session: AsyncSession = Depends(get_session)) -> Page[PostModel] | JSONResponse:
    if get_user(session=a_session, username=jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username']):
        result = await grpc_client.get_posts(user=username)
        posts = MessageToDict(result)['posts']
        return paginate(posts['posts'])
    else:
        return JSONResponse(content={'message': 'user not found'}, status_code=404)


add_pagination(app)

"""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
