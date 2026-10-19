import logging
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "todo.db"

load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
USER_ID_RAW = os.getenv("TELEGRAM_USER_ID", "")

if not TOKEN or not USER_ID_RAW:
    raise RuntimeError("Configura TELEGRAM_BOT_TOKEN e TELEGRAM_USER_ID nel file .env")

try:
    ALLOWED_USER_ID = int(USER_ID_RAW)
except ValueError as exc:
    raise RuntimeError("TELEGRAM_USER_ID deve essere un numero intero") from exc

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
                    CHECK(length(trim(title)) BETWEEN 1 AND 500),
                created_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                ),
                completed_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_open
            ON tasks(completed_at, id)
        """)


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
        query += " AND date(created_at) = date('now')"
    query += " ORDER BY id DESC LIMIT 20"

    with connect_db() as conn:
        return conn.execute(query).fetchall()


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


async def authorized(update: Update) -> bool:
    user = update.effective_user
    if user and user.id == ALLOWED_USER_ID:
        return True

    # Non rivelare dettagli del bot agli utenti non autorizzati.
    if update.callback_query:
        await update.callback_query.answer(
            "Non autorizzato.", show_alert=True
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            "Non autorizzato."
        )
    return False


def parse_task_id(args) -> int | None:
    if len(args) != 1:
        return None
    try:
        value = int(args[0])
        return value if value > 0 else None
    except ValueError:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await authorized(update):
        return
    await update.effective_message.reply_text(
        "Ciao! Sono la tua to-do list.\n\n"
        "Usa /add per creare un'attività e /list per visualizzarla.\n"
        "Scrivi /help per tutti i comandi."
    )


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized(update):
        return
    await update.effective_message.reply_text(
        "/add testo - crea una task\n"
        "/list - mostra le task aperte\n"
        "/today - task create oggi\n"
        "/done ID - completa una task\n"
        "/delete ID - elimina una task\n"
        "/help - mostra questo messaggio"
    )


async def add_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized(update):
        return

    title = " ".join(context.args).strip()
    if not title:
        await update.effective_message.reply_text(
            "Scrivi la task dopo il comando.\n"
            "Esempio: /add Comprare il latte"
        )
        return

    if len(title) > 500:
        await update.effective_message.reply_text(
            "La descrizione non può superare 500 caratteri."
        )
        return

    task_id = add_task(title)
    await update.effective_message.reply_text(
        f"✅ Task #{task_id} creata: {title}"
    )


async def show_tasks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    today: bool = False,
):
    if not await authorized(update):
        return

    tasks = get_tasks(today=today)
    heading = "Task aperte create oggi" if today else "Task aperte"

    if not tasks:
        await update.effective_message.reply_text(
            f"{heading}: nessuna attività."
        )
        return

    lines = [f"{heading} (massimo 20):"]
    keyboard = []

    for task in tasks:
        lines.append(f"▫️ #{task['id']} - {task['title']}")
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Completa #{task['id']}",
                callback_data=f"done:{task['id']}",
            )
        ])

    await update.effective_message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def list_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await show_tasks(update, context)


async def today_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await show_tasks(update, context, today=True)


async def done_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized(update):
        return

    task_id = parse_task_id(context.args)
    if task_id is None:
        await update.effective_message.reply_text(
            "Uso: /done ID\nEsempio: /done 12"
        )
        return

    if complete_task(task_id):
        await update.effective_message.reply_text(
            f"✅ Task #{task_id} completata."
        )
    else:
        await update.effective_message.reply_text(
            "Task inesistente o già completata."
        )


async def delete_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized(update):
        return

    task_id = parse_task_id(context.args)
    if task_id is None:
        await update.effective_message.reply_text(
            "Uso: /delete ID\nEsempio: /delete 12"
        )
        return

    if remove_task(task_id):
        await update.effective_message.reply_text(
            f"🗑 Task #{task_id} eliminata."
        )
    else:
        await update.effective_message.reply_text(
            "Task non trovata."
        )


async def button_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if not await authorized(update):
        return

    await query.answer()

    try:
        action, raw_id = query.data.split(":", 1)
        task_id = int(raw_id)
    except (ValueError, AttributeError):
        await query.message.reply_text("Azione non valida.")
        return

    if action != "done" or task_id <= 0:
        await query.message.reply_text("Azione non valida.")
        return

    if complete_task(task_id):
        await query.edit_message_text(
            f"✅ Task #{task_id} completata."
        )
    else:
        await query.message.reply_text(
            "Task inesistente o già completata."
        )


async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Avvia il bot"),
        BotCommand("add", "Aggiungi una task"),
        BotCommand("list", "Mostra le task aperte"),
        BotCommand("today", "Task create oggi"),
        BotCommand("done", "Completa una task"),
        BotCommand("delete", "Elimina una task"),
        BotCommand("help", "Mostra l'aiuto"),
    ])


async def error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
):
    logger.error(
        "Errore durante l'elaborazione di un aggiornamento",
        exc_info=context.error,
    )


def main():
    init_db()

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    logger.info("Avvio del bot Telegram")
    app.run_polling()


if __name__ == "__main__":
    main()
