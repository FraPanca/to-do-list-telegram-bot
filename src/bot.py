from telegram import (
    BotCommand,
    BotCommandScopeChat,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
)

from config.constants import ADMIN_USER_ID, TOKEN
from db.schema import init_db
from middleware.log import logger
from services.handlers import (
    add_command,
    adduser_command,
    button_handler,
    delete_command,
    deleteuser_command,
    done_command,
    error_handler,
    help_command,
    list_command,
    listuser_command,
    start,
    today_command,
)


async def post_init(app: Application):
    user_commands = [
        BotCommand("start", "Avvia il bot"),
        BotCommand("add", "Aggiungi una task"),
        BotCommand("list", "Mostra le task aperte"),
        BotCommand("today", "Task create oggi"),
        BotCommand("done", "Completa una task"),
        BotCommand("delete", "Elimina una task"),
        BotCommand("help", "Mostra l'aiuto"),
    ]
    admin_commands = user_commands + [
        BotCommand("adduser", "Aggiunge un user"),
        BotCommand("deleteuser", "Rimuove un user"),
        BotCommand("listuser", "Mostra tutti gli user"),
    ]
    await app.bot.set_my_commands(user_commands)
    await app.bot.set_my_commands(
        admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_USER_ID)
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
    app.add_handler(CommandHandler("adduser", adduser_command))
    app.add_handler(CommandHandler("deleteuser", deleteuser_command))
    app.add_handler(CommandHandler("listuser", listuser_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    logger.info("Avvio del bot Telegram")
    app.run_polling()


if __name__ == "__main__":
    main()