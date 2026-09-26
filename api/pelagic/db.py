from contextlib import contextmanager
from pathlib import Path
import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@contextmanager
def connection():
    with psycopg.connect(
        os.environ.get("DATABASE_URL", "postgresql:///maritime_oil_v2"),
        row_factory=dict_row,
    ) as conn:
        yield conn


def init_schema():
    with connection() as conn:
        conn.execute((Path(__file__).parent / "schema.sql").read_text())
