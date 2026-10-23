from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
)

from config.constants import ADMIN_USER_ID
from db.repositories.tasks import (
    add_task,
    complete_task,
    count_tasks,
    get_tasks,
    remove_task,
)
from db.repositories.users import (
    add_user,
    get_users,
    remove_user,
)
from middleware.auth import authorized, authorized_admin
from middleware.log import logger
from utils.helper import parse_positive_int


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

    text = (
        "/add testo - crea una task\n"
        "/list - mostra le task aperte\n"
        "/today - task create oggi\n"
        "/done ID - completa una task\n"
        "/delete ID - elimina una task\n"
        "/help - mostra questo messaggio"
    )
    if update.effective_user.id == ADMIN_USER_ID:
        text += (
            "\n\nAdmin:\n"
            "/adduser USER_ID - aggiunge un utente\n"
            "/deleteuser USER_ID - rimuove un utente\n"
            "/listuser - mostra gli utenti"
        )
    
    await update.effective_message.reply_text(text)


async def adduser_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized_admin(update):
        return

    user_id = parse_positive_int(context.args)
    if user_id is None:
        await update.effective_message.reply_text(
            "Uso: /adduser USER_ID\nEsempio: /adduser 1234567890"
        )
        return

    if add_user(user_id):
        await update.effective_message.reply_text(f"✅ User {user_id} aggiunto.")
    else:
        await update.effective_message.reply_text("User già esistente.")


async def deleteuser_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized_admin(update):
        return

    user_id = parse_positive_int(context.args)
    if user_id is None:
        await update.effective_message.reply_text(
            "Uso: /deleteuser USER_ID\nEsempio: /deleteuser 1234567890"
        )
        return
    
    if user_id == ADMIN_USER_ID:
        await update.effective_message.reply_text(
            "Impossibile rimuovere l'admin."
        )
        return

    if remove_user(user_id):
        await update.effective_message.reply_text(
            f"🗑 User #{user_id} rimosso."
        )
    else:
        await update.effective_message.reply_text(
            "User non trovato."
        )

def build_user_list() -> str:
    users = get_users()
    lines = [f"Utenti totali ({len(users)}):"]
    for n, user_id in enumerate(users, start=1):
        lines.append(f"{n}. {user_id}")
        
    return "\n".join(lines)


async def show_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized_admin(update):
        return

    text = build_user_list()
    await update.effective_message.reply_text(
        text
    )


async def listuser_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await show_users(update, context)


async def add_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await authorized(update):
        return

    # Mantiene spazi e a capo interni; funziona anche con /add@nomebot testo
    parts = (update.effective_message.text or "").split(maxsplit=1)
    title = parts[1].strip() if len(parts) > 1 else ""
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

    task_id = add_task(update.effective_user.id, title)
    await update.effective_message.reply_text(
        f"✅ Task #{task_id} creata: {title}"
    )


def build_task_list(owner_id: int, today: bool = False):
    tasks = get_tasks(owner_id, today=today)
    heading = "Task aperte create oggi" if today else "Task aperte"

    if not tasks:
        return f"{heading}: nessuna attività.", None

    total = count_tasks(owner_id, today=today)
    scope = "t" if today else "a"
    lines = [f"{heading} (mostro {len(tasks)} di {total}):"]
    keyboard = []

    for task in tasks:
        title = task["title"]
        if len(title) > 80:
            title = title[:80] + "…"
        lines.append(f"▫️ #{task['id']} - {title}")
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Completa #{task['id']}",
                callback_data=f"done:{task['id']}:{scope}",
            )
        ])

    return "\n".join(lines), InlineKeyboardMarkup(keyboard)


async def show_tasks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    today: bool = False,
):
    if not await authorized(update):
        return

    text, markup = build_task_list(update.effective_user.id, today)
    await update.effective_message.reply_text(
        text, reply_markup=markup
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

    task_id = parse_positive_int(context.args)
    if task_id is None:
        await update.effective_message.reply_text(
            "Uso: /done ID\nEsempio: /done 12"
        )
        return

    if complete_task(update.effective_user.id, task_id):
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

    task_id = parse_positive_int(context.args)
    if task_id is None:
        await update.effective_message.reply_text(
            "Uso: /delete ID\nEsempio: /delete 12"
        )
        return

    if remove_task(update.effective_user.id, task_id):
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

    try:
        parts = query.data.split(":")
        # Compatibile con i vecchi bottoni "done:ID" (senza scope)
        if len(parts) == 2:
            action, raw_id = parts
            scope = "a"
        else:
            action, raw_id, scope = parts
        task_id = int(raw_id)
    except (ValueError, AttributeError):
        await query.answer("Azione non valida.", show_alert=True)
        return

    if action != "done" or task_id <= 0 or scope not in ("a", "t"):
        await query.answer("Azione non valida.", show_alert=True)
        return

    owner_id = update.effective_user.id
    if complete_task(owner_id, task_id):
        await query.answer(f"✅ Task #{task_id} completata")
    else:
        await query.answer(
            "Task inesistente o già completata.", show_alert=True
        )

    # Rigenera la lista in ogni caso
    text, markup = build_task_list(owner_id, today=(scope == "t"))
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except BadRequest:
        pass  # "message is not modified": niente da aggiornare


async def error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
):
    logger.error(
        "Errore durante l'elaborazione di un aggiornamento",
        exc_info=context.error,
    )
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Si è verificato un errore. Riprova tra poco."
            )
        except Exception:  # noqa: BLE001
            logger.exception("Impossibile inviare il messaggio di errore")