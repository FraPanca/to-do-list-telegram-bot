from config.constants import ADMIN_USER_ID
from db.connection import connect_db


def init_db():
    with connect_db() as conn:
        # Tasks
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                title TEXT NOT NULL
                    CHECK(length(trim(title)) BETWEEN 1 AND 500),
                created_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                ),
                completed_at TEXT
            )
        """)

        # Indice per ricerca ottimizzata
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_owner_open
            ON tasks(owner_id, completed_at, id)
        """)

        # Users
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL
            )
        """)

        # Inserimento admin
        conn.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
            (ADMIN_USER_ID,),
        )