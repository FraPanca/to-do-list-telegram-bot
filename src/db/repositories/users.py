from db.connection import connect_db


def add_user(user_id: int) -> bool:
    with connect_db() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
            (str(user_id),),
        )
        return cur.rowcount == 1


def remove_user(user_id: int) -> bool:
    # NB: le task dell'utente rimosso NON vengono eliminate: restano nel
    # database e ricompaiono se lo stesso user_id viene riaggiunto.
    with connect_db() as conn:
        cur = conn.execute(
            "DELETE FROM users WHERE user_id = ?",
            (str(user_id),),
        )
        return cur.rowcount == 1


def is_user_allowed(user_id: int) -> bool:
    with connect_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (str(user_id),),
        ).fetchone()
        return row is not None


def get_users() -> list[int]:
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT user_id FROM users ORDER BY id ASC"
        ).fetchall()
        return [int(r["user_id"]) for r in rows]