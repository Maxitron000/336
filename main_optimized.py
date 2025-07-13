#!/usr/bin/env python3
"""
🚀 Оптимизированная версия Telegram Bot для PythonAnywhere
📦 Размер: < 500MB, без тяжелых зависимостей
🎯 Система учета прибытия/убытия персонала
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
MAIN_ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else None  # Главный админ - первый в списке

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

# 👑 Права админов
ADMIN_PERMISSIONS = {
    'view_all_users': 'Просмотр всех пользователей',
    'manage_users': 'Управление пользователями', 
    'export_data': 'Экспорт данных',
    'cleanup_data': 'Очистка данных',
    'view_statistics': 'Просмотр статистики',
    'manage_locations': 'Управление локациями',
    'manage_admins': 'Управление админами',
    'system_settings': 'Системные настройки'
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
            admin_permissions TEXT DEFAULT '',
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

def is_admin(user_id):
    """🔍 Проверка прав администратора"""
    return user_id in ADMIN_IDS

def is_main_admin(user_id):
    """👑 Проверка главного администратора"""
    return user_id == MAIN_ADMIN_ID

def get_user_permissions(user_id):
    """📋 Получение прав пользователя"""
    if is_main_admin(user_id):
        return list(ADMIN_PERMISSIONS.keys())  # Все права
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute("SELECT admin_permissions FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return result[0].split(',')
    return []

def has_permission(user_id, permission):
    """✅ Проверка конкретного права"""
    if is_main_admin(user_id):
        return True
    return permission in get_user_permissions(user_id)

# === ОБРАБОТЧИКИ КОМАНД ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🚀 Команда /start"""
    user_id = update.effective_user.id
    
    # Проверяем регистрацию
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        # Первый запуск - просим ФИО
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 Добро пожаловать в систему учета персонала!\n\n"
            "📝 Введите ваше ФИО в формате:\n"
            "📋 Пример: Иванов И.И.\n\n"
            "✍️ Напишите ваше ФИО:",
            reply_markup=reply_markup
        )
        # Устанавливаем состояние ожидания ФИО
        context.user_data['waiting_for_name'] = True
        return
    
    # Пользователь зарегистрирован - показываем меню
    await show_main_menu(update, context, user[0])

async def show_main_menu(update, context, user_name):
    """🏠 Показать главное меню"""
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    
    if is_admin(user_id):
        # Меню для админов
        keyboard = [
            [InlineKeyboardButton("✅ Прибыл", callback_data="arrived")],
            [InlineKeyboardButton("❌ Убыл", callback_data="departed")],
            [InlineKeyboardButton("📋 Мой журнал", callback_data="my_journal")],
            [InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")]
        ]
    else:
        # Меню для обычных бойцов
        keyboard = [
            [InlineKeyboardButton("✅ Прибыл", callback_data="arrived")],
            [InlineKeyboardButton("❌ Убыл", callback_data="departed")],
            [InlineKeyboardButton("📋 Мой журнал", callback_data="my_journal")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎖️ {user_name}\n\n📍 Выберите действие:"
    
    if hasattr(update, 'message'):
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📝 Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Обработка регистрации ФИО
    if context.user_data.get('waiting_for_name'):
        # Валидация ФИО
        if len(text) < 5 or '.' not in text:
            keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Неверный формат ФИО!\n\n"
                "📋 Используйте формат: Иванов И.И.\n"
                "✍️ Попробуйте еще раз:",
                reply_markup=reply_markup
            )
            return
        
        # Сохраняем пользователя
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (user_id, full_name) VALUES (?, ?)",
                (user_id, text)
            )
            conn.commit()
            context.user_data['waiting_for_name'] = False
            
            await update.message.reply_text(
                f"✅ Регистрация завершена!\n"
                f"🎖️ Добро пожаловать, {text}!"
            )
            
            # Показываем главное меню
            await show_main_menu(update, context, text)
            
        except sqlite3.IntegrityError:
            await update.message.reply_text("❌ Такое ФИО уже зарегистрировано!")
        finally:
            conn.close()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔘 Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Получаем имя пользователя
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        await query.edit_message_text("❌ Сначала зарегистрируйтесь!")
        return
    
    user_name = user[0]
    
    if data == "cancel":
        await query.edit_message_text("❌ Операция отменена")
        return
    
    elif data == "arrived":
        await show_location_menu(query, context, "arrived", user_name)
    
    elif data == "departed":
        await show_location_menu(query, context, "departed", user_name)
    
    elif data == "my_journal":
        await show_my_journal(query, context, user_id, user_name)
    
    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Нет прав доступа!")
            return
        await show_admin_panel(query, context)
    
    elif data == "back_to_main":
        await show_main_menu(query, context, user_name)
    
    elif data.startswith("location_"):
        # Обработка выбора локации
        parts = data.split("_", 2)
        if len(parts) >= 3:
            action = parts[1]  # arrived или departed
            location = parts[2]
            await process_location_action(query, context, action, location, user_id, user_name)
    
    elif data.startswith("admin_"):
        # Обработка админских команд
        await handle_admin_commands(query, context, data, user_id)

async def show_location_menu(query, context, action, user_name):
    """📍 Показать меню выбора локации"""
    action_text = "прибытие" if action == "arrived" else "убытие"
    emoji = "✅" if action == "arrived" else "❌"
    
    keyboard = []
    locations_list = list(LOCATIONS.keys())
    
    # Создаем клавиатуру по 2 кнопки в ряд
    for i in range(0, len(locations_list), 2):
        row = []
        row.append(InlineKeyboardButton(
            locations_list[i], 
            callback_data=f"location_{action}_{LOCATIONS[locations_list[i]]}"
        ))
        if i + 1 < len(locations_list):
            row.append(InlineKeyboardButton(
                locations_list[i + 1], 
                callback_data=f"location_{action}_{LOCATIONS[locations_list[i + 1]]}"
            ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎖️ {user_name}\n\n"
        f"{emoji} Выберите локацию для отметки ({action_text}):",
        reply_markup=reply_markup
    )

async def process_location_action(query, context, action, location, user_id, user_name):
    """⚡ Обработка действия с локацией"""
    status = "✅ Прибыл" if action == "arrived" else "❌ Убыл"
    
    # Записываем в базу данных
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO arrivals (user_id, location, status) VALUES (?, ?, ?)",
        (user_id, location, status)
    )
    conn.commit()
    conn.close()
    
    # Показываем подтверждение
    keyboard = [
        [InlineKeyboardButton("✅ Еще отметка", callback_data="arrived" if action == "arrived" else "departed")],
        [InlineKeyboardButton("📋 Мой журнал", callback_data="my_journal")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Отмечено!\n\n"
        f"🎖️ {user_name}\n"
        f"📍 {location}\n"
        f"📊 {status}\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=reply_markup
    )

async def show_my_journal(query, context, user_id, user_name):
    """📋 Показать журнал пользователя"""
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT location, status, created_at
        FROM arrivals
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (user_id,))
    
    records = cursor.fetchall()
    conn.close()
    
    if not records:
        text = f"📋 Журнал: {user_name}\n\n❌ Нет записей"
    else:
        text = f"📋 Журнал: {user_name}\n\n"
        for location, status, created_at in records:
            date_str = datetime.fromisoformat(created_at).strftime('%d.%m %H:%M')
            text += f"• {location} - {status} ({date_str})\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def show_admin_panel(query, context):
    """👑 Показать админ-панель"""
    user_id = query.from_user.id
    
    keyboard = []
    
    # Основные функции для всех админов
    if has_permission(user_id, 'view_all_users'):
        keyboard.append([InlineKeyboardButton("👥 Личный состав", callback_data="admin_users")])
    
    if has_permission(user_id, 'view_statistics'):
        keyboard.append([InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")])
    
    if has_permission(user_id, 'export_data'):
        keyboard.append([InlineKeyboardButton("📄 Экспорт данных", callback_data="admin_export")])
    
    if has_permission(user_id, 'cleanup_data'):
        keyboard.append([InlineKeyboardButton("🧹 Очистка данных", callback_data="admin_cleanup")])
    
    # Функции только для главного админа
    if is_main_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Управление админами", callback_data="admin_manage_admins")])
    
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👑 Административная панель\n\n"
        "📋 Выберите действие:",
        reply_markup=reply_markup
    )

async def handle_admin_commands(query, context, data, user_id):
    """⚙️ Обработка админских команд"""
    if data == "admin_users":
        if not has_permission(user_id, 'view_all_users'):
            await query.edit_message_text("❌ Нет прав доступа!")
            return
        await show_users_list(query, context, user_id)
    
    elif data == "admin_stats":
        if not has_permission(user_id, 'view_statistics'):
            await query.edit_message_text("❌ Нет прав доступа!")
            return
        await show_statistics(query, context)
    
    elif data == "admin_export":
        if not has_permission(user_id, 'export_data'):
            await query.edit_message_text("❌ Нет прав доступа!")
            return
        await export_data(query, context)
    
    elif data == "admin_cleanup":
        if not has_permission(user_id, 'cleanup_data'):
            await query.edit_message_text("❌ Нет прав доступа!")
            return
        await cleanup_data(query, context)
    
    elif data == "admin_manage_admins":
        if not is_main_admin(user_id):
            await query.edit_message_text("❌ Только главный админ!")
            return
        await show_admin_management(query, context)
    
    elif data.startswith("make_admin_"):
        target_user_id = int(data.split("_")[2])
        await make_admin(query, context, target_user_id, user_id)
    
    elif data.startswith("remove_admin_"):
        target_user_id = int(data.split("_")[2])
        await remove_admin(query, context, target_user_id, user_id)

async def show_users_list(query, context, admin_user_id):
    """👥 Показать список пользователей"""
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, full_name, is_admin
        FROM users
        ORDER BY full_name
    """)
    
    users = cursor.fetchall()
    conn.close()
    
    text = "👥 Личный состав:\n\n"
    keyboard = []
    
    for user_id, full_name, is_admin_flag in users:
        admin_mark = " 👑" if is_admin_flag else ""
        text += f"• {full_name}{admin_mark}\n"
        text += f"  📱 ID: `{user_id}`\n\n"
        
        # Кнопки для главного админа
        if is_main_admin(admin_user_id) and user_id != admin_user_id:
            if is_admin_flag:
                keyboard.append([InlineKeyboardButton(
                    f"❌ Снять с админа: {full_name}", 
                    callback_data=f"remove_admin_{user_id}"
                )])
            else:
                keyboard.append([InlineKeyboardButton(
                    f"👑 Назначить админом: {full_name}", 
                    callback_data=f"make_admin_{user_id}"
                )])
    
    keyboard.append([InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def make_admin(query, context, target_user_id, admin_user_id):
    """👑 Назначить админом"""
    if not is_main_admin(admin_user_id):
        await query.answer("❌ Только главный админ!")
        return
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # Получаем имя пользователя
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (target_user_id,))
    user = cursor.fetchone()
    
    if not user:
        await query.answer("❌ Пользователь не найден!")
        return
    
    # Назначаем админом
    cursor.execute(
        "UPDATE users SET is_admin = 1 WHERE user_id = ?", 
        (target_user_id,)
    )
    conn.commit()
    conn.close()
    
    # Добавляем в глобальный список админов
    if target_user_id not in ADMIN_IDS:
        ADMIN_IDS.append(target_user_id)
    
    await query.answer(f"✅ {user[0]} назначен админом!")
    await show_users_list(query, context, admin_user_id)

async def remove_admin(query, context, target_user_id, admin_user_id):
    """❌ Снять с админа"""
    if not is_main_admin(admin_user_id):
        await query.answer("❌ Только главный админ!")
        return
    
    if target_user_id == admin_user_id:
        await query.answer("❌ Нельзя снять себя с админа!")
        return
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # Получаем имя пользователя
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (target_user_id,))
    user = cursor.fetchone()
    
    if not user:
        await query.answer("❌ Пользователь не найден!")
        return
    
    # Снимаем с админа
    cursor.execute(
        "UPDATE users SET is_admin = 0, admin_permissions = '' WHERE user_id = ?", 
        (target_user_id,)
    )
    conn.commit()
    conn.close()
    
    # Убираем из глобального списка админов
    if target_user_id in ADMIN_IDS:
        ADMIN_IDS.remove(target_user_id)
    
    await query.answer(f"❌ {user[0]} снят с админа!")
    await show_users_list(query, context, admin_user_id)

async def show_statistics(query, context):
    """📊 Показать статистику"""
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM arrivals WHERE DATE(created_at) = DATE('now')")
    today_arrivals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM arrivals")
    total_arrivals = cursor.fetchone()[0]
    
    # Статистика по локациям за сегодня
    cursor.execute("""
        SELECT location, COUNT(*) 
        FROM arrivals 
        WHERE DATE(created_at) = DATE('now') 
        GROUP BY location 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    top_locations = cursor.fetchall()
    
    conn.close()
    
    text = f"📊 Статистика системы\n\n"
    text += f"👥 Всего пользователей: {total_users}\n"
    text += f"📅 Отметок сегодня: {today_arrivals}\n"
    text += f"📋 Всего отметок: {total_arrivals}\n\n"
    
    if top_locations:
        text += f"🏆 Топ локации сегодня:\n"
        for location, count in top_locations:
            text += f"• {location}: {count} отметок\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def export_data(query, context):
    """📄 Экспорт данных"""
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
    filename = f'personnel_export_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    await query.edit_message_text("📄 Экспорт готов! Файл будет отправлен...")
    
    await context.bot.send_document(
        chat_id=query.message.chat_id,
        document=open(filename, 'rb'),
        filename=filename,
        caption="📊 Экспорт данных персонала"
    )
    
    # Удаляем временный файл
    os.remove(filename)
    
    keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="✅ Экспорт завершен!",
        reply_markup=reply_markup
    )

async def cleanup_data(query, context):
    """🧹 Очистка данных"""
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM arrivals WHERE created_at < datetime('now', '-3 months')")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🧹 Очистка завершена!\n\n"
        f"🗑️ Удалено записей: {deleted}",
        reply_markup=reply_markup
    )

async def show_admin_management(query, context):
    """⚙️ Управление админами и правами"""
    text = "⚙️ Управление админами\n\n"
    text += "🚧 Функция в разработке...\n"
    text += "Здесь будут чекбоксы для настройки прав"
    
    keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

# === УВЕДОМЛЕНИЯ ===
def send_daily_reminder():
    """📢 Отправка ежедневного напоминания"""
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
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=schedule_notifications, daemon=True)
    scheduler_thread.start()
    
    logger.info("🚀 Бот запущен (оптимизированная версия)")
    print("🚀 Бот запущен и готов к работе! 🎉")
    
    # Запускаем бота
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")