"""
Админская панель v2.0 для бота учета персонала
Соответствует чек-листу v2.0 с многоуровневой структурой и эмодзи
"""

import logging
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import (
    get_user, get_all_users, add_admin_log, get_admin_logs, 
    get_location_logs, get_active_users_by_location, get_users_without_location,
    clear_location_logs, clear_admin_logs, clear_all_locations, mark_all_as_arrived,
    get_database_stats, delete_user, set_admin_status, get_user_location_history
)
from keyboards import (
    get_admin_keyboard, get_personnel_keyboard, get_journal_keyboard,
    get_settings_keyboard, get_danger_zone_keyboard, get_notification_settings_keyboard,
    get_export_journal_keyboard
)
from keyboards_v2 import (
    get_confirmation_keyboard, get_double_confirmation_keyboard,
    get_cancel_keyboard, get_back_keyboard
)
from utils import (
    is_admin, generate_location_summary, generate_log_entry, format_admin_log,
    get_current_time, format_datetime, get_locations_list, get_confirmation_phrases,
    get_user_display_name, get_status_indicator, get_bro_phrases
)
from export import export_data

logger = logging.getLogger(__name__)

async def handle_admin_callback_v2(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Главный обработчик всех админских callback-запросов v2.0"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Проверяем права администратора
    if not is_admin(user_id):
        await query.edit_message_text(
            "❌ У вас нет прав администратора.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    try:
        # Разбираем команду
        parts = data.split(":")
        
        if len(parts) < 2:
            await query.edit_message_text(
                "❌ Неверный формат команды.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        command = parts[1]
        
        # Маршрутизация команд по новой структуре
        if command == "main":
            await show_admin_main_v2(update, context)
        elif command == "dashboard":
            await show_dashboard(update, context)
        elif command == "personnel":
            await handle_personnel_command(update, context, parts)
        elif command == "journal":
            await handle_journal_command(update, context, parts)
        elif command == "settings":
            await handle_settings_command(update, context, parts)
        elif command == "danger":
            await handle_danger_zone_command(update, context, parts)
        else:
            await query.edit_message_text(
                "❌ Неизвестная команда.",
                reply_markup=get_cancel_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка в admin callback v2: {e}")
        await query.edit_message_text(
            "⚠️ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_admin_keyboard()
        )

async def show_admin_main_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню админки v2.0 - Уровень 1: 🏠 Главное меню"""
    user_id = update.callback_query.from_user.id
    user = get_user(user_id)
    
    admin_text = f"🏠 <b>Главное меню админ-панели</b>\n\n"
    admin_text += f"Добро пожаловать, <b>{user['full_name']}</b>!\n\n"
    admin_text += "Выберите раздел:"
    
    await update.callback_query.edit_message_text(
        admin_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Быстрая сводка - показывает кто отсутствует с группировкой по локациям"""
    active_locations = get_active_users_by_location()
    users_without_location = get_users_without_location()
    
    dashboard_text = "📊 <b>Быстрая сводка</b>\n\n"
    
    # Показываем отсутствующих
    if users_without_location:
        dashboard_text += "❌ <b>Отсутствуют:</b>\n"
        for user in users_without_location:
            dashboard_text += f"• {user['full_name']}\n"
        dashboard_text += "\n"
    else:
        dashboard_text += "✅ <b>Все бойцы на месте!</b>\n\n"
    
    # Показываем группировку по локациям
    if active_locations:
        dashboard_text += "📍 <b>Распределение по локациям:</b>\n"
        for location, users in active_locations.items():
            emoji = get_location_emoji(location)
            dashboard_text += f"{emoji} <b>{location}</b>: {len(users)} чел.\n"
            for user in users[:3]:  # Показываем первые 3 имени
                dashboard_text += f"  • {user['full_name']}\n"
            if len(users) > 3:
                dashboard_text += f"  ... и еще {len(users) - 3}\n"
            dashboard_text += "\n"
    
    await update.callback_query.edit_message_text(
        dashboard_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:main")
    )

async def handle_personnel_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд управления личным составом - Уровень 2: Меню «👥 Управление л/с»"""
    if len(parts) < 3:
        await show_personnel_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "change_name":
        await start_change_name(update, context)
    elif subcommand == "add_user":
        await start_add_user(update, context)
    elif subcommand == "delete_user":
        await start_delete_user(update, context)
    elif subcommand == "manage_admins":
        await show_manage_admins(update, context)
    elif subcommand == "list_all":
        await show_all_personnel(update, context)
    elif subcommand == "search":
        await start_personnel_search(update, context)
    else:
        await show_personnel_menu(update, context)

async def show_personnel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню управления личным составом"""
    personnel_text = "👥 <b>Управление личным составом</b>\n\n"
    personnel_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        personnel_text,
        parse_mode='HTML',
        reply_markup=get_personnel_keyboard()
    )

async def handle_journal_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд журнала событий - Уровень 2: Меню «📖 Журнал событий»"""
    if len(parts) < 3:
        await show_journal_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "export":
        await show_export_journal_menu(update, context)
    elif subcommand == "all_events":
        await show_all_events(update, context)
    elif subcommand == "search_name":
        await start_journal_search_name(update, context)
    elif subcommand == "search_date":
        await start_journal_search_date(update, context)
    elif subcommand == "my_actions":
        await show_my_actions(update, context)
    elif subcommand == "admin_logs":
        await show_admin_logs_menu(update, context)
    else:
        await show_journal_menu(update, context)

async def show_journal_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню журнала событий"""
    journal_text = "📖 <b>Журнал событий</b>\n\n"
    journal_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        journal_text,
        parse_mode='HTML',
        reply_markup=get_journal_keyboard()
    )

async def show_export_journal_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню экспорта журнала"""
    export_text = "📥 <b>Экспорт журнала</b>\n\n"
    export_text += "Выберите формат экспорта:"
    
    await update.callback_query.edit_message_text(
        export_text,
        parse_mode='HTML',
        reply_markup=get_export_journal_keyboard()
    )

async def handle_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд настроек - Уровень 2: Меню «⚙️ Настройки»"""
    if len(parts) < 3:
        await show_settings_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "notifications":
        await show_notification_settings(update, context)
    elif subcommand == "admins":
        await show_admin_management(update, context)
    elif subcommand == "danger_zone":
        await show_danger_zone_menu(update, context)
    elif subcommand == "system":
        await show_system_settings(update, context)
    elif subcommand == "stats":
        await show_system_stats(update, context)
    elif subcommand == "maintenance":
        await show_maintenance_menu(update, context)
    else:
        await show_settings_menu(update, context)

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню настроек"""
    settings_text = "⚙️ <b>Настройки системы</b>\n\n"
    settings_text += "Выберите раздел настроек:"
    
    await update.callback_query.edit_message_text(
        settings_text,
        parse_mode='HTML',
        reply_markup=get_settings_keyboard()
    )

async def show_danger_zone_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню опасной зоны - Уровень 3: Меню «⚠️ Опасная зона»"""
    danger_text = "⚠️ <b>Опасная зона</b>\n\n"
    danger_text += "🚨 <b>ВНИМАНИЕ!</b> Эти действия необратимы!\n\n"
    danger_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        danger_text,
        parse_mode='HTML',
        reply_markup=get_danger_zone_keyboard()
    )

async def handle_danger_zone_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд опасной зоны"""
    if len(parts) < 3:
        await show_danger_zone_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "mark_all_arrived":
        await confirm_mark_all_arrived(update, context)
    elif subcommand == "clear_all_data":
        await confirm_clear_all_data(update, context)
    elif subcommand == "reset_system":
        await confirm_reset_system(update, context)
    elif subcommand == "delete_all_users":
        await confirm_delete_all_users(update, context)
    else:
        await show_danger_zone_menu(update, context)

async def confirm_mark_all_arrived(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение отметки всех прибывшими с обязательным шагом подтверждения"""
    users_without_location = get_users_without_location()
    
    if not users_without_location:
        await update.callback_query.edit_message_text(
            "✅ Все бойцы уже отмечены как прибывшие!",
            reply_markup=get_back_keyboard("admin:danger")
        )
        return
    
    confirm_text = "🚨 <b>Отметить всех прибывшими</b>\n\n"
    confirm_text += f"⚠️ Это действие отметит <b>{len(users_without_location)}</b> бойцов как прибывших.\n\n"
    confirm_text += "📋 Список бойцов:\n"
    for user in users_without_location[:5]:  # Показываем первые 5
        confirm_text += f"• {user['full_name']}\n"
    if len(users_without_location) > 5:
        confirm_text += f"... и еще {len(users_without_location) - 5}\n\n"
    
    confirm_text += "🔐 <b>Требуется двойное подтверждение!</b>"
    
    await update.callback_query.edit_message_text(
        confirm_text,
        parse_mode='HTML',
        reply_markup=get_double_confirmation_keyboard("admin:danger:mark_all_arrived:confirm")
    )

# Вспомогательные функции
def get_location_emoji(location: str) -> str:
    """Получить эмодзи для локации"""
    emoji_map = {
        "🏥 Поликлиника": "🏥",
        "⚓ ОБРМП": "⚓", 
        "🌆 Калининград": "🌆",
        "🛒 Магазин": "🛒",
        "🍲 Столовая": "🍲",
        "🏨 Госпиталь": "🏨",
        "⚙️ Рабочка": "⚙️",
        "🩺 ВВК": "🩺",
        "🏛️ МФЦ": "🏛️",
        "🚓 Патруль": "🚓"
    }
    return emoji_map.get(location, "📍")

# Заглушки для функций, которые будут реализованы позже
async def start_change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "✏️ <b>Смена ФИО бойца</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:personnel")
    )

async def start_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "➕ <b>Добавление нового бойца</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:personnel")
    )

async def start_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "❌ <b>Удаление бойца</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:personnel")
    )

async def show_manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "👑 <b>Управление админами</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:personnel")
    )

async def show_all_personnel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📋 <b>Список всех бойцов</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:personnel")
    )

async def start_personnel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔍 <b>Поиск бойца</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:personnel")
    )

async def show_all_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📋 <b>Все события</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:journal")
    )

async def start_journal_search_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔍 <b>Поиск по имени</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:journal")
    )

async def start_journal_search_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📅 <b>Поиск по дате</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:journal")
    )

async def show_my_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "👤 <b>Мои действия</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:journal")
    )

async def show_admin_logs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔧 <b>Админские логи</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:journal")
    )

async def show_notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:settings")
    )

async def show_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "👑 <b>Управление админами</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:settings")
    )

async def show_system_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔧 <b>Системные настройки</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:settings")
    )

async def show_system_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📊 <b>Статистика системы</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:settings")
    )

async def show_maintenance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🛠️ <b>Обслуживание системы</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:settings")
    )

async def confirm_clear_all_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🗑️ <b>Очистка всех данных</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:danger")
    )

async def confirm_reset_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔄 <b>Сброс системы</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:danger")
    )

async def confirm_delete_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "💀 <b>Удаление всех пользователей</b>\n\n"
        "Функция в разработке...",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:danger")
    )