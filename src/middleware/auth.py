from telegram import (
    Update,
)

from config.constants import ALLOWED_USER_ID


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