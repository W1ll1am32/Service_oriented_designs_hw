from unittest import IsolatedAsyncioTestCase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from ..src.main import UserModel, get_session


class MainTestCase(IsolatedAsyncioTestCase):
    def test_dto_conversion(self):
        Base = declarative_base()

        class TestUser(Base):
            __tablename__ = "users"

            id = Column(Integer, primary_key=True, autoincrement=True, index=True)
            username = Column(String, nullable=False)
            password = Column(String, nullable=False)
            name = Column(String, nullable=True)
            surname = Column(String, nullable=True)
            birthday = Column(String, nullable=True)
            email = Column(String, nullable=True)
            phone = Column(String, nullable=True)

            def set_data(self):
                self.username = "user"
                self.password = "pass"
                self.name = "name"
                self.surname = "surname"
                self.birthday = "12.02.01"
                self.email = "asd@asd"
                self.phone = "12321"

        test_user = TestUser()
        test_user.set_data()
        test_res = UserModel(username="user", password="pass", name="name", surname="surname", birthday="12.02.01",
                             email="asd@asd", phone="12321")
        self.assertEqual(UserModel.from_dao(test_user), test_res)

    async def test_session_getter(self):
        async for ses in get_session():
            self.assertIsInstance(ses, AsyncSession)
