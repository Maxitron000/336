# handlers_user.py

from telegram import Update
from telegram.ext import CallbackContext
from keyboards import (
    main_menu_keyboard, locations_inline_keyboard, comment_confirm_keyboard,
    journal_keyboard, profile_keyboard
)
from utils import validate_fio, now_str, auto_delete_message
from database import (
    add_log_entry, read_logs, get_status, get_user_profile, update_fio,
    add_user, delete_user
)
from notifications import (
    format_admin_notify_arrival, format_admin_notify_departure,
    format_user_journal, format_profile_view, format_profile_edited
)
from admins import load_admins, is_admin

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    admins = load_admins()
    message = update.message

    # Удаляем /start для чистоты чата
    try:
        if message:
            context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
    except Exception:
        pass

    if not context.user_data.get("fio"):
        instr = context.bot.send_message(
            chat_id=user.id,
            text="👤 Введите свою фамилию и инициалы (пример: Иванов И.И.)"
        )
        context.user_data["state"] = "ASK_FIO"
        auto_delete_message(context, instr, delay=120)
        return

    isadm = is_admin(user.id, admins)
    context.bot.send_message(
        chat_id=user.id,
        text=f"👋 Здравствуйте, {context.user_data.get('fio', user.full_name)}!\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(isadm)
    )
    context.user_data["state"] = "MAIN_MENU"

def ask_fio_handler(update: Update, context: CallbackContext):
    fio = update.message.text.strip()
    if not validate_fio(fio):
        msg = update.message.reply_text(
            "⚠️ ФИО должно содержать только кириллицу, минимум 2 символа.\nПример: Иванов И.И."
        )
        auto_delete_message(context, msg)
        return

    try:
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except Exception:
        pass

    context.user_data["fio"] = fio
    add_user(update.effective_user.id, fio)

    isadm = is_admin(update.effective_user.id, load_admins())
    msg = context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"👋 Здравствуйте, {fio}!\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(isadm)
    )
    context.user_data["state"] = "MAIN_MENU"
    auto_delete_message(context, msg, delay=60)
def profile_handler(update: Update, context: CallbackContext):
    user = update.effective_user
    fio = context.user_data.get("fio", user.full_name)
    profile = get_user_profile(user.id)
    msg = update.message.reply_text(
        format_profile_view(profile),
        reply_markup=profile_keyboard(),
        parse_mode="HTML"
    )
    context.user_data["state"] = "PROFILE"
    auto_delete_message(context, msg, delay=90)

def change_fio_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        "✏️ Введите новое ФИО (пример: Петров П.П.):"
    )
    context.user_data["state"] = "CHANGE_FIO"

def save_new_fio_handler(update: Update, context: CallbackContext):
    fio = update.message.text.strip()
    if not validate_fio(fio):
        msg = update.message.reply_text(
            "⚠️ ФИО должно содержать только кириллицу, минимум 2 символа."
        )
        auto_delete_message(context, msg)
        return

    context.user_data["fio"] = fio
    update_fio(update.effective_user.id, fio)
    msg = update.message.reply_text(
        format_profile_edited(fio),
        reply_markup=profile_keyboard(),
        parse_mode="HTML"
    )
    context.user_data["state"] = "PROFILE"
    auto_delete_message(context, msg, delay=60)

def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user = update.effective_user
    admins = load_admins()
    isadm = is_admin(user.id, admins)
    fio = context.user_data.get("fio", user.full_name)

    if data == "arrive":
        if get_status(user.id) == "В расположении":
            query.answer("Вы уже в расположении!")
            query.edit_message_text("Вы уже в расположении!", reply_markup=main_menu_keyboard(isadm))
        else:
            add_log_entry(fio, "Прибыл", "В расположении", "", user.id)
            query.edit_message_text("🟢 Отметка 'Прибыл' добавлена!", reply_markup=main_menu_keyboard(isadm))
            admin_msg = format_admin_notify_arrival(fio, user.id, now_str())
            context.bot.send_message(MAIN_ADMIN_ID, admin_msg, parse_mode="HTML")

    elif data == "depart":
        if get_status(user.id) == "В расположении":
            query.edit_message_text(
                "🌍 Выберите локацию, куда убыл (только по кнопке ниже):",
                reply_markup=locations_inline_keyboard()
            )
            context.user_data["state"] = "SELECT_LOCATION"
        else:
            query.edit_message_text("⚠️ Сначала отметьте 'Прибыл'!", reply_markup=main_menu_keyboard(isadm))

    elif data.startswith("loc_"):
        context.user_data["location"] = data[4:]
        query.edit_message_text(
            "✍️ Хотите добавить комментарий к отметке?\n"
            "(Пример: Вышел в магазин, приду в 16:00)",
            reply_markup=comment_confirm_keyboard()
        )
        context.user_data["state"] = "ASK_COMMENT"

    elif data == "add_comment":
        query.edit_message_text(
            "Напишите комментарий к отметке (или отправьте 'Пропустить')."
        )
        context.user_data["state"] = "WRITE_COMMENT"

    elif data == "skip_comment":
        return save_departure_inline(update, context, "")

    elif data == "journal":
        entries = read_logs(fio=fio, max_count=3)
        msg = format_user_journal(entries, limit=3)
        query.edit_message_text(msg, reply_markup=journal_keyboard(short=True), parse_mode="HTML")

    elif data == "more_journal":
        entries = read_logs(fio=fio, max_count=10)
        msg = format_user_journal(entries, limit=10)
        query.edit_message_text(msg, reply_markup=journal_keyboard(short=False), parse_mode="HTML")

    elif data == "less_journal":
        entries = read_logs(fio=fio, max_count=3)
        msg = format_user_journal(entries, limit=3)
        query.edit_message_text(msg, reply_markup=journal_keyboard(short=True), parse_mode="HTML")

    elif data == "back_menu":
        query.edit_message_text(
            f"👋 Здравствуйте, {fio}!\n\nВыберите действие:",
            reply_markup=main_menu_keyboard(isadm)
        )

    elif data == "profile":
        profile = get_user_profile(user.id)
        query.edit_message_text(
            format_profile_view(profile),
            reply_markup=profile_keyboard(),
            parse_mode="HTML"
        )
        context.user_data["state"] = "PROFILE"

    elif data == "change_fio":
        query.edit_message_text(
            "✏️ Введите новое ФИО (пример: Петров П.П.):"
        )
        context.user_data["state"] = "CHANGE_FIO"

    elif data == "delete_user":
        delete_user(user.id)
        query.edit_message_text("❌ Ваш профиль удалён. Для работы с ботом потребуется зарегистрироваться заново.")
        context.user_data.clear()

    elif data == "help":
        query.edit_message_text(
            "ℹ️ <b>Памятка по работе с ботом:</b>\n"
            "- Отмечайтесь 'Прибыл' и 'Убыл' только кнопками внизу\n"
            "- Все локации выбирайте только по кнопке\n"
            "- Если требуется, добавляйте комментарий к уходу\n"
            "- Журнал — всегда доступен через меню\n"
            "- Смена ФИО и удаление профиля — в личном профиле\n"
            "Все вопросы — к администратору.",
            reply_markup=main_menu_keyboard(isadm),
            parse_mode="HTML"
        )

def save_departure_inline(update: Update, context: CallbackContext, comment):
    user = update.effective_user
    fio = context.user_data.get("fio", user.full_name)
    location = context.user_data.get("location", "—")
    add_log_entry(fio, "Убыл", location, comment, user.id)
    admin_msg = format_admin_notify_departure(fio, user.id, now_str(), location, comment)
    context.bot.send_message(MAIN_ADMIN_ID, admin_msg, parse_mode="HTML")
    update.callback_query.edit_message_text("🔴 Отметка 'Убыл' добавлена!", reply_markup=main_menu_keyboard(is_admin(user.id, load_admins())))

def message_handler(update: Update, context: CallbackContext):
    state = context.user_data.get("state", "")
    if state == "ASK_FIO":
        return ask_fio_handler(update, context)
    if state == "WRITE_COMMENT":
        comment = update.message.text.strip()
        if comment.lower() == "пропустить":
            return save_departure_inline(update, context, "")
        return save_departure_inline(update, context, comment)
    if state == "CHANGE_FIO":
        return save_new_fio_handler(update, context)
    # fallback — возвращаем меню
    start(update, context)
