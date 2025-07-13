"""
Админская панель для бота учета персонала
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
    get_admin_keyboard, get_users_keyboard, get_logs_keyboard,
    get_locations_admin_keyboard, get_export_keyboard, get_manage_keyboard,
    get_cleanup_keyboard, get_cleanup_period_keyboard, get_mass_arrival_keyboard,
    get_confirmation_keyboard, get_double_confirmation_keyboard, get_cancel_keyboard,
    get_pagination_keyboard, get_user_actions_keyboard, get_settings_keyboard,
    get_notification_settings_keyboard, get_back_keyboard
)
from utils import (
    is_admin, generate_location_summary, generate_log_entry, format_admin_log,
    get_current_time, format_datetime, get_locations_list, get_confirmation_phrases,
    get_user_display_name, get_status_indicator, get_bro_phrases
)
from export import export_data

logger = logging.getLogger(__name__)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Главный обработчик всех админских callback-запросов"""
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
        
        # Маршрутизация команд
        if command == "main":
            await show_admin_main(update, context)
        elif command == "users":
            await handle_users_command(update, context, parts)
        elif command == "logs":
            await handle_logs_command(update, context, parts)
        elif command == "locations":
            await handle_locations_command(update, context, parts)
        elif command == "export":
            await handle_export_command(update, context, parts)
        elif command == "manage":
            await handle_manage_command(update, context, parts)
        elif command == "cleanup":
            await handle_cleanup_command(update, context, parts)
        elif command == "settings":
            await handle_settings_command(update, context, parts)
        elif command == "stats":
            await show_statistics(update, context)
        elif command == "mass_arrival":
            await handle_mass_arrival(update, context, parts)
        else:
            await query.edit_message_text(
                "❌ Неизвестная команда.",
                reply_markup=get_cancel_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка в admin callback: {e}")
        await query.edit_message_text(
            "⚠️ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_admin_keyboard()
        )

async def show_admin_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню админки"""
    user_id = update.callback_query.from_user.id
    user = get_user(user_id)
    
    admin_text = f"🔧 <b>Админ-панель</b>\n\n"
    admin_text += f"Добро пожаловать, <b>{user['full_name']}</b>!\n\n"
    admin_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        admin_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def handle_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд управления пользователями"""
    if len(parts) < 3:
        await show_users_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "list":
        await show_users_list(update, context)
    elif subcommand == "search":
        await start_user_search(update, context)
    elif subcommand == "add_admin":
        await start_add_admin(update, context)
    elif subcommand == "remove_admin":
        await start_remove_admin(update, context)
    elif subcommand == "delete":
        await start_delete_user(update, context)
    elif subcommand == "stats":
        await show_users_stats(update, context)
    else:
        await show_users_menu(update, context)

async def show_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню пользователей"""
    users_text = "👥 <b>Управление пользователями</b>\n\n"
    users_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        users_text,
        parse_mode='HTML',
        reply_markup=get_users_keyboard()
    )

async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список всех пользователей"""
    users = get_all_users()
    
    if not users:
        await update.callback_query.edit_message_text(
            "📝 <b>Список пользователей</b>\n\n"
            "❌ Пользователи не найдены.",
            parse_mode='HTML',
            reply_markup=get_back_keyboard("admin:users")
        )
        return
    
    # Получаем информацию о текущих локациях
    active_locations = get_active_users_by_location()
    
    users_text = f"📝 <b>Список пользователей</b> ({len(users)} чел.)\n\n"
    
    for user in users:
        status_icon = "👑" if user['is_admin'] else "👤"
        
        # Проверяем, где находится пользователь
        current_location = None
        for location, location_users in active_locations.items():
            if any(u['telegram_id'] == user['telegram_id'] for u in location_users):
                current_location = location
                break
        
        location_status = get_status_indicator(current_location is not None)
        location_text = f" • {current_location}" if current_location else " • не указано"
        
        users_text += f"{status_icon} <b>{user['full_name']}</b> {location_status}\n"
        users_text += f"   ID: <code>{user['telegram_id']}</code>{location_text}\n\n"
    
    await update.callback_query.edit_message_text(
        users_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:users")
    )

async def start_user_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать поиск пользователя"""
    context.user_data['waiting_for_search'] = 'user'
    
    await update.callback_query.edit_message_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите фамилию или часть имени для поиска:",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

async def handle_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд просмотра логов"""
    if len(parts) < 3:
        await show_logs_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "all":
        await show_all_logs(update, context)
    elif subcommand == "search_name":
        await start_logs_search_name(update, context)
    elif subcommand == "search_date":
        await start_logs_search_date(update, context)
    elif subcommand == "my_actions":
        await show_my_admin_actions(update, context)
    elif subcommand == "admin":
        await show_admin_logs(update, context)
    elif subcommand == "stats":
        await show_logs_stats(update, context)
    else:
        await show_logs_menu(update, context)

async def show_logs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню логов"""
    logs_text = "📋 <b>Просмотр логов</b>\n\n"
    logs_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        logs_text,
        parse_mode='HTML',
        reply_markup=get_logs_keyboard()
    )

async def show_all_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все логи"""
    logs = get_location_logs(limit=50)
    
    if not logs:
        await update.callback_query.edit_message_text(
            "📋 <b>Журнал действий</b>\n\n"
            "❌ Записи не найдены.",
            parse_mode='HTML',
            reply_markup=get_back_keyboard("admin:logs")
        )
        return
    
    logs_text = f"📋 <b>Журнал действий</b> (последние {len(logs)})\n\n"
    
    for log in logs:
        log_entry = generate_log_entry(log)
        logs_text += f"• {log_entry}\n"
    
    await update.callback_query.edit_message_text(
        logs_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:logs")
    )

async def start_logs_search_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать поиск логов по имени"""
    context.user_data['waiting_for_search'] = 'logs_name'
    
    await update.callback_query.edit_message_text(
        "🔍 <b>Поиск в журнале по имени</b>\n\n"
        "Введите фамилию или часть имени:",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

async def start_logs_search_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать поиск логов по дате"""
    context.user_data['waiting_for_search'] = 'logs_date'
    
    await update.callback_query.edit_message_text(
        "📅 <b>Поиск в журнале по дате</b>\n\n"
        "Введите дату в формате ГГГГ-ММ-ДД:\n"
        "Например: <code>2024-01-15</code>",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

async def handle_locations_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд управления локациями"""
    if len(parts) < 3:
        await show_locations_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "current":
        await show_current_locations(update, context)
    elif subcommand == "stats":
        await show_locations_stats(update, context)
    elif subcommand == "clear_all":
        await confirm_clear_all_locations(update, context)
    elif subcommand == "mass_arrival":
        await show_mass_arrival_menu(update, context)
    else:
        await show_locations_menu(update, context)

async def show_locations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню локаций"""
    locations_text = "📍 <b>Управление локациями</b>\n\n"
    locations_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        locations_text,
        parse_mode='HTML',
        reply_markup=get_locations_admin_keyboard()
    )

async def show_current_locations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущие локации"""
    locations_data = get_active_users_by_location()
    users_without_location = get_users_without_location()
    
    summary = generate_location_summary(locations_data)
    
    if users_without_location:
        summary += f"\n🔴 <b>Не указали местоположение</b> ({len(users_without_location)} чел.)\n"
        for user in users_without_location:
            summary += f"  • {user['full_name']}\n"
    
    await update.callback_query.edit_message_text(
        summary,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:locations")
    )

async def show_mass_arrival_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню массового прибытия"""
    mass_text = "🎯 <b>Массовое прибытие</b>\n\n"
    mass_text += "⚠️ <b>ВНИМАНИЕ!</b> Эта функция отметит <b>ВСЕХ</b> пользователей как прибывших в выбранную локацию.\n\n"
    mass_text += "Выберите локацию для массового прибытия:"
    
    await update.callback_query.edit_message_text(
        mass_text,
        parse_mode='HTML',
        reply_markup=get_mass_arrival_keyboard()
    )

async def handle_mass_arrival(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка массового прибытия"""
    if len(parts) < 3:
        await show_mass_arrival_menu(update, context)
        return
    
    location = parts[2]
    
    # Проверяем валидность локации
    if location not in get_locations_list():
        await update.callback_query.edit_message_text(
            "❌ Неизвестная локация.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Запрашиваем двойное подтверждение
    confirmation_text = f"⚠️ <b>ПОДТВЕРЖДЕНИЕ МАССОВОГО ПРИБЫТИЯ</b>\n\n"
    confirmation_text += f"Вы собираетесь отметить <b>ВСЕХ</b> пользователей как прибывших в:\n"
    confirmation_text += f"📍 <b>{location}</b>\n\n"
    confirmation_text += f"🔄 Это действие <b>НЕЛЬЗЯ ОТМЕНИТЬ</b>!\n\n"
    confirmation_text += random.choice(get_confirmation_phrases())
    
    await update.callback_query.edit_message_text(
        confirmation_text,
        parse_mode='HTML',
        reply_markup=get_confirmation_keyboard(f"mass_arrival_confirm:{location}")
    )

async def handle_cleanup_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд очистки"""
    if len(parts) < 3:
        await show_cleanup_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "logs":
        await show_cleanup_logs_menu(update, context)
    elif subcommand == "admin_logs":
        await show_cleanup_admin_logs_menu(update, context)
    elif subcommand == "locations":
        await confirm_clear_all_locations(update, context)
    elif subcommand == "full":
        await confirm_full_cleanup(update, context)
    elif subcommand == "period":
        await handle_cleanup_period(update, context, parts)
    else:
        await show_cleanup_menu(update, context)

async def show_cleanup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню очистки"""
    cleanup_text = "🧹 <b>Очистка данных</b>\n\n"
    cleanup_text += "⚠️ <b>ВНИМАНИЕ!</b> Операции очистки необратимы!\n\n"
    cleanup_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        cleanup_text,
        parse_mode='HTML',
        reply_markup=get_cleanup_keyboard()
    )

async def show_cleanup_logs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню очистки журнала"""
    cleanup_text = "🗑️ <b>Очистка журнала действий</b>\n\n"
    cleanup_text += "Выберите период для очистки:"
    
    await update.callback_query.edit_message_text(
        cleanup_text,
        parse_mode='HTML',
        reply_markup=get_cleanup_period_keyboard()
    )

async def handle_cleanup_period(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка очистки по периоду"""
    if len(parts) < 4:
        await show_cleanup_logs_menu(update, context)
        return
    
    period = parts[3]
    
    # Запрашиваем подтверждение
    period_text = {
        'day': 'записи старше 1 дня',
        'week': 'записи старше 1 недели',
        'month': 'записи старше 1 месяца',
        'all': 'ВСЕ записи'
    }.get(period, 'записи')
    
    confirmation_text = f"🗑️ <b>ПОДТВЕРЖДЕНИЕ ОЧИСТКИ</b>\n\n"
    confirmation_text += f"Будут удалены: <b>{period_text}</b>\n\n"
    confirmation_text += f"⚠️ Это действие <b>НЕЛЬЗЯ ОТМЕНИТЬ</b>!\n\n"
    confirmation_text += random.choice(get_confirmation_phrases())
    
    await update.callback_query.edit_message_text(
        confirmation_text,
        parse_mode='HTML',
        reply_markup=get_confirmation_keyboard(f"cleanup_logs_confirm:{period}")
    )

async def confirm_clear_all_locations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение очистки всех локаций"""
    confirmation_text = f"🏠 <b>ПОДТВЕРЖДЕНИЕ ОЧИСТКИ ЛОКАЦИЙ</b>\n\n"
    confirmation_text += f"Все пользователи будут отмечены как <b>покинувшие</b> свои текущие локации.\n\n"
    confirmation_text += f"⚠️ Это действие <b>НЕЛЬЗЯ ОТМЕНИТЬ</b>!\n\n"
    confirmation_text += random.choice(get_confirmation_phrases())
    
    await update.callback_query.edit_message_text(
        confirmation_text,
        parse_mode='HTML',
        reply_markup=get_confirmation_keyboard("clear_all_locations_confirm")
    )

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику системы"""
    stats = get_database_stats()
    
    stats_text = f"📊 <b>Статистика системы</b>\n\n"
    stats_text += f"👥 Пользователи: <b>{stats['users']}</b>\n"
    stats_text += f"👑 Администраторы: <b>{stats['admins']}</b>\n"
    stats_text += f"📋 Записи в журнале: <b>{stats['location_logs']}</b>\n"
    stats_text += f"📍 Активные сессии: <b>{stats['active_sessions']}</b>\n"
    stats_text += f"🔧 Админские действия: <b>{stats['admin_logs']}</b>\n\n"
    
    # Активные локации
    active_locations = get_active_users_by_location()
    if active_locations:
        stats_text += f"📍 <b>Активные локации:</b>\n"
        for location, users in active_locations.items():
            stats_text += f"  • {location}: {len(users)} чел.\n"
    
    # Пользователи без локации
    users_without_location = get_users_without_location()
    if users_without_location:
        stats_text += f"\n🔴 Без локации: <b>{len(users_without_location)}</b> чел.\n"
    
    await update.callback_query.edit_message_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:main")
    )

async def handle_export_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд экспорта"""
    if len(parts) < 3:
        await show_export_menu(update, context)
        return
    
    export_type = parts[2]
    
    if export_type in ['csv', 'excel', 'pdf']:
        await start_export(update, context, export_type)
    elif export_type == "all":
        await start_export_all(update, context)
    else:
        await show_export_menu(update, context)

async def show_export_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню экспорта"""
    export_text = "📁 <b>Экспорт данных</b>\n\n"
    export_text += "Выберите формат для экспорта:"
    
    await update.callback_query.edit_message_text(
        export_text,
        parse_mode='HTML',
        reply_markup=get_export_keyboard()
    )

async def start_export(update: Update, context: ContextTypes.DEFAULT_TYPE, export_type: str):
    """Начать экспорт данных"""
    user_id = update.callback_query.from_user.id
    
    await update.callback_query.edit_message_text(
        f"📊 Экспорт данных в формате {export_type.upper()}...\n\n"
        f"⏳ Пожалуйста, подождите...",
        parse_mode='HTML'
    )
    
    try:
        file_path = await export_data(export_type)
        
        if file_path:
            # Логируем экспорт
            add_admin_log(user_id, f"Экспорт данных ({export_type})")
            
            # Отправляем файл
            with open(file_path, 'rb') as file:
                await update.callback_query.message.reply_document(
                    document=file,
                    filename=f"personnel_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_type}",
                    caption=f"📊 Экспорт данных в формате {export_type.upper()}\n"
                           f"🕒 Создан: {format_datetime(datetime.now().isoformat())}"
                )
            
            await update.callback_query.edit_message_text(
                f"✅ Экспорт завершен!\n\n"
                f"Файл отправлен выше.",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("admin:export")
            )
        else:
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при экспорте данных.",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("admin:export")
            )
            
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при экспорте данных.",
            parse_mode='HTML',
            reply_markup=get_back_keyboard("admin:export")
        )

async def handle_manage_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд управления системой"""
    if len(parts) < 3:
        await show_manage_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "system_stats":
        await show_system_stats(update, context)
    elif subcommand == "backup":
        await start_backup(update, context)
    else:
        await show_manage_menu(update, context)

async def show_manage_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню управления"""
    manage_text = "🔧 <b>Управление системой</b>\n\n"
    manage_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        manage_text,
        parse_mode='HTML',
        reply_markup=get_manage_keyboard()
    )

async def handle_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE, search_text: str):
    """Обработка ввода поиска"""
    search_type = context.user_data.get('waiting_for_search')
    
    if search_type == 'logs_name':
        await search_logs_by_name(update, context, search_text)
    elif search_type == 'logs_date':
        await search_logs_by_date(update, context, search_text)
    elif search_type == 'user':
        await search_users(update, context, search_text)
    
    # Очищаем состояние
    context.user_data.pop('waiting_for_search', None)

async def search_logs_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
    """Поиск логов по имени"""
    logs = get_location_logs(limit=50, user_filter=name)
    
    if not logs:
        await update.message.reply_text(
            f"🔍 <b>Результаты поиска</b>\n\n"
            f"❌ По запросу '<b>{name}</b>' ничего не найдено.",
            parse_mode='HTML',
            reply_markup=get_back_keyboard("admin:logs")
        )
        return
    
    results_text = f"🔍 <b>Результаты поиска по '{name}'</b>\n\n"
    results_text += f"Найдено записей: <b>{len(logs)}</b>\n\n"
    
    for log in logs:
        log_entry = generate_log_entry(log)
        results_text += f"• {log_entry}\n"
    
    await update.message.reply_text(
        results_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:logs")
    )

async def search_logs_by_date(update: Update, context: ContextTypes.DEFAULT_TYPE, date: str):
    """Поиск логов по дате"""
    logs = get_location_logs(limit=100, date_filter=date)
    
    if not logs:
        await update.message.reply_text(
            f"📅 <b>Результаты поиска</b>\n\n"
            f"❌ За <b>{date}</b> записей не найдено.",
            parse_mode='HTML',
            reply_markup=get_back_keyboard("admin:logs")
        )
        return
    
    results_text = f"📅 <b>Записи за {date}</b>\n\n"
    results_text += f"Найдено записей: <b>{len(logs)}</b>\n\n"
    
    for log in logs:
        log_entry = generate_log_entry(log)
        results_text += f"• {log_entry}\n"
    
    await update.message.reply_text(
        results_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin:logs")
    )

async def execute_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Выполнение подтвержденного действия"""
    user_id = update.callback_query.from_user.id
    
    try:
        if action.startswith("mass_arrival_confirm:"):
            location = action.split(":", 1)[1]
            count = mark_all_as_arrived(location)
            
            # Логируем действие
            add_admin_log(user_id, f"Массовое прибытие в {location}", details=f"Отмечено {count} пользователей")
            
            await update.callback_query.edit_message_text(
                f"✅ <b>Массовое прибытие выполнено!</b>\n\n"
                f"📍 Локация: <b>{location}</b>\n"
                f"👥 Отмечено пользователей: <b>{count}</b>\n\n"
                f"🕒 Время: {format_datetime(get_current_time().isoformat())}",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("admin:locations")
            )
            
        elif action.startswith("cleanup_logs_confirm:"):
            period = action.split(":", 1)[1]
            deleted_count = clear_location_logs(period)
            
            # Логируем действие
            add_admin_log(user_id, f"Очистка журнала ({period})", details=f"Удалено {deleted_count} записей")
            
            await update.callback_query.edit_message_text(
                f"✅ <b>Очистка журнала выполнена!</b>\n\n"
                f"🗑️ Удалено записей: <b>{deleted_count}</b>\n\n"
                f"🕒 Время: {format_datetime(get_current_time().isoformat())}",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("admin:cleanup")
            )
            
        elif action == "clear_all_locations_confirm":
            count = clear_all_locations()
            
            # Логируем действие
            add_admin_log(user_id, "Очистка всех локаций", details=f"Очищено {count} локаций")
            
            await update.callback_query.edit_message_text(
                f"✅ <b>Очистка локаций выполнена!</b>\n\n"
                f"🏠 Очищено локаций: <b>{count}</b>\n\n"
                f"🕒 Время: {format_datetime(get_current_time().isoformat())}",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("admin:locations")
            )
            
        else:
            await update.callback_query.edit_message_text(
                "❌ Неизвестное действие.",
                reply_markup=get_cancel_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка выполнения действия {action}: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при выполнении действия.",
            reply_markup=get_cancel_keyboard()
        )

async def handle_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Обработка команд настроек"""
    if len(parts) < 3:
        await show_settings_menu(update, context)
        return
    
    subcommand = parts[2]
    
    if subcommand == "notifications":
        await show_notification_settings(update, context)
    else:
        await show_settings_menu(update, context)

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню настроек"""
    settings_text = "⚙️ <b>Настройки системы</b>\n\n"
    settings_text += "Выберите раздел:"
    
    await update.callback_query.edit_message_text(
        settings_text,
        parse_mode='HTML',
        reply_markup=get_settings_keyboard()
    )

async def show_notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать настройки уведомлений"""
    settings_text = "⏰ <b>Настройки уведомлений</b>\n\n"
    settings_text += "Выберите действие:"
    
    await update.callback_query.edit_message_text(
        settings_text,
        parse_mode='HTML',
        reply_markup=get_notification_settings_keyboard()
    )

# Обработчики подтверждений
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Обработка подтверждения действий"""
    if action.startswith("mass_arrival_confirm:") or action.startswith("cleanup_logs_confirm:") or action == "clear_all_locations_confirm":
        await execute_action(update, context, action)
    else:
        await update.callback_query.edit_message_text(
            "❌ Неизвестное действие.",
            reply_markup=get_cancel_keyboard()
        )

# Добавим обработчики для поисковых запросов
async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обновленный главный обработчик админских callback-запросов"""
    # Проверяем, не это ли поисковый запрос
    if data.startswith("search_input:"):
        search_text = data.split(":", 1)[1]
        await handle_search_input(update, context, search_text)
        return
    
    # Проверяем, не это ли выполнение действия
    if data.startswith("execute:"):
        action = data.split(":", 1)[1]
        await handle_confirmation(update, context, action)
        return
    
    # Проверяем, не это ли финальное выполнение действия
    if data.startswith("final_execute:"):
        action = data.split(":", 1)[1]
        await execute_action(update, context, action)
        return
    
    # Вызываем оригинальный обработчик
    await handle_admin_callback(update, context, data)