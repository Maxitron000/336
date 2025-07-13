#!/usr/bin/env python3
"""
Оптимизированная версия Telegram Bot для PythonAnywhere
Размер: < 500MB, без тяжелых зависимостей
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

# Облегченные локации
LOCATIONS = [
    "Поликлиника", "ОБРМП", "Калининград", "Магазин", "Столовая",
    "Госпиталь", "Рабочка", "ВВК", "МФЦ", "Патруль"
]

# === БАЗА ДАННЫХ ===
def init_db():
    """Инициализация базы данных"""
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
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("Зарегистрироваться", callback_data="register")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Добро пожаловать в систему учета персонала!\n\n"
        "Для начала работы необходимо зарегистрироваться.",
        reply_markup=reply_markup
    )

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регистрация пользователя"""
    if len(context.args) != 1:
        await update.message.reply_text(
            "Использование: /register Фамилия И.О.\n"
            "Пример: /register Иванов И.И."
        )
        return
    
    full_name = context.args[0]
    user_id = update.effective_user.id
    
    # Простая валидация
    if not full_name or len(full_name) < 5:
        await update.message.reply_text("Неверный формат ФИО!")
        return
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (user_id, full_name) VALUES (?, ?)",
            (user_id, full_name)
        )
        conn.commit()
        await update.message.reply_text(f"Регистрация завершена! Добро пожаловать, {full_name}")
    except sqlite3.IntegrityError:
        await update.message.reply_text("Вы уже зарегистрированы!")
    finally:
        conn.close()

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора локации"""
    location = update.message.text
    user_id = update.effective_user.id
    
    if location not in LOCATIONS:
        # Показываем клавиатуру с локациями
        keyboard = []
        for i in range(0, len(LOCATIONS), 2):
            row = []
            row.append(InlineKeyboardButton(LOCATIONS[i], callback_data=f"loc_{LOCATIONS[i]}"))
            if i + 1 < len(LOCATIONS):
                row.append(InlineKeyboardButton(LOCATIONS[i + 1], callback_data=f"loc_{LOCATIONS[i + 1]}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите локацию:", reply_markup=reply_markup)
        return
    
    # Проверяем регистрацию
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь: /register Фамилия И.О.")
        conn.close()
        return
    
    # Записываем прибытие
    cursor.execute(
        "INSERT INTO arrivals (user_id, location, status) VALUES (?, ?, ?)",
        (user_id, location, "Прибыл")
    )
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"Отмечено: {user[0]} - {location}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - показать статус пользователя"""
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
    
    if not results:
        await update.message.reply_text("Вы не зарегистрированы!")
        return
    
    text = f"Статус пользователя: {results[0][0]}\n\n"
    text += "Последние отметки:\n"
    
    for row in results:
        if row[1]:  # Если есть записи
            text += f"• {row[1]} - {row[2]} ({row[3][:16]})\n"
    
    await update.message.reply_text(text)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /admin - административная панель"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет прав администратора!")
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
    
    text = f"📊 Административная панель\n\n"
    text += f"👥 Всего пользователей: {total_users}\n"
    text += f"📅 Отметок сегодня: {today_arrivals}\n"
    text += f"📋 Всего отметок: {total_arrivals}\n"
    
    keyboard = [
        [InlineKeyboardButton("Экспорт CSV", callback_data="export_csv")],
        [InlineKeyboardButton("Очистить старые записи", callback_data="cleanup")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "register":
        await query.edit_message_text(
            "Для регистрации используйте команду:\n"
            "/register Фамилия И.О.\n\n"
            "Пример: /register Иванов И.И."
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            "Команды бота:\n"
            "/start - Начать работу\n"
            "/register - Регистрация\n"
            "/status - Мой статус\n"
            "/admin - Админ-панель\n\n"
            "Для отметки просто отправьте название локации"
        )
    
    elif query.data.startswith("loc_"):
        location = query.data[4:]  # Убираем "loc_"
        user_id = query.from_user.id
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            await query.edit_message_text("Сначала зарегистрируйтесь: /register Фамилия И.О.")
            conn.close()
            return
        
        cursor.execute(
            "INSERT INTO arrivals (user_id, location, status) VALUES (?, ?, ?)",
            (user_id, location, "Прибыл")
        )
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"✅ Отмечено: {user[0]} - {location}")
    
    elif query.data == "export_csv":
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("Нет прав!")
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
        
        await query.edit_message_text("📄 Экспорт готов!")
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=open('temp_export.csv', 'rb'),
            filename=f'personnel_export_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
        # Удаляем временный файл
        os.remove('temp_export.csv')
    
    elif query.data == "cleanup":
        if query.from_user.id not in ADMIN_IDS:
            await query.edit_message_text("Нет прав!")
            return
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM arrivals WHERE created_at < datetime('now', '-3 months')")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"🧹 Удалено записей: {deleted}")

# === УВЕДОМЛЕНИЯ ===
def send_daily_reminder():
    """Отправка ежедневного напоминания"""
    # Эта функция будет вызываться планировщиком
    pass

def schedule_notifications():
    """Планировщик уведомлений"""
    schedule.every().day.at("09:00").do(send_daily_reminder)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# === ОСНОВНАЯ ФУНКЦИЯ ===
async def main():
    """Основная функция"""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    
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
    
    logger.info("🚀 Бот запущен (PythonAnywhere версия)")
    print("🚀 Бот запущен и готов к работе на PythonAnywhere!")
    
    # Запускаем бота
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")