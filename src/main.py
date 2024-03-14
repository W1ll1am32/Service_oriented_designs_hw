from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Optional
from sqlalchemy import Column, String, Integer, Date, DateTime, Interval, ForeignKeyConstraint, Index
from os import environ
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import jwt
import uvicorn

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


@app.post('/user/register', tags=["user"])
async def register_user(data: InputModel, a_session: AsyncSession = Depends(get_session)):
    result = await a_session.execute(
        select(User).where(and_(User.username == data.username, User.password == data.password)))
    check = result.scalars().one_or_none()
    if check:
        return JSONResponse(content={'message': 'user already exists'}, status_code=401)
    new_user = User(username=data.username, password=hash_pwd.hash(data.password))
    a_session.add(new_user)
    await a_session.commit()
    return JSONResponse(content={'message': 'user created'}, status_code=201)


@app.post('/user/login', tags=["user"])
async def login_user(data: InputModel, a_session: AsyncSession = Depends(get_session)):
    try:
        result = await a_session.execute(
            select(User).where(User.username == data.username))
        user = result.scalars().one_or_none()
        if user and hash_pwd.verify(data.password, user.password):
            token = jwt.encode({'username': user.username}, jwt_secret, algorithm=jwt_algorithm)
            return {"access_token": token, "token_type": "bearer"}
        else:
            return JSONResponse(content={'message': 'wrong login/password'}, status_code=401)
    except:
        return JSONResponse(content={'message': 'error logging in'}, status_code=500)


# get all users
@app.get('/admin/users', tags=["admin"])
async def get_users(a_session: AsyncSession = Depends(get_session)):
    result = await a_session.execute(select(User))
    users = result.scalars().all()
    return JSONResponse(content=[UserModel.from_dao(user) for user in users], status_code=200)


# get a user by id
@app.get('/user/profile', tags=["user"])
async def get_user(token: str = Depends(oauth2), a_session: AsyncSession = Depends(get_session)):
    try:
        result = await a_session.execute(
            select(User).where(
                User.username == jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username']))
        user = result.scalars().one_or_none()
        if user:
            return JSONResponse(content={'user': UserModel.from_dao(user)}, status_code=200)
        return JSONResponse(content={'message': 'user not logged in'}, status_code=401)
    except:
        return JSONResponse(content={'message': 'error getting user'}, status_code=500)


# update a user
@app.put('/user/update', tags=["user"])
async def update_user(data: UpdateModel, token: str = Depends(oauth2), a_session: AsyncSession = Depends(get_session)):
    try:
        result = await a_session.execute(
            select(User).where(
                User.username == jwt.decode(token, jwt_secret, algorithms=jwt_algorithm)['username']))
        user = result.scalars().one_or_none()
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


"""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
