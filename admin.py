from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import get_all_users, get_all_logs, clear_logs, get_daily_stats, get_logs_by_name_filter, get_logs_by_date
from keyboards import (
    admin_menu_keyboard,
    admin_export_keyboard,
    admin_danger_keyboard,
    clear_logs_period_keyboard,
    confirm_danger_keyboard,
    double_confirm_danger_keyboard,
    admin_manage_users_keyboard,
    admin_back_keyboard,
    admin_logs_keyboard
)
from utils import format_datetime, get_today_date, is_action_allowed, get_current_time
from export import export_to_csv, export_to_excel, export_to_pdf
import sqlite3
import os

DB_NAME = "data/personnel.db"

def handle_admin_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    user = query.from_user

    if not is_admin(user.id):
        query.edit_message_text("❌ У вас нет прав администратора!")
        return

    # Защита от быстрых нажатий
    if not is_action_allowed(user.id, data):
        return

    if data == 'admin_panel' or data == 'admin_back':
        query.edit_message_text(
            "👑 **АДМИН-ПАНЕЛЬ**\n\n"
            "🎛️ Добро пожаловать в центр управления!\n"
            "🔧 Здесь вы можете управлять всеми функциями системы\n"
            "📊 Просматривать отчеты и статистику\n"
            "⚙️ Настраивать параметры работы\n\n"
            "⚡ Выберите раздел:",
            reply_markup=admin_menu_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'admin_manage':
        query.edit_message_text(
            "👥 **УПРАВЛЕНИЕ ЛИЧНЫМ СОСТАВОМ**\n\n"
            "🔧 Здесь вы можете:\n"
            "📝 Просматривать список всех бойцов\n"
            "➕ Добавлять новых сотрудников\n"
            "✏️ Редактировать данные\n"
            "🗑️ Удалять неактивных пользователей\n\n"
            "⚡ Выберите действие:",
            reply_markup=admin_manage_users_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'admin_logs':
        query.edit_message_text(
            "📜 **ЖУРНАЛ ДЕЙСТВИЙ**\n\n"
            "🔍 Выберите способ просмотра:\n"
            "📋 Фильтр по фамилии - поиск конкретного сотрудника\n"
            "📅 Фильтр по дате - записи за определенный день\n"
            "📜 Показать все - последние 10 записей\n\n"
            "⚡ Выберите действие:",
            reply_markup=admin_logs_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'logs_show_all':
        logs = get_all_logs()[:10]
        if not logs:
            query.edit_message_text(
                "📜 **ЖУРНАЛ ДЕЙСТВИЙ**\n\n"
                "🔍 В журнале пока нет записей\n"
                "📝 Записи появятся после действий пользователей\n"
                "⏰ Система готова к работе",
                reply_markup=admin_logs_keyboard(),
                parse_mode='Markdown'
            )
            return

        log_text = "📜 **ЖУРНАЛ ДЕЙСТВИЙ** (последние 10)\n\n"
        
        for i, log in enumerate(logs, 1):
            # Определяем эмодзи для действий - красный/зеленый кружок
            action_emoji = "🟢" if log['action'] == "Прибыл" else "🔴"
            
            # Эмодзи для локаций
            location_emoji = ""
            if log['location']:
                location_map = {
                    "Поликлиника": "🏥",
                    "ОБРМП": "⚓",
                    "Калининград": "🌆",
                    "Магазин": "🛒",
                    "Столовая": "🍲",
                    "Госпиталь": "🏨",
                    "Рабочка": "⚙️",
                    "ВВК": "🩺",
                    "МФЦ": "🏛️",
                    "Патруль": "🚓",
                    "В расположение": "🏠"
                }
                location_emoji = location_map.get(log['location'], "📍")
            
            log_text += f"{i}. {action_emoji} **{log['full_name']}** - {log['action']}\n"
            log_text += f"   ⏰ {format_datetime(log['timestamp'])}\n"
            
            if log['location']:
                log_text += f"   📍 {location_emoji} {log['location']}\n"
            
            if log['comment']:
                log_text += f"   💬 {log['comment']}\n"
            
            log_text += "\n"

        query.edit_message_text(
            log_text,
            reply_markup=admin_logs_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'logs_filter_name':
        context.user_data['awaiting_filter'] = 'name'
        query.edit_message_text(
            "🔍 **ФИЛЬТР ПО ФАМИЛИИ**\n\n"
            "📝 Введите фамилию или часть фамилии для поиска:\n"
            "Например: Иванов, Петр, Сид\n\n"
            "⚠️ Следующим сообщением отправьте текст для поиска",
            reply_markup=admin_logs_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'logs_filter_date':
        context.user_data['awaiting_filter'] = 'date'
        query.edit_message_text(
            "📅 **ФИЛЬТР ПО ДАТЕ**\n\n"
            "📝 Введите дату в формате ДД.ММ.ГГГГ:\n"
            "Например: 13.01.2024\n\n"
            "⚠️ Следующим сообщением отправьте дату",
            reply_markup=admin_logs_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'admin_export':
        query.edit_message_text(
            "💾 **ЭКСПОРТ ДАННЫХ**\n\n"
            "📊 Выберите формат для экспорта:\n"
            "📄 CSV - для таблиц\n"
            "📋 Excel - для отчетов\n"
            "📑 PDF - для печати\n"
            "🗂️ Все форматы - полный комплект\n\n"
            "⚡ Выберите формат:",
            reply_markup=admin_export_keyboard(),
            parse_mode='Markdown'
        )

    elif data.startswith('export_'):
        date = get_today_date()
        logs = get_all_logs(date)

        if not logs:
            query.edit_message_text(
                "❌ **НЕТ ДАННЫХ ДЛЯ ЭКСПОРТА!**\n\n"
                "📊 За сегодня нет записей в журнале\n"
                "📝 Данные появятся после действий пользователей\n"
                "⏰ Попробуйте позже",
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )
            return

        try:
            if data == 'export_csv':
                file_path = export_to_csv(logs, date)
                file_type = "CSV"
            elif data == 'export_excel':
                file_path = export_to_excel(logs, date)
                file_type = "Excel"
            elif data == 'export_pdf':
                file_path = export_to_pdf(logs, date)
                file_type = "PDF"
            else:  # export_all
                export_to_csv(logs, date)
                export_to_excel(logs, date)
                export_to_pdf(logs, date)
                file_path = f"exports/{date}"
                file_type = "все форматы"

            query.edit_message_text(
                f"✅ **ЭКСПОРТ ВЫПОЛНЕН УСПЕШНО!**\n\n"
                f"📊 Формат: {file_type}\n"
                f"📁 Файлы сохранены в: {file_path}\n"
                f"⏰ Время: {format_datetime(get_current_time())}\n"
                f"👤 Выполнил: {user.full_name}",
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )
        except Exception as e:
            query.edit_message_text(
                f"❌ **ОШИБКА ЭКСПОРТА!**\n\n"
                f"💥 Причина: {str(e)}\n"
                f"🔧 Обратитесь к администратору\n"
                f"📋 Попробуйте другой формат",
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )

    elif data == 'admin_summary':
        today = get_today_date()
        stats = get_daily_stats(today)
        all_users = get_all_users()

        summary = f"📊 **СВОДКА ПО ЛИЧНОМУ СОСТАВУ**\n"
        summary += f"� Дата: {today}\n"
        summary += f"⏰ Время: {format_datetime(get_current_time())}\n\n"

        # Группировка по статусам
        in_base = [u for u in all_users if u['status'] == 'В расположении']
        out_base = [u for u in all_users if u['status'] == 'Вне базы']
        unknown = [u for u in all_users if u['status'] == 'unknown']

        summary += "📈 **ОБЩАЯ СТАТИСТИКА:**\n"
        summary += f"👥 Всего зарегистрировано: {len(all_users)} чел.\n"
        summary += f"🏠 В расположении: {len(in_base)} чел.\n"
        summary += f"🚶‍♂️ Вне базы: {len(out_base)} чел.\n"
        summary += f"❓ Статус неизвестен: {len(unknown)} чел.\n\n"

        # Детальная разбивка по локациям для тех, кто вне базы
        if out_base:
            summary += "📍 **РАСПРЕДЕЛЕНИЕ ПО ЛОКАЦИЯМ:**\n"
            
            # Группируем по локациям
            location_count = {}
            for user in out_base:
                location = user['location'] or 'Неизвестно'
                location_count[location] = location_count.get(location, 0) + 1
            
            # Эмодзи для локаций
            location_emojis = {
                "Поликлиника": "🏥",
                "ОБРМП": "⚓",
                "Калининград": "🌆",
                "Магазин": "🛒",
                "Столовая": "🍲",
                "Госпиталь": "🏨",
                "Рабочка": "⚙️",
                "ВВК": "🩺",
                "МФЦ": "🏛️",
                "Патруль": "🚓",
                "Неизвестно": "❓"
            }
            
            for location, count in sorted(location_count.items()):
                emoji = location_emojis.get(location, "📍")
                summary += f"{emoji} {location}: {count} чел.\n"
            
            summary += "\n"

        # Список тех, кто в расположении
        if in_base:
            summary += "🏠 **В РАСПОЛОЖЕНИИ:**\n"
            for user in in_base:
                summary += f"✅ {user['full_name']}\n"
            summary += "\n"

        # Активность за сегодня
        if stats:
            summary += "📊 **АКТИВНОСТЬ ЗА СЕГОДНЯ:**\n"
            for stat in stats:
                summary += f"📝 {stat[0]}: {stat[1]} действий\n"
        else:
            summary += "📊 **АКТИВНОСТЬ ЗА СЕГОДНЯ:**\n"
            summary += "📝 Пока нет записей\n"

        query.edit_message_text(
            summary,
            reply_markup=admin_back_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'admin_danger':
        query.edit_message_text(
            "🚨 **ОПАСНАЯ ЗОНА**\n\n"
            "⚠️ Здесь находятся критические функции!\n"
            "🔥 Действия могут быть НЕОБРАТИМЫМИ!\n"
            "🔒 Все операции логируются!\n\n"
            "⚡ Выберите действие:",
            reply_markup=admin_danger_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'danger_clear_logs_menu':
        query.edit_message_text(
            "🗑️ **ОЧИСТКА ЖУРНАЛА**\n\n"
            "📊 Выберите период для очистки:\n"
            "📅 За сегодня - удалит записи только за сегодня\n"
            "📆 За неделю - удалит записи за последние 7 дней\n"
            "🗓️ За месяц - удалит записи за последние 30 дней\n"
            "🗑️ Весь журнал - удалит ВСЕ записи\n\n"
            "⚠️ Все действия НЕОБРАТИМЫ!",
            reply_markup=clear_logs_period_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'danger_clear_today':
        query.edit_message_text(
            "⚠️ **ВНИМАНИЕ! ОЧИСТКА ЗА СЕГОДНЯ!**\n\n"
            "📅 Вы хотите удалить записи за сегодня?\n"
            "🗑️ Все записи за сегодняшний день будут удалены!\n"
            "📊 Восстановление будет невозможно!\n"
            "🔒 Это действие логируется!\n\n"
            "⚠️ Подтвердите действие:",
            reply_markup=confirm_danger_keyboard('clear_today'),
            parse_mode='Markdown'
        )

    elif data == 'danger_clear_week':
        query.edit_message_text(
            "⚠️ **ВНИМАНИЕ! ОЧИСТКА ЗА НЕДЕЛЮ!**\n\n"
            "📆 Вы хотите удалить записи за неделю?\n"
            "🗑️ Все записи за последние 7 дней будут удалены!\n"
            "📊 Восстановление будет невозможно!\n"
            "🔒 Это действие логируется!\n\n"
            "⚠️ Подтвердите действие:",
            reply_markup=confirm_danger_keyboard('clear_week'),
            parse_mode='Markdown'
        )

    elif data == 'danger_clear_month':
        query.edit_message_text(
            "⚠️ **ВНИМАНИЕ! ОЧИСТКА ЗА МЕСЯЦ!**\n\n"
            "🗓️ Вы хотите удалить записи за месяц?\n"
            "🗑️ Все записи за последние 30 дней будут удалены!\n"
            "📊 Восстановление будет невозможно!\n"
            "🔒 Это действие логируется!\n\n"
            "⚠️ Подтвердите действие:",
            reply_markup=confirm_danger_keyboard('clear_month'),
            parse_mode='Markdown'
        )

    elif data.startswith('danger_clear_'):
        if data == 'danger_clear_today':
            period = 'today'
            period_text = "ЗА СЕГОДНЯ"
            description = "записи только за сегодняшний день"
        elif data == 'danger_clear_week':
            period = 'week'
            period_text = "ЗА НЕДЕЛЮ"
            description = "записи за последние 7 дней"
        elif data == 'danger_clear_month':
            period = 'month'
            period_text = "ЗА МЕСЯЦ"
            description = "записи за последние 30 дней"
        elif data == 'danger_clear_logs':
            period = 'all'
            period_text = "ПОЛНАЯ ОЧИСТКА"
            description = "ВСЕ записи в журнале"
        else:
            return
        
        query.edit_message_text(
            f"⚠️ **ВНИМАНИЕ! ОЧИСТКА {period_text}!**\n\n"
            f"🗑️ Будут удалены: {description}\n"
            f"❌ Восстановление будет невозможно!\n"
            f"🔒 Это действие логируется!\n\n"
            f"⚠️ Подтвердите действие:",
            reply_markup=confirm_danger_keyboard(f'clear_{period}'),
            parse_mode='Markdown'
        )

    elif data.startswith('confirm_clear_'):
        if data == 'confirm_clear_today':
            period = 'today'
            period_text = "ЗА СЕГОДНЯ"
            action_text = "УДАЛИТЬ записи за сегодня"
        elif data == 'confirm_clear_week':
            period = 'week'
            period_text = "ЗА НЕДЕЛЮ"
            action_text = "УДАЛИТЬ записи за неделю"
        elif data == 'confirm_clear_month':
            period = 'month'
            period_text = "ЗА МЕСЯЦ"
            action_text = "УДАЛИТЬ записи за месяц"
        elif data == 'confirm_clear_logs':
            period = 'all'
            period_text = "ПОЛНОСТЬЮ"
            action_text = "УДАЛИТЬ ВСЕ записи"
        else:
            return
            
        query.edit_message_text(
            f"🚨 **ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ!**\n\n"
            f"💥 Вы ТОЧНО хотите {action_text}?\n"
            f"🗑️ Очистка журнала {period_text}!\n"
            f"⏰ Восстановление невозможно!\n"
            f"📋 Данные исчезнут навсегда!\n\n"
            f"🔥 **ДЕЙСТВИЕ НЕОБРАТИМО!**",
            reply_markup=double_confirm_danger_keyboard(f'clear_{period}'),
            parse_mode='Markdown'
        )

    elif data.startswith('execute_clear_'):
        try:
            if data == 'execute_clear_today':
                deleted_count = clear_logs_by_period('today')
                period_text = "ЗА СЕГОДНЯ"
                action_text = "записи за сегодня"
            elif data == 'execute_clear_week':
                deleted_count = clear_logs_by_period('week')
                period_text = "ЗА НЕДЕЛЮ"
                action_text = "записи за неделю"
            elif data == 'execute_clear_month':
                deleted_count = clear_logs_by_period('month')
                period_text = "ЗА МЕСЯЦ"
                action_text = "записи за месяц"
            elif data == 'execute_clear_all' or data == 'execute_clear_logs':
                clear_logs()
                deleted_count = "все"
                period_text = "ПОЛНОСТЬЮ"
                action_text = "все записи"
            else:
                return
            
            # Логируем критическое действие
            import logging
            logging.warning(f"CRITICAL: Journal cleared ({action_text}) by admin {user.id} ({user.full_name})")
            
            query.edit_message_text(
                f"✅ **ЖУРНАЛ ОЧИЩЕН {period_text}!**\n\n"
                f"🗑️ Удалено: {deleted_count} записей\n"
                f"⏰ Время очистки: {format_datetime(get_current_time())}\n"
                f"👤 Выполнил: {user.full_name}\n"
                f"🔒 Действие зафиксировано в логах",
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )
        except Exception as e:
            query.edit_message_text(
                f"❌ **ОШИБКА ОЧИСТКИ ЖУРНАЛА!**\n\n"
                f"💥 Причина: {str(e)}\n"
                f"🔧 Обратитесь к администратору",
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )

    elif data == 'danger_reset_statuses':
        query.edit_message_text(
            "⚠️ **ВНИМАНИЕ! МАССОВОЕ ДЕЙСТВИЕ!**\n\n"
            "♻️ Вы хотите сбросить все статусы?\n"
            "👥 Все пользователи станут 'неизвестно'!\n"
            "📊 Текущие локации будут очищены!\n"
            "🔒 Это действие логируется!\n\n"
            "⚠️ Подтвердите первый шаг:",
            reply_markup=confirm_danger_keyboard('reset_statuses'),
            parse_mode='Markdown'
        )

    elif data == 'confirm_reset_statuses':
        query.edit_message_text(
            "🚨 **ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ!**\n\n"
            "💥 Вы ТОЧНО хотите СБРОСИТЬ ВСЕ статусы?\n"
            "♻️ Все бойцы станут 'неизвестно'!\n"
            "📍 Все локации будут очищены!\n"
            "📊 Статистика собьется!\n\n"
            "🔥 **ДЕЙСТВИЕ НЕОБРАТИМО!**",
            reply_markup=double_confirm_danger_keyboard('reset_statuses'),
            parse_mode='Markdown'
        )

    elif data == 'execute_reset_statuses':
        try:
            reset_all_statuses()
            
            # Логируем критическое действие
            import logging
            logging.warning(f"CRITICAL: All statuses reset by admin {user.id} ({user.full_name})")
            
            query.edit_message_text(
                "✅ **СТАТУСЫ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ СБРОШЕНЫ!**\n\n"
                "♻️ Все статусы обнулены\n"
                "📍 Все локации очищены\n"
                "⏰ Время сброса: {}\n"
                "👤 Выполнил: {}\n"
                "🔒 Действие зафиксировано в логах".format(
                    format_datetime(get_current_time()),
                    user.full_name
                ),
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )
        except Exception as e:
            query.edit_message_text(
                f"❌ **ОШИБКА СБРОСА СТАТУСОВ!**\n\n"
                f"💥 Причина: {str(e)}\n"
                f"🔧 Обратитесь к администратору",
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )

    elif data == 'danger_mark_all_arrived':
        query.edit_message_text(
            "⚠️ **ВНИМАНИЕ! МАССОВОЕ ДЕЙСТВИЕ!**\n\n"
            "🏠 Вы хотите отметить всех прибывшими?\n"
            "👥 Все пользователи станут 'В расположении'!\n"
            "📊 Изменятся все статусы!\n"
            "📝 Будут созданы записи в журнале!\n"
            "🔒 Это действие логируется!\n\n"
            "⚠️ Подтвердите первый шаг:",
            reply_markup=confirm_danger_keyboard('mark_all_arrived'),
            parse_mode='Markdown'
        )

    elif data == 'confirm_mark_all_arrived':
        query.edit_message_text(
            "🚨 **ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ!**\n\n"
            "💥 Вы ТОЧНО хотите ОТМЕТИТЬ ВСЕХ прибывшими?\n"
            "🏠 Все бойцы станут 'В расположении'!\n"
            "📝 Будет создано много записей в журнале!\n"
            "📊 Статистика изменится!\n\n"
            "🔥 **ДЕЙСТВИЕ НЕОБРАТИМО!**",
            reply_markup=double_confirm_danger_keyboard('mark_all_arrived'),
            parse_mode='Markdown'
        )

    elif data == 'execute_mark_all_arrived':
        try:
            updated_count = mark_all_arrived()
            
            # Логируем критическое действие
            import logging
            logging.warning(f"CRITICAL: Mass arrival marked by admin {user.id} ({user.full_name}), updated {updated_count} users")
            
            query.edit_message_text(
                "✅ **МАССОВАЯ ОТМЕТКА О ПРИБЫТИИ ВЫПОЛНЕНА!**\n\n"
                "🏠 Все отмечены как прибывшие\n"
                "📊 Обновлено статусов: {}\n"
                "⏰ Время операции: {}\n"
                "👤 Выполнил: {}\n"
                "🔒 Действие зафиксировано в логах".format(
                    updated_count,
                    format_datetime(get_current_time()),
                    user.full_name
                ),
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )
            

            
        except Exception as e:
            query.edit_message_text(
                f"❌ **ОШИБКА МАССОВОЙ ОТМЕТКИ!**\n\n"
                f"💥 Причина: {str(e)}\n"
                f"🔧 Обратитесь к администратору",
                reply_markup=admin_back_keyboard(),
                parse_mode='Markdown'
            )

def is_admin(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admins WHERE tg_id = ?", (tg_id,))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0

def reset_all_statuses():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'unknown', location = ''")
    conn.commit()
    conn.close()

def mark_all_arrived():
    """Отмечает всех пользователей как прибывших в расположение"""
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Получаем всех пользователей
    cursor.execute("SELECT id, full_name, status FROM users")
    users = cursor.fetchall()
    
    current_time = get_current_time()
    updated_count = 0
    
    for user_id, full_name, current_status in users:
        # Обновляем статус только если он не "В расположении"
        if current_status != 'В расположении':
            # Обновляем статус пользователя
            cursor.execute("""
                UPDATE users 
                SET status = 'В расположении', location = '', last_action = ?
                WHERE id = ?
            """, (current_time, user_id))
            
            # Добавляем запись в лог
            cursor.execute("""
                INSERT INTO logs (user_id, action, location, comment, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, "Прибыл", "В расположение", "Массовая отметка админом", current_time))
            
            updated_count += 1
    
    conn.commit()
    conn.close()
    
    return updated_count

def clear_logs_by_period(period):
    """Очищает логи за указанный период"""
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    current_time = get_current_time()
    
    if period == 'today':
        # За сегодня
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute("DELETE FROM logs WHERE timestamp >= ?", (start_of_day,))
    elif period == 'week':
        # За неделю
        week_ago = current_time - timedelta(days=7)
        cursor.execute("DELETE FROM logs WHERE timestamp >= ?", (week_ago,))
    elif period == 'month':
        # За месяц
        month_ago = current_time - timedelta(days=30)
        cursor.execute("DELETE FROM logs WHERE timestamp >= ?", (month_ago,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count

def get_period_description(period):
    """Возвращает описание периода"""
    descriptions = {
        'today': 'за сегодня',
        'week': 'за неделю',
        'month': 'за месяц'
    }
    return descriptions.get(period, period)