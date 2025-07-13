#!/usr/bin/env python3
"""
Telegram Bot для отслеживания прибытия/убытия персонала
Главный файл для запуска бота
"""

import logging
import asyncio
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes

# Импортируем обработчики
from handlers import (
    start_command, register_user, location_handler, 
    admin_command, help_command, status_command,
    button_handler, cancel_handler
)
from database import init_db, close_db
from notifications_v2 import start_notification_scheduler_v2
from utils import is_admin

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла ошибка при обработке запроса. Попробуйте еще раз или обратитесь к администратору.",
            parse_mode='HTML'
        )

async def main():
    """Основная функция для запуска бота"""
    # Инициализируем базу данных
    init_db()
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("register", register_user))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("cancel", cancel_handler))
    
    # Добавляем обработчики callback-запросов
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Добавляем обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, location_handler))
    
    # Добавляем обработчик ошибок
    app.add_error_handler(error_handler)
    
    # Запускаем планировщик уведомлений v2.0
    start_notification_scheduler_v2(app)
    
    logger.info("🚀 Бот запущен")
    print("🚀 Бот запущен и готов к работе!")
    
    # Запускаем бота
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        close_db()
        logger.info("Бот завершил работу")