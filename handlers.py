from telegram import Update, ParseMode
from telegram.ext import CallbackContext
import time
from database import get_user, register_user, log_action, get_user_logs, is_admin
from keyboards import (
    main_menu_keyboard,
    locations_keyboard,
    comment_keyboard,
    history_keyboard,
    admin_menu_keyboard
)
from utils import validate_full_name, format_datetime, load_locations, is_action_allowed
from notifications import notify_admins

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    tg_id = user.id

    db_user = get_user(tg_id)
    if db_user:
        show_admin = is_admin(tg_id)
        update.message.reply_text(
            f"Добро пожаловать, {db_user['full_name']}!",
            reply_markup=main_menu_keyboard(show_admin_button=show_admin)
        )
    else:
        update.message.reply_text(
            "👋 Добро пожаловать! Для регистрации в системе "
            "введите ваше ФИО в формате 'Иванов И.И.'"
        )

def admin_command(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin(user.id):
        update.message.reply_text("❌ У вас нет прав администратора!")
        return

    update.message.reply_text(
        "👑 Административное меню:",
        reply_markup=admin_menu_keyboard()
    )

def text_handler(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text.strip()

    if context.user_data.get('awaiting_comment'):
        location = context.user_data.get('location')
        if location:
            db_user = get_user(user.id)
            if db_user:
                # Защита: нельзя убыть если уже убыл
                if db_user['status'] == 'Вне базы':
                    update.message.reply_text("❌ Вы уже убыли! Сначала отметьте прибытие.")
                    context.user_data.pop('awaiting_comment', None)
                    context.user_data.pop('location', None)
                    return

                timestamp = log_action(db_user['id'], "Убыл", location, text)
                notify_admins(
                    context.bot,
                    f"🔴 {db_user['full_name']} убыл в {location}\n"
                    f"⏰ {format_datetime(timestamp)}\n"
                    f"💬 Комментарий: {text}\n"
                    f"👤 TG: [{user.id}](tg://user?id={user.id})"
                )
                update.message.reply_text(
                    f"✅ Вы отмечены как убывший в {location} с комментарием.",
                    reply_markup=main_menu_keyboard(show_admin_button=is_admin(user.id)))
            else:
                update.message.reply_text("❌ Ошибка: пользователь не найден.")
        else:
            update.message.reply_text("❌ Ошибка: не указана локация.")

        context.user_data.pop('awaiting_comment', None)
        context.user_data.pop('location', None)
        return

    if validate_full_name(text):
        if register_user(user.id, text):
            update.message.reply_text(
                f"✅ Регистрация успешна, {text}!",
                reply_markup=main_menu_keyboard(show_admin_button=is_admin(user.id)))
        else:
            update.message.reply_text("⚠️ Ошибка регистрации. Обратитесь к администратору.")
    else:
        update.message.reply_text(
            "❌ Неверный формат ФИО. Введите в формате 'Иванов И.И.'"
        )

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    user = query.from_user
    tg_id = user.id

    db_user = get_user(tg_id)
    if not db_user:
        query.edit_message_text("Сначала зарегистрируйтесь с помощью команды /start")
        return

    user_id = db_user['id']
    full_name = db_user['full_name']
    show_admin = is_admin(tg_id)

    # Защита от быстрых повторных нажатий
    if not is_action_allowed(tg_id, data):
        return

    if data == 'arrived':
        # Защита: нельзя прибыть если уже в расположении
        if db_user['status'] == 'В расположении':
            query.edit_message_text(
                "✅ Вы уже в расположении!",
                reply_markup=main_menu_keyboard(show_admin_button=show_admin)
            )
            return

        timestamp = log_action(user_id, "Прибыл")
        notify_admins(
            context.bot,
            f"🟢 {full_name} прибыл в расположение\n"
            f"⏰ {format_datetime(timestamp)}\n"
            f"👤 TG: [{user.id}](tg://user?id={user.id})"
        )
        query.edit_message_text(
            f"✅ {full_name}, вы отмечены как прибывший в расположение",
            reply_markup=main_menu_keyboard(show_admin_button=show_admin)
        )

    elif data == 'depart':
        # Защита: нельзя убыть если уже вне базы
        if db_user['status'] == 'Вне базы':
            query.edit_message_text(
                "❌ Вы уже убыли! Сначала отметьте прибытие.",
                reply_markup=main_menu_keyboard(show_admin_button=show_admin)
            )
            return

        query.edit_message_text(
            "Выберите место назначения:",
            reply_markup=locations_keyboard()
        )

    elif data.startswith('loc_'):
        loc_id = int(data.split('_')[1])
        locations = load_locations()
        location = next((loc for loc in locations if loc['id'] == loc_id), None)

        if location:
            loc_str = f"{location['emoji']} {location['name']}"
            context.user_data['location'] = loc_str
            query.edit_message_text(
                f"Вы выбрали: {loc_str}\nДобавить комментарий к убытию?",
                reply_markup=comment_keyboard()
            )
        else:
            query.edit_message_text("❌ Локация не найдена.")

    elif data == 'add_comment':
        query.edit_message_text("Введите ваш комментарий:")
        context.user_data['awaiting_comment'] = True

    elif data == 'no_comment':
        location = context.user_data.get('location', 'Неизвестно')
        # Защита: нельзя убыть если уже вне базы
        if db_user['status'] == 'Вне базы':
            query.edit_message_text(
                "❌ Вы уже убыли! Сначала отметьте прибытие.",
                reply_markup=main_menu_keyboard(show_admin_button=show_admin)
            )
            return

        timestamp = log_action(user_id, "Убыл", location)
        notify_admins(
            context.bot,
            f"🔴 {full_name} убыл в {location}\n"
            f"⏰ {format_datetime(timestamp)}\n"
            f"👤 TG: [{user.id}](tg://user?id={user.id})"
        )
        query.edit_message_text(
            f"✅ {full_name}, вы отмечены как убывший в {location}",
            reply_markup=main_menu_keyboard(show_admin_button=show_admin)
        )
        context.user_data.pop('location', None)

    elif data == 'history':
        logs = get_user_logs(user_id)
        if not logs:
            query.edit_message_text(
                "📜 У вас пока нет записей в истории действий",
                reply_markup=history_keyboard()
            )
            return

        log_text = "\n".join(
            [f"{format_datetime(log['timestamp'])}: {log['action']} - "
             f"{log['location'] or ''} {log['comment'] or ''}"
             for log in logs]
        )
        query.edit_message_text(
            f"📜 Ваши последние действия:\n{log_text}",
            reply_markup=history_keyboard()
        )

    elif data == 'history_expand':
        logs = get_user_logs(user_id, limit=10)
        log_text = "\n".join(
            [f"{format_datetime(log['timestamp'])}: {log['action']} - "
             f"{log['location'] or ''} {log['comment'] or ''}"
             for log in logs]
        )
        query.edit_message_text(
            f"📜 Ваши последние 10 действий:\n{log_text}",
            reply_markup=history_keyboard(expanded=True)
        )

    elif data == 'history_collapse':
        logs = get_user_logs(user_id)
        log_text = "\n".join(
            [f"{format_datetime(log['timestamp'])}: {log['action']} - "
             f"{log['location'] or ''} {log['comment'] or ''}"
             for log in logs]
        )
        query.edit_message_text(
            f"📜 Ваши последние действия:\n{log_text}",
            reply_markup=history_keyboard()
        )

    elif data == 'admin_panel':
        if is_admin(tg_id):
            query.edit_message_text(
                "👑 Административное меню:",
                reply_markup=admin_menu_keyboard()
            )
        else:
            query.edit_message_text("❌ У вас нет прав администратора!")

    elif data == 'back_main':
        query.edit_message_text(
            f"Главное меню, {full_name}:",
            reply_markup=main_menu_keyboard(show_admin_button=show_admin)
        )

    elif data == 'back':
        query.edit_message_text(
            f"Главное меню, {full_name}:",
            reply_markup=main_menu_keyboard(show_admin_button=show_admin)
        )