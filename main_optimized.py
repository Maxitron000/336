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

# 📍 Локации с эмодзи (военная тематика)
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
    "🚔 Патруль": "Патруль",
    "📝 Другое": "Другое"
}

# 🟢 Логика "в расположении":
# - По умолчанию все в части (нет записей = в расположении)
# - Статус "Прибыл" = в расположении
# - Статус "Убыл" = не в расположении

# 💬 Шуточные уведомления для не отметившихся (50 фраз)
FUNNY_REMINDERS = [
    "Бро, где ты? 🤔 Отметься, а то думаем ты в плену! 😄",
    "Товарищ, связь потеряна! 📡 Дай сигнал о своем местонахождении! 🚨",
    "Эй, боец! 🪖 Система показывает, что ты где-то в поле! Отметься! 📍",
    "Братан, ты случайно не заблудился? 🧭 Нажми кнопку 'Прибыл'! ✅",
    "Товарищ майор интересуется твоим местоположением! 🎖️ Отметься срочно! ⚡",
    "Бро, ты же обещал вернуться! 🤝 Где отметка о прибытии? 📋",
    "Эй, странник! 🚶‍♂️ Пора домой, отметься в системе! 🏠",
    "Товарищ, ты не на секретном задании? 🕵️ Тогда отметься! 📝",
    "Бро, GPS тебя потерял! 🛰️ Помоги системе найти тебя! 🔍",
    "Эй, призрак! 👻 Материализуйся и отметься! ✨",
    "Товарищ, ты в другом измерении? 🌌 Вернись и отметься! 🌍",
    "Бро, связь прервана! 📞 Восстанови контакт - отметься! 🔗",
    "Эй, партизан! 🌲 Выходи из леса и отметься! 🌳",
    "Товарищ, ты случайно не в отпуске? 🏖️ Если нет - отметься! 📅",
    "Бро, система глючит или ты пропал? 🤖 Отметься для проверки! ✔️",
    "Эй, невидимка! 🫥 Стань видимым - отметься! 👁️",
    "Товарищ, ты не застрял в лифте? 🛗 Отметься, если выбрался! 🚪",
    "Бро, ты забыл пароль от кнопки? 🔐 Напомню: просто нажми! 👆",
    "Эй, путешественник! 🗺️ Закончи путешествие - отметься! 🎯",
    "Товарищ, ты изучаешь город? 🏙️ Изучил - отметься! 📖",
    "Бро, ты не заснул где-то? 😴 Проснись и отметься! ⏰",
    "Эй, исследователь! 🔬 Завершай исследование - отметься! 🧪",
    "Товарищ, ты в командировке? 💼 Если вернулся - отметься! ✈️",
    "Бро, ты не стал туристом? 📷 Хватит фотографировать - отметься! 🎭",
    "Эй, философ! 🤔 Закончи размышления - отметься! 💭",
    "Товарищ, ты медитируешь? 🧘‍♂️ Просветлись - отметься! 🌟",
    "Бро, ты играешь в прятки? 🙈 Игра окончена - отметься! 🎮",
    "Эй, детектив! 🕵️ Дело раскрыто - отметься! 🔍",
    "Товарищ, ты пишешь мемуары? 📝 Глава закончена - отметься! 📚",
    "Бро, ты на диете? 🥗 Покушал - отметься! 🍽️",
    "Эй, спортсмен! 🏃‍♂️ Пробежка закончена - отметься! 🏁",
    "Товарищ, ты занимаешься йогой? 🧘 Намасте - отметься! 🙏",
    "Бро, ты стал шопоголиком? 🛍️ Покупки сделаны - отметься! 💳",
    "Эй, гурман! 👨‍🍳 Дегустация окончена - отметься! 🍴",
    "Товарищ, ты изучаешь архитектуру? 🏛️ Достаточно - отметься! 📐",
    "Бро, ты стал фотографом? 📸 Фотосессия окончена - отметься! 🎬",
    "Эй, метеоролог! 🌤️ Погоду изучил - отметься! 🌡️",
    "Товарищ, ты читаешь книгу? 📖 Страница перевернута - отметься! 📄",
    "Бро, ты стал художником? 🎨 Шедевр создан - отметься! 🖼️",
    "Эй, музыкант! 🎵 Концерт окончен - отметься! 🎪",
    "Товарищ, ты танцуешь? 💃 Танец закончен - отметься! 🕺",
    "Бро, ты стал актером? 🎭 Спектакль окончен - отметься! 🎪",
    "Эй, ученый! 👨‍🔬 Эксперимент завершен - отметься! ⚗️",
    "Товарищ, ты изобретаешь? 💡 Изобретение готово - отметься! 🔧",
    "Бро, ты стал поваром? 👨‍🍳 Блюдо готово - отметься! 🍳",
    "Эй, садовник! 🌱 Цветы политы - отметься! 🌺",
    "Товарищ, ты рыбачишь? 🎣 Улов хороший - отметься! 🐟",
    "Бро, ты стал пилотом? ✈️ Посадка выполнена - отметься! 🛬",
    "Эй, космонавт! 🚀 Миссия выполнена - отметься! 🛸",
    "Товарищ, напоминаю: нажать кнопку проще, чем объяснять где был! 😅"
]

# 👑 Права админов
ADMIN_PERMISSIONS = {
    'view_all_users': 'Просмотр всех пользователей',
    'manage_users': 'Управление пользователями', 
    'export_data': 'Экспорт данных',
    'cleanup_data': 'Очистка данных',
    'view_statistics': 'Просмотр статистики',
    'manage_locations': 'Управление локациями',
    'manage_admins': 'Управление админами',
    'system_settings': 'Системные настройки',
    'notification_settings': 'Настройки уведомлений'
}

# ⚙️ Настройки уведомлений
NOTIFICATION_SETTINGS = {
    'summary_time': '19:00',  # Время сводки админам
    'reminder_time': '20:30',  # Время напоминания не отметившимся
    'summary_enabled': True,
    'reminder_enabled': True,
    'admin_summary': True,
    'funny_reminders': True
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
            custom_location TEXT,
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
            "📋 Фамилия И.О. (инициалы через точку)\n\n"
            "✅ Правильные примеры:\n"
            "• Иванов И.И.\n"
            "• Петров П.П.\n"
            "• Сидоров С.С.\n"
            "• Козлов К.К.\n\n"
            "❌ Неправильные примеры:\n"
            "• Иванов Иван (без инициалов)\n"
            "• И.И. Иванов (неправильный порядок)\n"
            "• иванов и.и. (строчные буквы)\n"
            "• Иванов И И (без точек)\n\n"
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
                "📋 Правильный формат: Фамилия И.О.\n\n"
                "✅ Требования:\n"
                "• Фамилия с заглавной буквы\n"
                "• Инициалы через точку (И.О.)\n"
                "• Минимум 5 символов\n"
                "• Хотя бы одна точка\n\n"
                "✅ Правильные примеры:\n"
                "• Иванов И.И.\n"
                "• Петров П.П.\n"
                "• Сидоров С.С.\n\n"
                "❌ Ваш ввод не соответствует формату\n"
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
                f"🎖️ Добро пожаловать, {text}!\n\n"
                f"📋 Теперь вы можете:\n"
                f"• ✅ Отмечать прибытие\n"
                f"• ❌ Отмечать убытие\n"
                f"• 📋 Просматривать свой журнал\n\n"
                f"🔄 Система автоматически покажет главное меню..."
            )
            
            # Показываем главное меню
            await show_main_menu(update, context, text)
            
        except sqlite3.IntegrityError:
            await update.message.reply_text("❌ Такое ФИО уже зарегистрировано!")
        finally:
            conn.close()
            
    # Обработка ввода пользовательской локации
    if context.user_data.get('waiting_for_custom_location'):
        action = context.user_data.get('custom_location_action')
        user_name = context.user_data.get('user_name')
        
        # Валидация введенного текста
        if len(text.strip()) < 2:
            await update.message.reply_text(
                "❌ Слишком короткое название!\n\n"
                "📝 Введите местоположение (минимум 2 символа):"
            )
            return
            
        if len(text.strip()) > 50:
            await update.message.reply_text(
                "❌ Слишком длинное название!\n\n"
                "📝 Введите местоположение (максимум 50 символов):"
            )
            return
        
        # Сохраняем отметку с пользовательской локацией
        custom_location = text.strip()
        
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO arrivals (user_id, location, custom_location, status) VALUES (?, ?, ?, ?)",
                (user_id, "Другое", custom_location, action)
            )
            conn.commit()
            
            # Очищаем состояние
            context.user_data['waiting_for_custom_location'] = False
            context.user_data['custom_location_action'] = None
            context.user_data['user_name'] = None
            
            # Подтверждение
            status_emoji = "✅" if action == "arrived" else "❌"
            status_text = "прибыл" if action == "arrived" else "убыл"
            
            keyboard = [
                [InlineKeyboardButton("📍 Сделать еще отметку", callback_data="main_menu")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Отметка сохранена!\n\n"
                f"🎖️ {user_name}\n"
                f"{status_emoji} {status_text.capitalize()}: {custom_location}\n"
                f"🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
                f"📋 Выберите действие:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка сохранения: {str(e)}")
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
        # Очищаем все состояния ожидания
        context.user_data.clear()
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
    
    elif data == "toggle_summary":
        NOTIFICATION_SETTINGS['summary_enabled'] = not NOTIFICATION_SETTINGS['summary_enabled']
        await show_notification_settings(query, context)
    
    elif data == "toggle_reminders":
        NOTIFICATION_SETTINGS['reminder_enabled'] = not NOTIFICATION_SETTINGS['reminder_enabled']
        await show_notification_settings(query, context)
    
    elif data == "main_menu":
        await show_main_menu(query, context, user_name)

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
    
    # Если выбрана локация "Другое", запрашиваем ввод
    if location == "Другое":
        # Сохраняем состояние для обработки в text_handler
        context.user_data['waiting_for_custom_location'] = True
        context.user_data['custom_location_action'] = action
        context.user_data['user_name'] = user_name
        
        action_text = "прибытия" if action == "arrived" else "убытия"
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📝 Введите место {action_text}:\n\n"
            f"🎖️ {user_name}\n\n"
            f"💡 Примеры:\n"
            f"• Дом\n"
            f"• Спортзал\n"
            f"• Учебка\n"
            f"• Командировка\n"
            f"• Отпуск\n\n"
            f"📝 Напишите ваше местоположение (2-50 символов):",
            reply_markup=reply_markup
        )
        return
    
    # Обычная обработка для стандартных локаций
    status = "✅ Прибыл" if action == "arrived" else "❌ Убыл"
    
    # Записываем в базу данных
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO arrivals (user_id, location, custom_location, status) VALUES (?, ?, ?, ?)",
        (user_id, location, None, status)
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
        SELECT location, custom_location, status, created_at
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
        for location, custom_location, status, created_at in records:
            display_location = custom_location if custom_location else location
            date_str = datetime.fromisoformat(created_at).strftime('%d.%m %H:%M')
            text += f"• {display_location} - {status} ({date_str})\n"
    
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
    
    if has_permission(user_id, 'notification_settings'):
        keyboard.append([InlineKeyboardButton("🔔 Настройки уведомлений", callback_data="admin_notifications")])
    
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
    
    elif data == "admin_notifications":
        if not has_permission(user_id, 'notification_settings'):
            await query.edit_message_text("❌ Нет прав доступа!")
            return
        await show_notification_settings(query, context)
    
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
        SELECT 
            CASE 
                WHEN custom_location IS NOT NULL THEN custom_location
                ELSE location 
            END as display_location,
            COUNT(*) 
        FROM arrivals 
        WHERE DATE(created_at) = DATE('now') 
        GROUP BY display_location 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    top_locations = cursor.fetchall()
    
    # Статистика по статусам
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM arrivals 
        WHERE DATE(created_at) = DATE('now') 
        GROUP BY status
    """)
    status_stats = cursor.fetchall()
    
    conn.close()
    
    text = f"📊 Статистика системы\n\n"
    text += f"👥 Всего пользователей: {total_users}\n"
    text += f"📅 Отметок сегодня: {today_arrivals}\n"
    text += f"📋 Всего отметок: {total_arrivals}\n\n"
    
    if status_stats:
        text += f"📈 Статистика за сегодня:\n"
        for status, count in status_stats:
            text += f"• {status}: {count} отметок\n"
        text += "\n"
    
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

async def show_notification_settings(query, context):
    """🔔 Показать настройки уведомлений"""
    summary_status = "✅ Включены" if NOTIFICATION_SETTINGS['summary_enabled'] else "❌ Отключены"
    reminder_status = "✅ Включены" if NOTIFICATION_SETTINGS['reminder_enabled'] else "❌ Отключены"
    
    keyboard = [
        [InlineKeyboardButton(f"📊 Сводка админам: {summary_status}", callback_data="toggle_summary")],
        [InlineKeyboardButton(f"💬 Напоминания: {reminder_status}", callback_data="toggle_reminders")],
        [InlineKeyboardButton("🕐 Время сводки", callback_data="set_summary_time")],
        [InlineKeyboardButton("🕕 Время напоминаний", callback_data="set_reminder_time")],
        [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔔 НАСТРОЙКИ УВЕДОМЛЕНИЙ\n\n"
        f"📊 Сводка админам: {summary_status}\n"
        f"🕐 Время сводки: {NOTIFICATION_SETTINGS['summary_time']}\n\n"
        f"💬 Напоминания: {reminder_status}\n"
        f"🕕 Время напоминаний: {NOTIFICATION_SETTINGS['reminder_time']}\n\n"
        f"📋 Описание:\n"
        f"• Сводка - отчет о местонахождении всех\n"
        f"• Напоминания - только не отметившимся о возвращении\n"
        f"• Всего смешных фраз: {len(FUNNY_REMINDERS)}"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)

# === УВЕДОМЛЕНИЯ ===
async def send_admin_summary(application):
    """📊 Отправка сводки админам в 19:00"""
    if not NOTIFICATION_SETTINGS['summary_enabled']:
        return
        
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # Получаем последнюю отметку каждого пользователя
    cursor.execute("""
        SELECT u.user_id, u.full_name, a.location, a.custom_location, a.status, a.created_at
        FROM users u
        LEFT JOIN arrivals a ON u.user_id = a.user_id
        WHERE a.created_at = (
            SELECT MAX(created_at) FROM arrivals WHERE user_id = u.user_id
        ) OR a.created_at IS NULL
        ORDER BY u.full_name
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    # Разделяем на группы
    in_base = []
    away = []
    
    for user_id, name, location, custom_location, status, created_at in results:
        if not location:  # Нет записей - по умолчанию в части
            in_base.append(f"• {name}")
        else:
            display_location = custom_location if custom_location else location
            
            if status == "✅ Прибыл":
                # Прибыл = в расположении (независимо от локации)
                in_base.append(f"• {name}")
            else:  # Убыл = не в расположении
                away.append(f"• {name} → {display_location}")
    
    # Формируем сводку
    summary = f"📊 СВОДКА ЛИЧНОГО СОСТАВА\n🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
    
    if in_base:
        summary += f"🟢 В РАСПОЛОЖЕНИИ ({len(in_base)}):\n" + "\n".join(in_base) + "\n\n"
    
    if away:
        summary += f"🔴 НЕ В РАСПОЛОЖЕНИИ ({len(away)}):\n" + "\n".join(away) + "\n\n"
    
    summary += f"📋 Всего личного состава: {len(results)}"
    
    # Отправляем всем админам
    for admin_id in ADMIN_IDS:
        try:
            await application.bot.send_message(
                chat_id=admin_id,
                text=summary,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сводки админу {admin_id}: {e}")

async def send_return_reminders(application):
    """💬 Отправка напоминаний не вернувшимся в 20:30"""
    if not NOTIFICATION_SETTINGS['reminder_enabled']:
        return
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # Находим пользователей, которые убыли но не отметились о возвращении
    cursor.execute("""
        SELECT u.user_id, u.full_name, a.location, a.custom_location, a.created_at
        FROM users u
        JOIN arrivals a ON u.user_id = a.user_id
        WHERE a.created_at = (
            SELECT MAX(created_at) FROM arrivals WHERE user_id = u.user_id
        ) AND a.status = '❌ Убыл'
        AND DATE(a.created_at) = DATE('now')
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return
    
    # Отправляем напоминания
    for user_id, name, location, custom_location, created_at in results:
        try:
            # Выбираем случайную фразу
            import random
            reminder = random.choice(FUNNY_REMINDERS)
            
            await application.bot.send_message(
                chat_id=user_id,
                text=reminder,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания пользователю {user_id}: {e}")

def schedule_notifications(application):
    """⏰ Планировщик уведомлений"""
    def run_summary():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_admin_summary(application))
        loop.close()
    
    def run_reminders():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_return_reminders(application))
        loop.close()
    
    schedule.every().day.at(NOTIFICATION_SETTINGS['summary_time']).do(run_summary)
    schedule.every().day.at(NOTIFICATION_SETTINGS['reminder_time']).do(run_reminders)
    
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
    scheduler_thread = threading.Thread(target=schedule_notifications, args=(app,), daemon=True)
    scheduler_thread.start()
    
    logger.info("🚀 Бот запущен (оптимизированная версия)")
    logger.info("🚀 Бот запущен и готов к работе! 🎉")
    
    # Запускаем бота
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")