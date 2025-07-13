THIS SHOULD BE A LINTER ERRORfrom telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import get_all_users, get_all_logs, clear_logs, get_daily_stats
from keyboards import (
    admin_menu_keyboard,
    admin_export_keyboard,
    admin_danger_keyboard,
    confirm_danger_keyboard,
    admin_manage_users_keyboard,
    admin_back_keyboard
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
            "👑 Административное меню:",
            reply_markup=admin_menu_keyboard()
        )

    elif data == 'admin_manage':
        query.edit_message_text(
            "👥 Управление личным составом:",
            reply_markup=admin_manage_users_keyboard()
        )

    elif data == 'admin_logs':
        logs = get_all_logs()[:10]
        if not logs:
            query.edit_message_text(
                "📜 В журнале пока нет записей",
                reply_markup=admin_back_keyboard()
            )
            return

        log_text = "Последние действия в системе:\n\n"
        for log in logs:
            log_text += (f"{format_datetime(log['timestamp'])} | "
                         f"{log['full_name']} | {log['action']} | "
                         f"{log['location']}\n")

        query.edit_message_text(
            log_text,
            reply_markup=admin_back_keyboard()
        )

    elif data == 'admin_export':
        query.edit_message_text(
            "💾 Экспорт данных:\nВыберите формат:",
            reply_markup=admin_export_keyboard()
        )

    elif data.startswith('export_'):
        date = get_today_date()
        logs = get_all_logs(date)

        if not logs:
            query.edit_message_text(
                "❌ Нет данных для экспорта за сегодня!",
                reply_markup=admin_back_keyboard()
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
                f"✅ Экспорт в {file_type} выполнен успешно!\n"
                f"Файлы сохранены в: {file_path}",
                reply_markup=admin_back_keyboard()
            )
        except Exception as e:
            query.edit_message_text(
                f"❌ Ошибка экспорта: {str(e)}",
                reply_markup=admin_back_keyboard()
            )

    elif data == 'admin_summary':
        today = get_today_date()
        stats = get_daily_stats(today)

        summary = f"📊 Сводка за {today}:\n\n"
        summary += "📍 Распределение по локациям:\n"

        for stat in stats:
            summary += f"{stat[0]}: {stat[1]} чел.\n"

        in_base = [u for u in get_all_users() if u['status'] == 'В расположении']
        out_base = [u for u in get_all_users() if u['status'] == 'Вне базы']

        summary += f"\n🏠 В расположении: {len(in_base)} чел."
        summary += f"\n🚶‍♂️ Вне базы: {len(out_base)} чел."

        query.edit_message_text(
            summary,
            reply_markup=admin_back_keyboard()
        )

    elif data == 'admin_danger':
        query.edit_message_text(
            "⚠️ Опасная зона:\nВыберите действие:",
            reply_markup=admin_danger_keyboard()
        )

    elif data == 'danger_clear_logs':
        query.edit_message_text(
            "❌ Вы уверены, что хотите очистить весь журнал действий?\n"
            "Это действие нельзя отменить!",
            reply_markup=confirm_danger_keyboard('clear_logs')
        )

    elif data == 'confirm_clear_logs':
        try:
            clear_logs()
            query.edit_message_text(
                "✅ Журнал действий полностью очищен!",
                reply_markup=admin_back_keyboard()
            )
        except Exception as e:
            query.edit_message_text(
                f"❌ Ошибка очистки журнала: {str(e)}",
                reply_markup=admin_back_keyboard()
            )

    elif data == 'danger_reset_statuses':
        query.edit_message_text(
            "❌ Вы уверены, что хотите сбросить все статусы?\n"
            "Все пользователи будут помечены как 'неизвестно'!",
            reply_markup=confirm_danger_keyboard('reset_statuses')
        )

    elif data == 'confirm_reset_statuses':
        try:
            reset_all_statuses()
            query.edit_message_text(
                "✅ Статусы всех пользователей сброшены!",
                reply_markup=admin_back_keyboard()
            )
        except Exception as e:
            query.edit_message_text(
                f"❌ Ошибка сброса статусов: {str(e)}",
                reply_markup=admin_back_keyboard()
            )

    elif data == 'danger_mark_all_arrived':
        query.edit_message_text(
            "🏠 Вы уверены, что хотите отметить всех прибывшими?\n"
            "Все пользователи будут помечены как 'В расположении'!",
            reply_markup=confirm_danger_keyboard('mark_all_arrived')
        )

    elif data == 'confirm_mark_all_arrived':
        try:
            updated_count = mark_all_arrived()
            query.edit_message_text(
                f"✅ Отметка о прибытии выполнена!\n"
                f"Обновлено статусов: {updated_count}",
                reply_markup=admin_back_keyboard()
            )
            
            # Уведомляем админов о массовом действии
            admin_message = (
                f"🏠 Массовая отметка о прибытии!\n"
                f"👑 Выполнил: {query.from_user.full_name}\n"
                f"📊 Обновлено: {updated_count} пользователей\n"
                f"⏰ Время: {format_datetime(get_current_time())}"
            )
            
            # Отправляем уведомление всем админам
            from notifications import notify_admins
            from telegram import Bot
            bot = Bot(token=query.bot.token)
            notify_admins(bot, admin_message)
            
        except Exception as e:
            query.edit_message_text(
                f"❌ Ошибка отметки прибытия: {str(e)}",
                reply_markup=admin_back_keyboard()
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