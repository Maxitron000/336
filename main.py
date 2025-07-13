#!/usr/bin/env python3
"""
Telegram Bot для отслеживания прибытия/убытия персонала
Главный файл для запуска бота на aiogram
"""

import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.utils.exceptions import TelegramAPIError
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
from pythonanywhere_support import PythonAnywhereSupport

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
dp = Dispatcher(bot, storage=storage)
db = Database()
notification_system = NotificationSystem(bot, db)
admin_panel = AdminPanel(db, notification_system)
pythonanywhere_support = PythonAnywhereSupport(db, notification_system)

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_location = State()
    waiting_for_confirmation = State()

# Глобальные переменные для управления ботом
bot_running = True
schedule_thread = None

async def on_startup(dp):
    """Инициализация при запуске бота"""
    logger.info("🚀 Бот запускается...")
    
    try:
        # Создаем папки если не существуют
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        os.makedirs('exports', exist_ok=True)
        
        # Инициализация базы данных
        await db.init()
        
        # Настройка PythonAnywhere
        await pythonanywhere_support.setup_pythonanywhere()
        
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

async def on_shutdown(dp):
    """Очистка при остановке бота"""
    logger.info("🛑 Бот останавливается...")
    global bot_running
    bot_running = False
    
    try:
        # Закрытие соединений
        await bot.close()
        await storage.close()
        await db.close()
        
        logger.info("✅ Бот остановлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")

def run_scheduler():
    """Запуск планировщика в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Настройка расписания
    aioschedule.every().day.at("19:00").do(lambda: loop.create_task(send_daily_summary()))
    aioschedule.every().day.at("20:30").do(lambda: loop.create_task(send_reminders()))
    
    while bot_running:
        aioschedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту

async def send_daily_summary():
    """Отправка ежедневной сводки в 19:00"""
    try:
        logger.info("📊 Отправка ежедневной сводки...")
        await notification_system.send_daily_summary()
    except Exception as e:
        logger.error(f"❌ Ошибка отправки ежедневной сводки: {e}")

async def send_reminders():
    """Отправка напоминаний в 20:30"""
    try:
        logger.info("🔔 Отправка напоминаний...")
        await notification_system.send_reminders()
    except Exception as e:
        logger.error(f"❌ Ошибка отправки напоминаний: {e}")

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Удаляем сообщение с командой для чистоты чата
    try:
        await message.delete()
    except TelegramAPIError:
        pass  # Игнорируем ошибки удаления
    
    # Проверяем, является ли пользователь админом
    is_admin = await admin_panel.is_admin(user_id)
    
    if is_admin:
        # Показываем админ-панель
        await message.answer(
            f"🏠 *Главное меню админ-панели*\n\n"
            f"Добро пожаловать, {user_name}!\n"
            f"Выберите нужный раздел:",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Показываем обычное меню
        await message.answer(
            f"👋 *Добро пожаловать в систему учета личного состава!*\n\n"
            f"Привет, {user_name}!\n"
            f"Выберите действие:",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 *Справка по командам:*\n\n"
        "🔹 `/start` - Главное меню\n"
        "🔹 `/help` - Эта справка\n"
        "🔹 `/status` - Статус системы\n\n"
        "💡 *Для админов:*\n"
        "🔹 `/admin` - Админ-панель\n"
        "🔹 `/export` - Экспорт данных\n"
        "🔹 `/backup` - Резервная копия"
    )
    
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands=['status'])
async def status_command(message: types.Message):
    """Обработчик команды /status"""
    try:
        # Получаем статистику
        total_users = await db.get_total_users()
        present_users = await db.get_present_users()
        absent_users = await db.get_absent_users()
        
        status_text = (
            "📊 *Статус системы:*\n\n"
            f"👥 Всего бойцов: {total_users}\n"
            f"✅ Присутствуют: {present_users}\n"
            f"❌ Отсутствуют: {absent_users}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}"
        )
        
        await message.answer(status_text, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        await message.answer("❌ Ошибка получения статуса системы")

@dp.message_handler(commands=['admin'])
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

@dp.errors_handler()
async def errors_handler(update, exception):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке {update}: {exception}")
    
    try:
        if update.message:
            await update.message.answer(
                "❌ Произошла ошибка при обработке запроса. Попробуйте позже."
            )
    except:
        pass

if __name__ == '__main__':
    try:
        logger.info("🚀 Запуск бота...")
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")