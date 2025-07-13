import os
import logging
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from database import init_db
from keyboards import main_menu_keyboard
from handlers import start, button, text_handler, admin_command
from notifications import setup_notifications
from admin import handle_admin_callback

# Загрузка переменных окружения
load_dotenv()

# Создание папки logs, если её нет
os.makedirs('logs', exist_ok=True)

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='logs/bot.log'
)
logger = logging.getLogger(__name__)

def main():
    # Инициализация базы данных
    init_db()

    # Запуск бота
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("Не установлен TELEGRAM_BOT_TOKEN!")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Регистрация обработчиков
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_command))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CallbackQueryHandler(handle_admin_callback, pattern='admin_'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    # Настройка уведомлений
    setup_notifications(updater.job_queue)

    # Запуск бота
    updater.start_polling()
    logger.info("Бот успешно запущен!")
    updater.idle()

if __name__ == "__main__":
    main()