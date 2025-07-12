# main.py

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from config import TOKEN
from handlers_user import (
    start, message_handler, callback_query_handler,
    profile_handler, change_fio_handler, save_new_fio_handler
)
from handlers_admin import (
    admin_panel_entry, admin_callback_handler, admin_message_handler
)
from utils import ensure_dirs

# 1. Настройка логгера
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    print("🚀 Запуск бота... (PTB 13)")
    ensure_dirs()
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    # USER HANDLERS
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    dp.add_handler(CallbackQueryHandler(callback_query_handler))

    # ADMIN HANDLERS (через Callback)
    dp.add_handler(CommandHandler("admin", admin_panel_entry))
    dp.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="admin_"))
    dp.add_handler(MessageHandler(Filters.text & Filters.user(username="admin"), admin_message_handler))

    print("✅ Бот успешно запущен! Жду ваши команды.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
