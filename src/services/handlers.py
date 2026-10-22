from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
)

from db.repositories.tasks import (
    add_task,
    complete_task,
    count_tasks,
    get_tasks,
    remove_task,
)
from middleware.auth import authorized
from middleware.log import logger
from utils.helper import parse_task_id


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

    task_id = add_task(title)
    await update.effective_message.reply_text(
        f"✅ Task #{task_id} creata: {title}"
    )


def build_task_list(today: bool = False):
    tasks = get_tasks(today=today)
    heading = "Task aperte create oggi" if today else "Task aperte"

    if not tasks:
        return f"{heading}: nessuna attività.", None

    total = count_tasks(today=today)
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

    text, markup = build_task_list(today)
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

    if complete_task(task_id):
        await query.answer(f"✅ Task #{task_id} completata")
    else:
        await query.answer(
            "Task inesistente o già completata.", show_alert=True
        )

    # Rigenera la lista in ogni caso
    text, markup = build_task_list(today=(scope == "t"))
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
        except Exception:
            logger.exception("Impossibile inviare il messaggio di errore")