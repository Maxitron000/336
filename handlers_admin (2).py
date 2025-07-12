# handlers_admin.py

from telegram import Update
from telegram.ext import CallbackContext
from keyboards import (
    admin_main_keyboard, admin_users_keyboard, admin_journal_keyboard, admin_settings_keyboard,
    admin_admins_keyboard, admin_notifications_keyboard, admin_danger_zone_keyboard, rights_checkbox_keyboard
)
from admins import (
    load_admins, is_admin, add_admin, delete_admin, get_admin_rights, set_admin_rights, list_admins
)
from database import (
    read_logs, export_logs, clear_logs, get_all_users, add_user, delete_user, update_fio, get_user_profile
)
from notifications import (
    format_admin_summary, format_full_journal, format_user_profile, format_export_done, format_clear_done
)
from config import MAIN_ADMIN_ID, EXPORT_FORMATS, LOGS_PAGE_SIZE
from utils import now_str, auto_delete_message

def admin_panel_entry(update: Update, context: CallbackContext):
    user = update.effective_user
    admins = load_admins()
    if not is_admin(user.id, admins):
        msg = update.message.reply_text("⛔ Доступ только для админов!")
        auto_delete_message(context, msg)
        return

    msg = update.message.reply_text(
        "⚙️ <b>Админ-панель</b>\n\nВыберите нужный раздел:",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )
    context.user_data["admin_state"] = "ADMIN_MAIN"
    auto_delete_message(context, msg, delay=120)

def admin_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user = update.effective_user
    admins = load_admins()
    if not is_admin(user.id, admins):
        query.answer("⛔ Нет доступа!")
        query.edit_message_text("⛔ Нет доступа!")
        return

    # Главная админка
    if data == "admin_menu":
        query.edit_message_text(
            "⚙️ <b>Админ-панель</b>\n\nВыберите нужный раздел:",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML"
        )
        context.user_data["admin_state"] = "ADMIN_MAIN"
    elif data == "admin":
        pass
    elif data == "admin_summary":
        pass
    elif data == "admin_users":
        query.edit_message_text(
            "👥 <b>Личный состав</b>\n\nДействия:",
            reply_markup=admin_users_keyboard(), parse_mode="HTML"
        )
        context.user_data["admin_state"] = "ADMIN_USERS"
    # ... дальше остальные обработчики ...
    elif data == "admin_journal":
        logs = read_logs(max_count=LOGS_PAGE_SIZE)
        msg = format_full_journal(logs)
        query.edit_message_text(
            msg, reply_markup=admin_journal_keyboard(), parse_mode="HTML"
        )
        context.user_data["admin_state"] = "ADMIN_JOURNAL"
    elif data == "admin_export_journal":
        for fmt in EXPORT_FORMATS:
            file_path = export_logs(fmt)
            if file_path:
                query.message.reply_document(open(file_path, "rb"), filename=file_path.split("/")[-1])
        query.edit_message_text("📤 Экспорт завершён!", reply_markup=admin_journal_keyboard())
    elif data == "admin_settings":
        query.edit_message_text(
            "⚙️ <b>Настройки</b>\n\nВыберите опцию:",
            reply_markup=admin_settings_keyboard(), parse_mode="HTML"
        )
        context.user_data["admin_state"] = "ADMIN_SETTINGS"
    elif data == "admin_admins":
        admin_list = list_admins()
        msg = "<b>Список админов:</b>\n" + "\n".join(admin_list)
        query.edit_message_text(
            msg, reply_markup=admin_admins_keyboard(), parse_mode="HTML"
        )
        context.user_data["admin_state"] = "ADMIN_ADMINS"
    elif data == "admin_edit_rights":
        admin_id = context.user_data.get("selected_admin_id", MAIN_ADMIN_ID)
        rights = get_admin_rights(admin_id)
        query.edit_message_text(
            f"Редактирование прав для {admin_id}:",
            reply_markup=rights_checkbox_keyboard(rights)
        )
    elif data.startswith("toggle_right_"):
        code = data.replace("toggle_right_", "")
        admin_id = context.user_data.get("selected_admin_id", MAIN_ADMIN_ID)
        rights = get_admin_rights(admin_id)
        if code in rights:
            rights.remove(code)
        else:
            rights.append(code)
        set_admin_rights(admin_id, rights)
        query.edit_message_reply_markup(rights_checkbox_keyboard(rights))
    elif data == "admin_notifications":
        query.edit_message_text(
            "🔔 <b>Уведомления</b>\n\nНастройте рассылки:",
            reply_markup=admin_notifications_keyboard(), parse_mode="HTML"
        )
        context.user_data["admin_state"] = "ADMIN_NOTIFICATIONS"
    elif data == "admin_danger_zone":
        query.edit_message_text(
            "⚠️ <b>Опасная зона</b>\n\nЗдесь только особые действия:",
            reply_markup=admin_danger_zone_keyboard(), parse_mode="HTML"
        )
        context.user_data["admin_state"] = "ADMIN_DANGER"
    elif data == "admin_mark_all_arrived":
        # Логика массового "Прибыл"
        # ...
        query.edit_message_text("🚨 Все отмечены как прибывшие!", reply_markup=admin_main_keyboard())
    elif data == "back_menu":
        admin_panel_entry(update, context)

# --- Обработка текстовых команд админа (пример) ---

def admin_message_handler(update: Update, context: CallbackContext):
    state = context.user_data.get("admin_state", "")
    user = update.effective_user
    admins = load_admins()
    if not is_admin(user.id, admins):
        msg = update.message.reply_text("⛔ Доступ только для админов!")
        auto_delete_message(context, msg)
        return

    text = update.message.text.strip()
    if state == "ADMIN_ADD_USER":
        # Логика добавления нового бойца
        # ...
        msg = update.message.reply_text(f"✅ Новый боец добавлен: {text}")
        auto_delete_message(context, msg)
        admin_panel_entry(update, context)
    elif state == "ADMIN_CHANGE_FIO":
        # Логика смены ФИО бойца
        # ...
        msg = update.message.reply_text(f"✅ ФИО бойца обновлено: {text}")
        auto_delete_message(context, msg)
        admin_panel_entry(update, context)
    elif state == "ADMIN_ADD_ADMIN":
        # Логика добавления нового админа
        # ...
        msg = update.message.reply_text(f"✅ Новый админ добавлен: {text}")
        auto_delete_message(context, msg)
        admin_panel_entry(update, context)
    elif state == "ADMIN_DEL_ADMIN":
        # Логика удаления админа
        # ...
        msg = update.message.reply_text(f"❌ Админ удалён: {text}")
        auto_delete_message(context, msg)
        admin_panel_entry(update, context)
    elif state == "ADMIN_SET_SCHEDULE":
        # Логика установки времени рассылки
        # ...
        msg = update.message.reply_text(f"⏰ Время уведомлений установлено: {text}")
        auto_delete_message(context, msg)
        admin_panel_entry(update, context)
    else:
        admin_panel_entry(update, context)
