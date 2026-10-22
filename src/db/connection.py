import sqlite3
from contextlib import contextmanager

from config.constants import DB_PATH


@contextmanager
def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        with conn:  # commit o rollback
            yield conn
    finally:
        conn.close()