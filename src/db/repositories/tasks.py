from db.connection import connect_db


def add_task(title: str) -> int:
    title = title.strip()
    if not title or len(title) > 500:
        raise ValueError("La task deve contenere da 1 a 500 caratteri.")

    with connect_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks(title) VALUES (?)",
            (title,),
        )
        return cur.lastrowid


def get_tasks(today: bool = False):
    query = """
        SELECT id, title, created_at
        FROM tasks
        WHERE completed_at IS NULL
    """
    if today:
        query += " AND date(created_at, 'localtime') = date('now', 'localtime')"
    query += " ORDER BY id ASC LIMIT 20"

    with connect_db() as conn:
        return conn.execute(query).fetchall()


def count_tasks(today: bool = False) -> int:
    query = "SELECT COUNT(*) FROM tasks WHERE completed_at IS NULL"
    if today:
        query += " AND date(created_at, 'localtime') = date('now', 'localtime')"
    with connect_db() as conn:
        return conn.execute(query).fetchone()[0]


def complete_task(task_id: int) -> bool:
    with connect_db() as conn:
        cur = conn.execute("""
            UPDATE tasks
            SET completed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
            WHERE id = ? AND completed_at IS NULL
        """, (task_id,))
        return cur.rowcount == 1


def remove_task(task_id: int) -> bool:
    with connect_db() as conn:
        cur = conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )
        return cur.rowcount == 1