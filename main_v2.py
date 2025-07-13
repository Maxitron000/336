#!/usr/bin/env python3
"""
🚀 Personnel Tracking Bot v2.0 - Реструктурированная версия
📦 Модульная архитектура с 3-уровневой админ-панелью
🎯 Система учета прибытия/убытия персонала военной части
"""

import logging
import asyncio
import os
import sqlite3
import schedule
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Импорт модулей
from ui_helpers import NavigationBuilder, MessageFormatter, CleanChat
from admin_panels import AdminPanels, DangerZoneOperations  
from user_management import UserManager
from notification_system import NotificationManager, NotificationSettingsPanel

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
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
MAIN_ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else None

# Глобальные экземпляры
nav_builder = NavigationBuilder()
message_formatter = MessageFormatter()
admin_panels = AdminPanels()
user_manager = UserManager() 
danger_zone = DangerZoneOperations()

# Система уведомлений - инициализируется после создания приложения
notification_manager = None
notification_settings_panel = None

# === БАЗА ДАННЫХ ===
def init_db():
    """🔧 Инициализация базы данных"""
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
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
    
    # Оптимизация для производительности
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    
    # Автоочистка старых записей (6 месяцев)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS auto_cleanup
        AFTER INSERT ON arrivals
        BEGIN
            DELETE FROM arrivals 
            WHERE created_at < datetime('now', '-6 months');
        END
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ База данных инициализирована")

def is_admin(user_id):
    """👑 Проверка прав администратора"""
    return user_id in ADMIN_IDS

def is_main_admin(user_id):
    """👑 Проверка главного администратора"""
    return user_id == MAIN_ADMIN_ID

# === КОМАНДЫ ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🚀 Команда /start с чистым чатом"""
    user_id = update.effective_user.id
    
    # Удаляем команду для чистоты чата
    await CleanChat.delete_command(update, context)
    
    # Проверяем регистрацию
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        # Первый запуск - просим ФИО с детальными примерами
        text = (
            "👋 <b>Добро пожаловать в систему учета персонала!</b>\n\n"
            "📝 Введите ваше ФИО в формате:\n"
            "📋 <b>Фамилия И.О.</b> (инициалы через точку)\n\n"
            "✅ <b>Правильные примеры:</b>\n"
            "• Иванов И.И.\n"
            "• Петров П.П.\n"
            "• Сидоров С.С.\n"
            "• Козлов К.К.\n\n"
            "❌ <b>Неправильные примеры:</b>\n"
            "• Иванов Иван (без инициалов)\n"
            "• И.И. Иванов (неправильный порядок)\n"
            "• иванов и.и. (строчные буквы)\n"
            "• Иванов И И (без точек)\n\n"
            "✍️ <b>Напишите ваше ФИО:</b>"
        )
        
        keyboard = nav_builder.build_back_menu("cancel")
        await CleanChat.edit_or_send(update, text, keyboard)
        
        # Устанавливаем состояние ожидания ФИО
        context.user_data['waiting_for_fullname'] = True
        return
    
    # Пользователь зарегистрирован - показываем главное меню
    user_name = user[0]
    is_user_admin = is_admin(user_id)
    
    text = message_formatter.format_main_menu(user_name, is_user_admin)
    keyboard = nav_builder.build_main_menu(is_user_admin)
    
    await CleanChat.edit_or_send(update, text, keyboard)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📝 Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Обработка регистрации ФИО
    if context.user_data.get('waiting_for_fullname'):
        result = await process_fullname_registration(update, context, text)
        return
    
    # Обработка добавления пользователя админом
    if context.user_data.get('waiting_for') == 'add_user':
        if not is_admin(user_id):
            await update.message.reply_text("❌ Нет прав доступа!")
            return
        
        result_text = await user_manager.process_add_user(text, context)
        keyboard = nav_builder.build_back_menu("admin_personnel")
        await update.message.reply_text(result_text, reply_markup=keyboard, parse_mode='HTML')
        
        # Очищаем состояние
        context.user_data.clear()
        return
    
    # Обработка редактирования ФИО
    if context.user_data.get('waiting_for') == 'edit_name':
        if not is_admin(user_id):
            await update.message.reply_text("❌ Нет прав доступа!")
            return
        
        result_text = await user_manager.process_edit_name(text, context)
        keyboard = nav_builder.build_back_menu("admin_personnel")
        await update.message.reply_text(result_text, reply_markup=keyboard, parse_mode='HTML')
        
        # Очищаем состояние
        context.user_data.clear()
        return
    
    # Обработка пользовательской локации
    if context.user_data.get('waiting_for_custom_location'):
        await process_custom_location(update, context, text)
        return
    
    # Если ничего не ожидается, показываем главное меню
    await start_command(update, context)

async def process_fullname_registration(update, context, text):
    """👤 Обработка регистрации ФИО"""
    user_id = update.effective_user.id
    
    # Валидация ФИО
    if len(text) < 5 or '.' not in text:
        error_text = (
            "❌ <b>Неверный формат ФИО!</b>\n\n"
            "📋 <b>Правильный формат:</b> Фамилия И.О.\n\n"
            "✅ <b>Требования:</b>\n"
            "• Фамилия с заглавной буквы\n"
            "• Инициалы через точку (И.О.)\n"
            "• Минимум 5 символов\n"
            "• Хотя бы одна точка\n\n"
            "✅ <b>Правильные примеры:</b>\n"
            "• Иванов И.И.\n"
            "• Петров П.П.\n"
            "• Сидоров С.С.\n\n"
            "❌ <b>Ваш ввод не соответствует формату</b>\n"
            "✍️ <b>Попробуйте еще раз:</b>"
        )
        keyboard = nav_builder.build_back_menu("cancel")
        await update.message.reply_text(error_text, reply_markup=keyboard, parse_mode='HTML')
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
        
        success_text = (
            f"✅ <b>Регистрация завершена!</b>\n"
            f"🎖️ <b>Добро пожаловать, {text}!</b>\n\n"
            f"📋 <b>Теперь вы можете:</b>\n"
            f"• ✅ Отмечать прибытие\n"
            f"• ❌ Отмечать убытие\n"
            f"• 📋 Просматривать свой журнал\n\n"
            f"🔄 <b>Система автоматически покажет главное меню...</b>"
        )
        await update.message.reply_text(success_text, parse_mode='HTML')
        
        # Очищаем состояние и показываем главное меню
        context.user_data.clear()
        
        # Создаем фиктивный update для show_main_menu
        is_user_admin = is_admin(user_id)
        menu_text = message_formatter.format_main_menu(text, is_user_admin)
        keyboard = nav_builder.build_main_menu(is_user_admin)
        
        await update.message.reply_text(menu_text, reply_markup=keyboard, parse_mode='HTML')
        
    except sqlite3.IntegrityError:
        await update.message.reply_text("❌ Такое ФИО уже зарегистрировано!", parse_mode='HTML')
    finally:
        conn.close()

async def process_custom_location(update, context, text):
    """📝 Обработка пользовательской локации"""
    user_id = update.effective_user.id
    action = context.user_data.get('custom_location_action')
    user_name = context.user_data.get('user_name')
    
    # Валидация
    if len(text) < 2:
        await update.message.reply_text("❌ Слишком короткое название! (минимум 2 символа)")
        return
    
    if len(text) > 50:
        await update.message.reply_text("❌ Слишком длинное название! (максимум 50 символов)")
        return
    
    # Сохраняем отметку
    status = "✅ Прибыл" if action == "arrived" else "❌ Убыл"
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO arrivals (user_id, location, custom_location, status) VALUES (?, ?, ?, ?)",
        (user_id, "Другое", text, status)
    )
    conn.commit()
    conn.close()
    
    # Отправляем уведомление админам
    if notification_manager:
        time_str = datetime.now().strftime('%H:%M %d.%m.%Y')
        if action == "arrived":
            await notification_manager.send_arrival_notification(user_name, text, time_str, ADMIN_IDS)
        else:
            await notification_manager.send_departure_notification(user_name, text, time_str, ADMIN_IDS)
    
    # Подтверждение
    time_str = datetime.now().strftime('%H:%M %d.%m.%Y')
    confirmation_text = message_formatter.format_action_confirmation(user_name, action, text, time_str)
    
    keyboard = [
        [nav_builder.build_main_menu(is_admin(user_id)).inline_keyboard[0][0]],  # Кнопка "Еще отметка"
        [nav_builder.build_back_menu("main_menu").inline_keyboard[0][0]]  # Кнопка "Главное меню"
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(confirmation_text, reply_markup=reply_markup, parse_mode='HTML')
    
    # Очищаем состояние
    context.user_data.clear()

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
    
    if not user and data not in ['cancel']:
        text = message_formatter.format_error("Сначала зарегистрируйтесь командой /start")
        await CleanChat.edit_or_send(query, text)
        return
    
    user_name = user[0] if user else ""
    
    # === ОСНОВНЫЕ КОМАНДЫ ===
    if data == "cancel":
        context.user_data.clear()
        text = "❌ Операция отменена"
        await CleanChat.edit_or_send(query, text)
        return
    
    elif data == "main_menu":
        is_user_admin = is_admin(user_id)
        text = message_formatter.format_main_menu(user_name, is_user_admin)
        keyboard = nav_builder.build_main_menu(is_user_admin)
        await CleanChat.edit_or_send(query, text, keyboard)
    
    # === ПОЛЬЗОВАТЕЛЬСКИЕ ДЕЙСТВИЯ ===
    elif data == "user_arrived":
        text = f"✅ <b>{user_name}</b>\n\n📍 Выберите локацию прибытия:"
        keyboard = nav_builder.build_locations_menu("arrived")
        await CleanChat.edit_or_send(query, text, keyboard)
    
    elif data == "user_departed":
        text = f"❌ <b>{user_name}</b>\n\n📍 Выберите локацию убытия:"
        keyboard = nav_builder.build_locations_menu("departed")
        await CleanChat.edit_or_send(query, text, keyboard)
    
    elif data == "user_journal":
        await show_user_journal(query, context, user_id, user_name)
    
    # === ЛОКАЦИИ ===
    elif data.startswith("location_"):
        await handle_location_action(query, context, data, user_id, user_name)
    
    # === АДМИН-ПАНЕЛЬ ===
    elif data == "admin_panel":
        if not is_admin(user_id):
            text = message_formatter.format_error("Нет прав доступа!")
            await CleanChat.edit_or_send(query, text)
            return
        await admin_panels.show_admin_panel(query, context)
    
    elif data == "admin_quick_summary":
        if not is_admin(user_id):
            return
        await admin_panels.show_quick_summary(query, context)
    
    elif data == "admin_personnel":
        if not is_admin(user_id):
            return
        await admin_panels.show_personnel_management(query, context)
    
    elif data == "admin_event_log":
        if not is_admin(user_id):
            return
        await admin_panels.show_event_log(query, context)
    
    elif data == "admin_settings":
        if not is_admin(user_id):
            return
        await admin_panels.show_settings(query, context)
    
    # === УПРАВЛЕНИЕ ПЕРСОНАЛОМ ===
    elif data == "personnel_add_user":
        if not is_admin(user_id):
            return
        await user_manager.show_add_user_prompt(query, context)
    
    elif data == "personnel_edit_name":
        if not is_admin(user_id):
            return
        await user_manager.show_edit_name_list(query, context)
    
    elif data == "personnel_delete_user":
        if not is_admin(user_id):
            return
        await user_manager.show_delete_user_list(query, context)
    
    elif data.startswith("edit_user_"):
        if not is_admin(user_id):
            return
        target_user_id = int(data.split("_")[2])
        await user_manager.show_edit_name_prompt(query, context, target_user_id)
    
    elif data.startswith("delete_user_"):
        if not is_admin(user_id):
            return
        target_user_id = int(data.split("_")[2])
        await user_manager.show_delete_confirmation(query, context, target_user_id)
    
    # === НАСТРОЙКИ ===
    elif data == "settings_notifications":
        if not is_admin(user_id):
            return
        if notification_settings_panel:
            await notification_settings_panel.show_notification_settings(query, context)
    
    elif data == "settings_danger":
        if not is_admin(user_id):
            return
        await admin_panels.show_danger_zone(query, context)
    
    # === ОПАСНАЯ ЗОНА ===
    elif data == "danger_mark_all_arrived":
        if not is_admin(user_id):
            return
        await danger_zone.mark_all_arrived_confirmation(query, context)
    
    elif data == "danger_clear_log":
        if not is_admin(user_id):
            return
        await danger_zone.clear_log_confirmation(query, context)
    
    # === ПОДТВЕРЖДЕНИЯ ===
    elif data.startswith("confirm_"):
        await handle_confirmations(query, context, data, user_id)
    
    # === НАСТРОЙКИ УВЕДОМЛЕНИЙ ===
    elif data.startswith("toggle_"):
        if not is_admin(user_id) or not notification_settings_panel:
            return
        setting_key = data.replace("toggle_", "") + "_enabled" if data.replace("toggle_", "") in ["summary", "reminders"] else data.replace("toggle_", "")
        if setting_key == "silent":
            setting_key = "silent_mode"
        elif setting_key == "arrival":
            setting_key = "arrival_notifications"
        elif setting_key == "departure":
            setting_key = "departure_notifications"
        
        await notification_settings_panel.toggle_setting(query, context, setting_key)

async def handle_location_action(query, context, data, user_id, user_name):
    """📍 Обработка действий с локациями"""
    parts = data.split("_", 2)
    if len(parts) < 3:
        return
    
    action = parts[1]  # arrived или departed
    location = parts[2]
    
    # Если выбрана локация "Другое"
    if location == "Другое":
        context.user_data['waiting_for_custom_location'] = True
        context.user_data['custom_location_action'] = action
        context.user_data['user_name'] = user_name
        
        action_text = "прибытия" if action == "arrived" else "убытия"
        
        text = (
            f"📝 <b>Введите место {action_text}:</b>\n\n"
            f"🎖️ {user_name}\n\n"
            f"💡 <b>Примеры:</b>\n"
            f"• Дом\n"
            f"• Спортзал\n"
            f"• Учебка\n"
            f"• Командировка\n"
            f"• Отпуск\n\n"
            f"📝 <b>Напишите ваше местоположение (2-50 символов):</b>"
        )
        keyboard = nav_builder.build_back_menu("main_menu")
        await CleanChat.edit_or_send(query, text, keyboard)
        return
    
    # Обычная обработка локации
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
    
    # Отправляем уведомление админам
    if notification_manager:
        time_str = datetime.now().strftime('%H:%M %d.%m.%Y')
        if action == "arrived":
            await notification_manager.send_arrival_notification(user_name, location, time_str, ADMIN_IDS)
        else:
            await notification_manager.send_departure_notification(user_name, location, time_str, ADMIN_IDS)
    
    # Показываем подтверждение
    time_str = datetime.now().strftime('%H:%M %d.%m.%Y')
    confirmation_text = message_formatter.format_action_confirmation(user_name, action, location, time_str)
    
    keyboard = nav_builder.build_back_menu("main_menu")
    await CleanChat.edit_or_send(query, confirmation_text, keyboard)

async def show_user_journal(query, context, user_id, user_name):
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
        text = f"📋 <b>Журнал: {user_name}</b>\n\n❌ Нет записей"
    else:
        text = f"📋 <b>Журнал: {user_name}</b>\n\n"
        for location, custom_location, status, created_at in records:
            display_location = custom_location if custom_location else location
            date_str = datetime.fromisoformat(created_at).strftime('%d.%m %H:%M')
            text += f"• {display_location} - {status} ({date_str})\n"
    
    keyboard = nav_builder.build_back_menu("main_menu")
    await CleanChat.edit_or_send(query, text, keyboard)

async def handle_confirmations(query, context, data, user_id):
    """✅ Обработка подтверждений"""
    if not is_admin(user_id):
        return
    
    parts = data.split("_", 2)
    if len(parts) < 2:
        return
    
    action = parts[1]
    
    if action == "mark" and len(parts) >= 3 and parts[2] == "all":
        await danger_zone.execute_mark_all_arrived(query, context)
    
    elif action == "clear" and len(parts) >= 3 and parts[2] == "log":
        await danger_zone.execute_clear_log(query, context)
    
    elif action == "delete" and len(parts) >= 3 and parts[2] == "user":
        if len(parts) >= 4:
            target_user_id = int(parts[3])
            result_text = await user_manager.execute_delete_user(target_user_id)
            keyboard = nav_builder.build_back_menu("admin_personnel")
            await CleanChat.edit_or_send(query, result_text, keyboard)

# === ПЛАНИРОВЩИК УВЕДОМЛЕНИЙ ===
def schedule_notifications():
    """⏰ Планировщик уведомлений"""
    if not notification_manager:
        return
    
    def run_summary():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(notification_manager.send_daily_summary(ADMIN_IDS))
        loop.close()
    
    def run_reminders():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(notification_manager.send_return_reminders())
        loop.close()
    
    # Запланированные задачи
    schedule.every().day.at("19:00").do(run_summary)
    schedule.every().day.at("20:30").do(run_reminders)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# === ОСНОВНАЯ ФУНКЦИЯ ===
async def main():
    """🚀 Основная функция"""
    global notification_manager, notification_settings_panel
    
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден в переменных окружения")
    
    # Инициализируем базу данных
    init_db()
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Инициализируем систему уведомлений
    notification_manager = NotificationManager(app)
    notification_settings_panel = NotificationSettingsPanel(notification_manager)
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=schedule_notifications, daemon=True)
    scheduler_thread.start()
    
    logger.info("🚀 Personnel Tracking Bot v2.0 запущен")
    print("🚀 Personnel Tracking Bot v2.0 готов к работе! 🎉")
    
    # Запускаем бота
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise