from unittest import IsolatedAsyncioTestCase
from src.main import UnaryPostService, start_connection
from unary.posts import unaryposts_pb2 as pb2


class PostTestCase(IsolatedAsyncioTestCase):
    async def test_create(self):
        start_connection()
        test = UnaryPostService()
        res = await test.create_post(pb2.Create(user="user", text="text"), None)
        self.assertIsInstance(res, pb2.MessageResponse)

    async def test_update(self):
        start_connection()
        test = UnaryPostService()
        res = await test.update_post(pb2.Update(user="user", id=1, text="text"), None)
        self.assertIsInstance(res, pb2.MessageResponse)


if __name__ == '__main__':
    unittest.main()
