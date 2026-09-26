import os, uuid
import pytest, psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from pelagic.main import app
from pelagic.auth import ATTEMPTS
from pelagic.db import ROOT


@pytest.fixture(scope="session", autouse=True)
def database():
    original = os.environ["DATABASE_URL"]
    schema = "test_" + uuid.uuid4().hex[:12]
    # All mutable test records live in an ephemeral schema, never the demo tables.
    with psycopg.connect(original, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    os.environ["DATABASE_URL"] = make_conninfo(
        original, options=f"-c search_path={schema},public"
    )
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute((ROOT / "api/pelagic/schema.sql").read_text())
        for table in ["observations", "tracks", "cases"]:
            conn.execute(
                sql.SQL("INSERT INTO {} SELECT * FROM public.{}").format(
                    sql.Identifier(schema, table), sql.Identifier(table)
                )
            )
        hasher = PasswordHasher()
        for role in ["public", "authority", "admin"]:
            conn.execute(
                "INSERT INTO users(id,email,name,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
                (
                    uuid.uuid4(),
                    f"{role}@test.local",
                    role,
                    hasher.hash("test-password-only"),
                    role,
                ),
            )
    yield
    os.environ["DATABASE_URL"] = original
    with psycopg.connect(original, autocommit=True) as conn:
        conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def client():
    ATTEMPTS.clear()
    with TestClient(app, headers={"Origin": "http://127.0.0.1:3100"}) as c:
        yield c


@pytest.fixture
def authority(client):
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "authority@test.local", "password": "test-password-only"},
        ).status_code
        == 200
    )
    return client


@pytest.fixture
def admin(client):
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "admin@test.local", "password": "test-password-only"},
        ).status_code
        == 200
    )
    return client
