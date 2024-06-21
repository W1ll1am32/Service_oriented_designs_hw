import os
import pytest
from testcontainers.postgres import PostgresContainer
from src.main import UnaryPostService, Post, start_connection
from unary.posts import unaryposts_pb2 as pb2
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
                CREATE TABLE posts (
                    id serial PRIMARY KEY,
                    username varchar not null,
                    text varchar not null)
                """)
            conn.commit()


def get_post_by_id(id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, text FROM posts WHERE id = {}".format(id))
            (id, username, text) = cur.fetchone()
            post = Post()
            post.id = id
            post.username = username
            post.text = text
            return post


def delete_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM posts")
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
async def test_create_post():
    start_connection()
    test = UnaryPostService()
    res = await test.create_post(pb2.Create(user="user", text="text"), None)
    assert isinstance(res, pb2.MessageResponse)
    assert res.message == "Post created"
    post = get_post_by_id(1)
    assert post.username == "user"
    assert post.text == "text"
