#!/usr/bin/env python3
"""
🚀 Оптимизированная версия Telegram Bot для PythonAnywhere
📦 Размер: < 500MB, без тяжелых зависимостей
🎯 Все функции + максимум эмодзи + только inline кнопки
"""

import logging
import asyncio
import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import schedule
import time
import threading

# Загружаем переменные окружения
load_dotenv()

# Настройка облегченного логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]

# 📍 Локации с эмодзи
LOCATIONS = {
    "🏥 Поликлиника": "Поликлиника",
    "⚓ ОБРМП": "ОБРМП", 
    "🌆 Калининград": "Калининград",
    "🛒 Магазин": "Магазин",
    "🍲 Столовая": "Столовая",
    "🏨 Госпиталь": "Госпиталь",
    "⚙️ Рабочка": "Рабочка",
    "🩺 ВВК": "ВВК",
    "🏛️ МФЦ": "МФЦ",
    "🚔 Патруль": "Патруль"
}

# === БАЗА ДАННЫХ ===
def init_db():
    """🔧 Инициализация базы данных"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # Создаем таблицы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT UNIQUE NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arrivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            location TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Оптимизация для PythonAnywhere
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    
    # Автоочистка старых записей (6 месяцев)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS cleanup_old_records
        AFTER INSERT ON arrivals
        BEGIN
            DELETE FROM arrivals 
            WHERE created_at < datetime('now', '-6 months');
        END;
    """)
    
    conn.commit()
    conn.close()

# === ОБРАБОТЧИКИ КОМАНД ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🚀 Команда /start"""
    keyboard = [
        [InlineKeyboardButton("👤 Зарегистрироваться", callback_data="register")],
        [InlineKeyboardButton("📍 Выбрать локацию", callback_data="choose_location")],
        [InlineKeyboardButton("📊 Мой статус", callback_data="my_status")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎉 Добро пожаловать в систему учета персонала!\n\n"
        "👋 Для начала работы выберите действие:",
        reply_markup=reply_markup
    )

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 Регистрация пользователя"""
    if len(context.args) != 1:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 Использование: /register Фамилия И.О.\n"
            "📋 Пример: /register Иванов И.И.",
            reply_markup=reply_markup
        )
        return
    
    full_name = context.args[0]
    user_id = update.effective_user.id
    
    # Простая валидация
    if not full_name or len(full_name) < 5:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Неверный формат ФИО!",
            reply_markup=reply_markup
        )
        return
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (user_id, full_name) VALUES (?, ?)",
            (user_id, full_name)
        )
        conn.commit()
        
        keyboard = [
            [InlineKeyboardButton("📍 Выбрать локацию", callback_data="choose_location")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Регистрация завершена! Добро пожаловать, {full_name}! 🎉",
            reply_markup=reply_markup
        )
    except sqlite3.IntegrityError:
        keyboard = [[InlineKeyboardButton("📍 Выбрать локацию", callback_data="choose_location")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "ℹ️ Вы уже зарегистрированы!",
            reply_markup=reply_markup
        )
    finally:
        conn.close()

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📍 Обработка выбора локации"""
    location = update.message.text
    user_id = update.effective_user.id
    
    # Проверяем, есть ли такая локация
    location_found = None
    for loc_emoji, loc_name in LOCATIONS.items():
        if location == loc_name or location == loc_emoji:
            location_found = loc_name
            break
    
    if not location_found:
        keyboard = []
        locations_list = list(LOCATIONS.keys())
        
        # Создаем клавиатуру по 2 кнопки в ряд
        for i in range(0, len(locations_list), 2):
            row = []
            row.append(InlineKeyboardButton(locations_list[i], callback_data=f"loc_{LOCATIONS[locations_list[i]]}"))
            if i + 1 < len(locations_list):
                row.append(InlineKeyboardButton(locations_list[i + 1], callback_data=f"loc_{LOCATIONS[locations_list[i + 1]]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📍 Выберите локацию:",
            reply_markup=reply_markup
        )
        return
    
    # Проверяем регистрацию
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        keyboard = [[InlineKeyboardButton("👤 Зарегистрироваться", callback_data="register")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Сначала зарегистрируйтесь!",
            reply_markup=reply_markup
        )
        conn.close()
        return
    
    # Записываем прибытие
    cursor.execute(
        "INSERT INTO arrivals (user_id, location, status) VALUES (?, ?, ?)",
        (user_id, location_found, "✅ Прибыл")
    )
    conn.commit()
    conn.close()
    
    keyboard = [
        [InlineKeyboardButton("📍 Другая локация", callback_data="choose_location")],
        [InlineKeyboardButton("📊 Мой статус", callback_data="my_status")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Отмечено: {user[0]} - {location_found} 🎯",
        reply_markup=reply_markup
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Команда /status - показать статус пользователя"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.full_name, a.location, a.status, a.created_at
        FROM users u
        LEFT JOIN arrivals a ON u.user_id = a.user_id
        WHERE u.user_id = ?
        ORDER BY a.created_at DESC
        LIMIT 5
    """, (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    keyboard = [
        [InlineKeyboardButton("📍 Выбрать локацию", callback_data="choose_location")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not results:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы!",
            reply_markup=reply_markup
        )
        return
    
    text = f"📊 Статус пользователя: {results[0][0]} 👤\n\n"
    text += "📝 Последние отметки:\n"
    
    for row in results:
        if row[1]:  # Если есть записи
            text += f"• {row[1]} - {row[2]} ({row[3][:16]}) 📅\n"
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👑 Команда /admin - административная панель"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ У вас нет прав администратора! 🚫",
            reply_markup=reply_markup
        )
        return
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # Статистика
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM arrivals WHERE DATE(created_at) = DATE('now')")
    today_arrivals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM arrivals")
    total_arrivals = cursor.fetchone()[0]
    
    conn.close()
    
    text = f"� Административная панель 🛠️\n\n"
    text += f"👥 Всего пользователей: {total_users}\n"
    text += f"📅 Отметок сегодня: {today_arrivals}\n"
    text += f"📋 Всего отметок: {total_arrivals}\n"
    
    keyboard = [
        [InlineKeyboardButton("📊 Детальная статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📄 Экспорт CSV", callback_data="export_csv")],
        [InlineKeyboardButton("🧹 Очистить старые записи", callback_data="cleanup")],
        [InlineKeyboardButton("👥 Список пользователей", callback_data="user_list")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔘 Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start":
        keyboard = [
            [InlineKeyboardButton("👤 Зарегистрироваться", callback_data="register")],
            [InlineKeyboardButton("📍 Выбрать локацию", callback_data="choose_location")],
            [InlineKeyboardButton("📊 Мой статус", callback_data="my_status")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎉 Добро пожаловать в систему учета персонала!\n\n"
            "👋 Для начала работы выберите действие:",
            reply_markup=reply_markup
        )
    
    elif query.data == "register":
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📝 Для регистрации используйте команду:\n"
            "/register Фамилия И.О.\n\n"
            "📋 Пример: /register Иванов И.И.",
            reply_markup=reply_markup
        )
    
    elif query.data == "help":
        keyboard = [
            [InlineKeyboardButton("📍 Выбрать локацию", callback_data="choose_location")],
            [InlineKeyboardButton("📊 Мой статус", callback_data="my_status")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❓ Команды бота:\n"
            "🚀 /start - Начать работу\n"
            "👤 /register - Регистрация\n"
            "📊 /status - Мой статус\n"
            "👑 /admin - Админ-панель\n\n"
            "📍 Для отметки выберите локацию из меню",
            reply_markup=reply_markup
        )
    
    elif query.data == "choose_location":
        keyboard = []
        locations_list = list(LOCATIONS.keys())
        
        # Создаем клавиатуру по 2 кнопки в ряд
        for i in range(0, len(locations_list), 2):
            row = []
            row.append(InlineKeyboardButton(locations_list[i], callback_data=f"loc_{LOCATIONS[locations_list[i]]}"))
            if i + 1 < len(locations_list):
                row.append(InlineKeyboardButton(locations_list[i + 1], callback_data=f"loc_{LOCATIONS[locations_list[i + 1]]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📍 Выберите локацию:",
            reply_markup=reply_markup
        )
    
    elif query.data == "my_status":
        user_id = query.from_user.id
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.full_name, a.location, a.status, a.created_at
            FROM users u
            LEFT JOIN arrivals a ON u.user_id = a.user_id
            WHERE u.user_id = ?
            ORDER BY a.created_at DESC
            LIMIT 5
        """, (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        keyboard = [
            [InlineKeyboardButton("📍 Выбрать локацию", callback_data="choose_location")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if not results:
            await query.edit_message_text(
                "❌ Вы не зарегистрированы!",
                reply_markup=reply_markup
            )
            return
        
        text = f"📊 Статус пользователя: {results[0][0]} 👤\n\n"
        text += "📝 Последние отметки:\n"
        
        for row in results:
            if row[1]:  # Если есть записи
                text += f"• {row[1]} - {row[2]} ({row[3][:16]}) 📅\n"
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data.startswith("loc_"):
        location = query.data[4:]  # Убираем "loc_"
        user_id = query.from_user.id
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            keyboard = [[InlineKeyboardButton("👤 Зарегистрироваться", callback_data="register")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ Сначала зарегистрируйтесь!",
                reply_markup=reply_markup
            )
            conn.close()
            return
        
        cursor.execute(
            "INSERT INTO arrivals (user_id, location, status) VALUES (?, ?, ?)",
            (user_id, location, "✅ Прибыл")
        )
        conn.commit()
        conn.close()
        
        keyboard = [
            [InlineKeyboardButton("📍 Другая локация", callback_data="choose_location")],
            [InlineKeyboardButton("📊 Мой статус", callback_data="my_status")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ Отмечено: {user[0]} - {location} 🎯",
            reply_markup=reply_markup
        )
    
    elif query.data == "admin_stats":
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ Нет прав! 🚫")
            return
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        # Детальная статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM arrivals WHERE DATE(created_at) = DATE('now')")
        today_arrivals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM arrivals WHERE DATE(created_at) = DATE('now', '-1 day')")
        yesterday_arrivals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM arrivals WHERE DATE(created_at) >= DATE('now', '-7 days')")
        week_arrivals = cursor.fetchone()[0]
        
        cursor.execute("SELECT location, COUNT(*) FROM arrivals WHERE DATE(created_at) = DATE('now') GROUP BY location ORDER BY COUNT(*) DESC LIMIT 5")
        top_locations = cursor.fetchall()
        
        conn.close()
        
        text = f"📊 Детальная статистика 📈\n\n"
        text += f"👥 Всего пользователей: {total_users}\n"
        text += f"📅 Отметок сегодня: {today_arrivals}\n"
        text += f"📅 Отметок вчера: {yesterday_arrivals}\n"
        text += f"📈 За неделю: {week_arrivals}\n\n"
        text += f"🏆 Топ локации сегодня:\n"
        
        for loc, count in top_locations:
            text += f"• {loc}: {count} отметок\n"
        
        keyboard = [
            [InlineKeyboardButton("👑 Админ-панель", callback_data="admin")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "user_list":
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ Нет прав! 🚫")
            return
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.full_name, COUNT(a.id) as arrivals_count, MAX(a.created_at) as last_arrival
            FROM users u
            LEFT JOIN arrivals a ON u.user_id = a.user_id
            GROUP BY u.user_id, u.full_name
            ORDER BY arrivals_count DESC
            LIMIT 10
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        text = f"👥 Список пользователей (топ 10) 📋\n\n"
        
        for i, (name, count, last) in enumerate(users, 1):
            last_str = last[:16] if last else "Нет отметок"
            text += f"{i}. {name} - {count} отметок (последняя: {last_str})\n"
        
        keyboard = [
            [InlineKeyboardButton("👑 Админ-панель", callback_data="admin")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "export_csv":
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ Нет прав! 🚫")
            return
        
        # Простой экспорт
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.full_name, a.location, a.status, a.created_at
            FROM arrivals a
            JOIN users u ON a.user_id = u.user_id
            ORDER BY a.created_at DESC
            LIMIT 1000
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        # Создаем CSV
        csv_content = "ФИО,Локация,Статус,Дата\n"
        for row in results:
            csv_content += f"{row[0]},{row[1]},{row[2]},{row[3]}\n"
        
        # Сохраняем во временный файл
        with open('temp_export.csv', 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        keyboard = [
            [InlineKeyboardButton("👑 Админ-панель", callback_data="admin")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📄 Экспорт готов! Файл будет отправлен... 📤",
            reply_markup=reply_markup
        )
        
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=open('temp_export.csv', 'rb'),
            filename=f'personnel_export_{datetime.now().strftime("%Y%m%d")}.csv',
            caption="📊 Экспорт данных персонала 📋"
        )
        
        # Удаляем временный файл
        os.remove('temp_export.csv')
    
    elif query.data == "cleanup":
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ Нет прав! 🚫")
            return
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM arrivals WHERE created_at < datetime('now', '-3 months')")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        keyboard = [
            [InlineKeyboardButton("👑 Админ-панель", callback_data="admin")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🧹 Очистка завершена! Удалено записей: {deleted} 🗑️",
            reply_markup=reply_markup
        )
    
    elif query.data == "admin":
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ Нет прав! 🚫")
            return
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        # Статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM arrivals WHERE DATE(created_at) = DATE('now')")
        today_arrivals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM arrivals")
        total_arrivals = cursor.fetchone()[0]
        
        conn.close()
        
        text = f"👑 Административная панель 🛠️\n\n"
        text += f"👥 Всего пользователей: {total_users}\n"
        text += f"📅 Отметок сегодня: {today_arrivals}\n"
        text += f"📋 Всего отметок: {total_arrivals}\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Детальная статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("📄 Экспорт CSV", callback_data="export_csv")],
            [InlineKeyboardButton("🧹 Очистить старые записи", callback_data="cleanup")],
            [InlineKeyboardButton("👥 Список пользователей", callback_data="user_list")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

# === УВЕДОМЛЕНИЯ ===
def send_daily_reminder():
    """📢 Отправка ежедневного напоминания"""
    # Эта функция будет вызываться планировщиком
    pass

def schedule_notifications():
    """⏰ Планировщик уведомлений"""
    schedule.every().day.at("09:00").do(send_daily_reminder)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# === ОСНОВНАЯ ФУНКЦИЯ ===
async def main():
    """🚀 Основная функция"""
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден в переменных окружения")
    
    # Инициализируем базу данных
    init_db()
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("register", register_user))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, location_handler))
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=schedule_notifications, daemon=True)
    scheduler_thread.start()
    
    logger.info("🚀 Бот запущен (оптимизированная версия)")
    print("🚀 Бот запущен и готов к работе на PythonAnywhere! 🎉")
    
    # Запускаем бота
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")