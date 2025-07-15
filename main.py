#!/usr/bin/env python3
"""
Telegram Bot для отслеживания прибытия/убытия персонала
Главный файл для запуска бота на aiogram 3.x
"""

import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
import aioschedule
import threading
import time

# Импорт модулей
from handlers import register_handlers
from keyboards import get_main_keyboard, get_admin_keyboard
from admin import AdminPanel
from notifications import NotificationSystem
from database import Database
from config import Config
from keep_alive import keep_alive

# Создание необходимых папок для Replit
for folder in ["data", "logs", "exports"]:
    os.makedirs(folder, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация компонентов
config = Config()
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()
notification_system = NotificationSystem(bot, db)
admin_panel = AdminPanel(db, notification_system)

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_location = State()
    waiting_for_confirmation = State()

# Глобальные переменные для управления ботом
bot_running = True
schedule_thread = None

def run_scheduler():
    """Запуск планировщика уведомлений"""
    global bot_running
    while bot_running:
        try:
            asyncio.run(aioschedule.run_pending())
            time.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка планировщика: {e}")
            time.sleep(5)

async def on_startup():
    """Инициализация при запуске бота"""
    logger.info("🚀 Бот запускается...")
    
    try:
        # Создаем папки если не существуют
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        os.makedirs('exports', exist_ok=True)
        
        # Инициализация базы данных
        await db.init()
        
        # Регистрация обработчиков
        register_handlers(dp, admin_panel, notification_system)
        
        # Запуск планировщика уведомлений
        global schedule_thread
        schedule_thread = threading.Thread(target=run_scheduler, daemon=True)
        schedule_thread.start()
        
        logger.info("✅ Бот успешно запущен!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        raise

async def on_shutdown():
    """Очистка при остановке бота"""
    logger.info("🛑 Бот останавливается...")
    global bot_running
    bot_running = False
    
    try:
        # Закрытие соединений
        await bot.session.close()
        await storage.close()
        
        logger.info("✅ Бот успешно остановлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")

# Обработчики команд
from aiogram.filters import Command

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "Неизвестный"
    
    logger.info(f"👋 Пользователь {username} ({user_id}) запустил бота")
    
    # Проверяем, зарегистрирован ли пользователь
    user_info = await db.get_user_info(user_id)
    
    if user_info:
        # Пользователь уже зарегистрирован
        await message.answer(
            f"👋 Добро пожаловать обратно, {user_info['full_name']}!\n"
            f"📍 Ваш статус: {user_info['status']}\n"
            f"📍 Местоположение: {user_info['location']}\n\n"
            f"🎯 Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Новый пользователь
        await message.answer(
            f"👋 Добро пожаловать в бот учета персонала!\n\n"
            f"🎯 Для начала работы нужно пройти регистрацию.\n"
            f"📝 Введите ваше полное имя (Фамилия Имя Отчество):",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 *Справка по боту учета персонала*\n\n"
        "🎯 *Основные команды:*\n"
        "• /start - Запуск бота\n"
        "• /help - Справка\n"
        "• /status - Текущий статус системы\n"
        "• /admin - Панель администратора\n\n"
        "🔧 *Функции:*\n"
        "• ✅ Отметка прибытия/убытия\n"
        "• 📍 Указание местоположения\n"
        "• 📊 Просмотр статистики\n"
        "• 🔔 Автоматические уведомления\n"
        "• 🎛️ Админ-панель (для администраторов)\n\n"
        "❓ *Нужна помощь?*\n"
        "Обратитесь к администратору системы."
    )
    
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("status"))
async def status_command(message: types.Message):
    """Обработчик команды /status"""
    try:
        present_users = await db.get_present_users()
        absent_users = await db.get_absent_users()
        
        status_text = (
            f"📊 *Текущий статус системы*\n\n"
            f"✅ Присутствуют: {present_users}\n"
            f"❌ Отсутствуют: {absent_users}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}"
        )
        
        await message.answer(status_text, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        await message.answer("❌ Ошибка получения статуса системы")

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    """Обработчик команды /admin"""
    user_id = message.from_user.id
    
    if await admin_panel.is_admin(user_id):
        await message.answer(
            "🏠 *Главное меню админ-панели*\n\n"
            "Выберите нужный раздел:",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer("❌ У вас нет прав администратора")

@dp.error()
async def error_handler(event):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {event.exception}")
    
    try:
        if event.update.message:
            await event.update.message.answer(
                "❌ Произошла ошибка при обработке запроса. Попробуйте позже."
            )
    except:
        pass

async def main():
    """Основная функция запуска бота"""
    try:
        await on_startup()
        logger.info("🚀 Начинаю polling...")
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except FileNotFoundError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        print(f"\n{e}")
    except ValueError as e:
        logger.error(f"❌ Ошибка настройки: {e}")
        print(f"\n{e}")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        print(f"💥 Критическая ошибка: {e}")
        print("🔧 Проверьте настройки в файле .env")
        print("📖 Инструкция по настройке: КАК_ЗАПУСТИТЬ_БОТА.md")
    finally:
        await on_shutdown()

if __name__ == '__main__':
    keep_alive()
    asyncio.run(main())

# Healthcheck-отчёт админу каждые 6 часов
import asyncio
from aiogram import Bot
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
bot = Bot(token=BOT_TOKEN)

async def healthcheck():
    while True:
        try:
            await bot.send_message(ADMIN_ID, "Healthcheck: бот жив!")
        except Exception as e:
            print(f"Healthcheck error: {e}")
        await asyncio.sleep(6 * 60 * 60)  # 6 часов

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(healthcheck())