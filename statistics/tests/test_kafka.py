import os
import pytest
import logging
from testcontainers.postgres import PostgresContainer
from testcontainers.kafka import KafkaContainer
from src.main import start_connection, app, consume, start_connection, loop
from aiokafka import AIOKafkaProducer
import asyncio
import psycopg
import json


postgres = PostgresContainer("postgres:14")
kafka = KafkaContainer()
proc = None


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


def get_all_stats():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM statistics")
            return [(id, post_id, username, action, author) for id, post_id, username, action, author in cur]


def delete_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM statistics")
            conn.commit()


@pytest.fixture(scope="module", autouse=True)
def setup(request):
    postgres.start()
    kafka.start()

    def remove_container():
        postgres.stop()
        kafka.stop()

    request.addfinalizer(remove_container)
    postgres.driver = "+asyncpg"
    os.environ["KAFKA"] = kafka.get_bootstrap_server()
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


async def send_one():
    producer = AIOKafkaProducer(
        bootstrap_servers=os.getenv("KAFKA"))
    await producer.start()
    try:
        await producer.send('statistics', json.dumps({"post_id": 1, "username": "a", "action": 'WATCHED', "author": "b"}).encode("ascii"), partition=0)
        await producer.flush()
    finally:
        await producer.stop()


"""
async def consume_one():
    consumer = AIOKafkaConsumer('statistics', bootstrap_servers=os.getenv("KAFKA"))
    await consumer.start()
    a = consumer.assignment()
    t = await consumer.topics()
    await consumer.seek_to_beginning()
    try:
        # Вот до сюда доходит программа, но застревает на async for
        msg = await consumer.getone()
        data = json.loads(msg.value.decode("ascii"))
        print(data)
    finally:
        await consumer.stop()
"""


@pytest.mark.asyncio
async def test_kafka_stats():
    logging.basicConfig(level=logging.INFO)
    start_connection(lp=asyncio.get_event_loop())
    await send_one()
    await asyncio.sleep(1)
    asyncio.create_task(consume())
    await asyncio.sleep(1)
    res = get_all_stats()
    assert len(res) == 1
    for id, post_id, username, action, author in res:
        assert post_id == 1
        assert username == "a"
        assert action == "WATCHED"
        assert author == "b"
