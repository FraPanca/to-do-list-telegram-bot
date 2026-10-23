from db.connection import connect_db

_TODAY = " AND date(created_at, 'localtime') = date('now', 'localtime')"


def add_task(owner_id: int, title: str) -> int:
    title = title.strip()
    if not title or len(title) > 500:
        raise ValueError("La task deve contenere da 1 a 500 caratteri.")

    with connect_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks(owner_id, title) VALUES (?, ?)",
            (owner_id, title),
        )
        return cur.lastrowid


def get_tasks(owner_id: int, today: bool = False):
    query = """
        SELECT id, title, created_at
        FROM tasks
        WHERE owner_id = ? AND completed_at IS NULL
    """
    if today:
        query += _TODAY
    query += " ORDER BY id ASC LIMIT 20"

    with connect_db() as conn:
        return conn.execute(query, (owner_id,)).fetchall()


def count_tasks(owner_id: int, today: bool = False) -> int:
    query = """
        SELECT COUNT(*) FROM tasks
        WHERE owner_id = ? AND completed_at IS NULL
    """
    if today:
        query += _TODAY
    with connect_db() as conn:
        return conn.execute(query, (owner_id,)).fetchone()[0]


def complete_task(owner_id: int, task_id: int) -> bool:
    with connect_db() as conn:
        cur = conn.execute("""
            UPDATE tasks
            SET completed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
            WHERE id = ? AND owner_id = ? AND completed_at IS NULL
        """, (task_id, owner_id))
        return cur.rowcount == 1


def remove_task(owner_id: int, task_id: int) -> bool:
    with connect_db() as conn:
        cur = conn.execute(
            "DELETE FROM tasks WHERE id = ? AND owner_id = ?",
            (task_id, owner_id),
        )
        return cur.rowcount == 1