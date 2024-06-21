from unittest import IsolatedAsyncioTestCase
from ..src.main import UnaryStatsService, start_connection
from unary.stats import unarystats_pb2 as pb2


class StatTestCase(IsolatedAsyncioTestCase):
    async def test_stat(self):
        start_connection()
        test = UnaryStatsService()
        res = await test.get_post_stats(pb2.Post(id=1), None)
        self.assertIsInstance(res, pb2.MessageResponse)

    async def test_top(self):
        start_connection()
        test = UnaryStatsService()
        res = await test.get_user_top(pb2.Empty(), None)
        self.assertIsInstance(res, (pb2.MessageResponse, pb2.TopUserResponse))
