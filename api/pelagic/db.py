from contextlib import contextmanager
from pathlib import Path
import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    if os.getenv("RENDER") or os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError(
            "DATABASE_URL environment variable is required in production. "
            "Please configure DATABASE_URL in your Render service environment."
        )
    return "postgresql:///maritime_oil_v2"


@contextmanager
def connection():
    with psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
    ) as conn:
        yield conn


def init_schema():
    with connection() as conn:
        conn.execute((Path(__file__).parent / "schema.sql").read_text())
