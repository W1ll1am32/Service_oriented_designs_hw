import os
import pytest
from testcontainers.postgres import PostgresContainer
from src.main import UnaryStatsService, Statistics, start_connection
from unary.stats import unarystats_pb2 as pb2
import psycopg

postgres = PostgresContainer("postgres:14")


def get_connection():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    username = os.getenv("DB_USERNAME", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    database = os.getenv("DB_NAME", "postgres")
    return psycopg.connect(f"host={host} dbname={database} user={username} password={password} port={port}")


def create_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE statistics (
                    id serial PRIMARY KEY,
                    post_id integer not null,
                    username varchar not null,
                    action varchar not null,
                    author varchar not null)
                """)
            conn.commit()


def create_stat(id, user, action, author):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO statistics (post_id, username, action, author) VALUES (%s, %s, %s, %s)", (id, user, action, author))
            conn.commit()


def delete_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM statistics")
            conn.commit()


@pytest.fixture(scope="module", autouse=True)
def setup(request):
    postgres.start()

    def remove_container():
        postgres.stop()

    request.addfinalizer(remove_container)
    postgres.driver = "+asyncpg"
    os.environ["DB_CONN"] = postgres.get_connection_url()
    os.environ["DB_HOST"] = postgres.get_container_host_ip()
    os.environ["DB_PORT"] = postgres.get_exposed_port(5432)
    os.environ["DB_USERNAME"] = postgres.username
    os.environ["DB_PASSWORD"] = postgres.password
    os.environ["DB_NAME"] = postgres.dbname
    os.environ["DB_URL"] = postgres.get_connection_url()
    create_table()


@pytest.fixture(scope="function", autouse=True)
def setup_data():
    delete_all()


@pytest.mark.asyncio
async def test_get_stats():
    start_connection()
    test = UnaryStatsService()
    create_stat(1, "a", "LIKED", "b")
    create_stat(1, 'a', 'WATCHED', 'b')
    res = await test.get_post_stats(pb2.Post(id=1), None)
    assert isinstance(res, pb2.MessageResponse)
    assert res.message == "Post id: 1 Likes: 1 Views: 1"
