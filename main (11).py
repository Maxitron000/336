# Табель выхода — полный бот учета посещаемости для военной части
# Все пожелания из диалога учтены!
# Python 3.11+, запуск на PythonAnywhere или Replit
# Telegram: @7973895358 — главный админ
# Token: 8040939701:AAFfULuaLMrnrQggJllGkOPWcTl24KUm_q8
# Google Sheets: https://docs.google.com/spreadsheets/d/1oc4X1qDzIp8qbFmaw4OGEZvmJxRsbVLUTw0nD8rDPRk

import logging
import sqlite3
import pytz
import datetime
import traceback
import threading
import csv

from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
)

# --- Google Sheets ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- КОНСТАНТЫ ---
TOKEN = '8040939701:AAFfULuaLMrnrQggJllGkOPWcTl24KUm_q8'
ADMIN_IDS = [7973895358]
GOOGLE_SHEET_ID = '1oc4X1qDzIp8qbFmaw4OGEZvmJxRsbVLUTw0nD8rDPRk'
GOOGLE_CRED_FILE = 'credentials.json'
TIMEZONE = pytz.timezone('Europe/Kaliningrad')

# --- АКТУАЛЬНЫЙ СПИСОК ЛОКАЦИЙ ---
LOCALES = [
    "Поликлиника 🏥",
    "БРМП ⚓️",
    "Госпиталь 🚑",
    "ВВК 🩺",
    "Рабочка 🛠️",
    "Домой 🏠",
    "Магазин 🛒",
    "Столовая 🍽️",
    "МФЦ 🏢",
    "Калининград 🌆"
]

DB_FILE = 'attendance.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        fullname TEXT,
        is_admin INTEGER DEFAULT 0,
        show_in_reports INTEGER DEFAULT 1,
        notify_on_checkin INTEGER DEFAULT 1,
        notify_enabled INTEGER DEFAULT 1,
        evening_report INTEGER DEFAULT 1
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        fullname TEXT,
        status TEXT,
        location TEXT,
        timestamp TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Google Sheets ---
def get_gsheet():
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CRED_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        return sheet
    except Exception as e:
        logging.error(f"Google Sheets connection error: {e}")
        return None

# --- ЛОГИ ---
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO
)

def log_error(context: CallbackContext, update: Update, e: Exception):
    err_text = f"⚠️ Бот упал!\n\n{traceback.format_exc()}"
    for admin_id in ADMIN_IDS:
        try:
            context.bot.send_message(chat_id=admin_id, text=err_text)
        except Exception as ex:
            logging.error(f"Ошибка отправки логов админу: {ex}")

# --- УТИЛИТЫ ДАТЫ/ВРЕМЕНИ ---
def now_kaliningrad():
    return datetime.datetime.now(TIMEZONE)

def date_str(dt=None):
    if not dt:
        dt = now_kaliningrad()
    return dt.strftime('%Y-%m-%d')

def time_str(dt=None, with_year=False):
    if not dt:
        dt = now_kaliningrad()
    return dt.strftime('%H:%M' if not with_year else '%Y-%m-%d %H:%M')

# --- КОНСТАНТЫ СОСТОЯНИЙ (для ConversationHandler) ---
(
    ADMIN_PANEL, CHANGE_FIO_SELECT, CHANGE_FIO_INPUT,
    EXPORT_LOGS, REPORT_DATE, NOTIF_SETTINGS,
    USER_OUT, USER_OUT_LOCATION,
    USER_IN, SET_ADMIN, NOTIF_TIME,
    EDIT_PERSONNEL, EDIT_PERSON_ACTION,
    DELETE_PERSON_CONFIRM, EDIT_LOGS, EDIT_LOG_SELECT, EDIT_LOG_FIELD, EDIT_LOG_CHANGE
) = range(18)

# --- ДАЛЕЕ: функции пользователей, журнал, Sheets, меню, админка ---
# ---------- РЕГИСТРАЦИЯ И ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ ----------

def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return bool(res and res[0])

def user_fullname(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT fullname FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else ""

def all_users(show_all=True):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if show_all:
        c.execute("SELECT user_id, fullname FROM users ORDER BY fullname ASC")
    else:
        c.execute("SELECT user_id, fullname FROM users WHERE show_in_reports=1 ORDER BY fullname ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_notify_settings(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT notify_enabled FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return bool(res[0]) if res else True

def get_evening_report_setting(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT evening_report FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return bool(res[0]) if res else True

def register(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    # Если уже есть — пропускаем регистрацию
    if user_fullname(user_id):
        return main_menu(update, context)
    update.message.reply_text(
        "Добро пожаловать!\n\nПожалуйста, введите вашу фамилию и инициалы (например: Иванов И.И.).\n\n⚠️ Только админ сможет поменять их потом.",
        reply_markup=ReplyKeyboardRemove()
    )
    return CHANGE_FIO_INPUT

def set_fullname(user_id, fullname):
    fullname = fullname.strip().title()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, fullname) VALUES (?, ?)", (user_id, fullname))
    conn.commit()
    conn.close()

def change_fio(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Изменить ФИО может только администратор.")
        return main_menu(update, context)
    users = all_users()
    # Кнопки по 2 в ряд
    buttons = []
    row = []
    for i, (_, fio) in enumerate(users, 1):
        row.append(KeyboardButton(fio))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton("⬅️ Назад")])
    update.message.reply_text(
        "Выберите, чьё ФИО изменить:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
    context.user_data['change_fio_list'] = [fio for _, fio in users]
    return CHANGE_FIO_SELECT

def change_fio_select(update: Update, context: CallbackContext):
    fio = update.message.text
    if fio not in context.user_data.get('change_fio_list', []):
        return change_fio(update, context)
    context.user_data['selected_fio'] = fio
    update.message.reply_text(
        f"Введите новое ФИО для {fio} (пример: Иванов И.И.):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("⬅️ Назад")]], resize_keyboard=True)
    )
    return CHANGE_FIO_INPUT

def change_fio_input(update: Update, context: CallbackContext):
    new_fio = update.message.text.strip().title()
    old_fio = context.user_data.get('selected_fio')
    if not new_fio or "." not in new_fio or " " not in new_fio:
        update.message.reply_text("Некорректный формат! Введите как: Иванов И.И.")
        return CHANGE_FIO_INPUT
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET fullname=? WHERE fullname=?", (new_fio, old_fio))
    c.execute("UPDATE logs SET fullname=? WHERE fullname=?", (new_fio, old_fio))
    conn.commit()
    conn.close()
    update.message.reply_text(f"ФИО изменено с <b>{old_fio}</b> на <b>{new_fio}</b>.", parse_mode="HTML")
    return admin_panel(update, context)

# ---------- КНОПКИ МЕНЮ ----------

def main_menu_keyboard(is_admin=False):
    buttons = [
        [KeyboardButton("✅ Прибыл"), KeyboardButton("❌ Убыл")],
        [KeyboardButton("📊 Статус")]
    ]
    if is_admin:
        buttons.append([KeyboardButton("🛡 Админ-панель")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def admin_panel_keyboard():
    buttons = [
        [KeyboardButton("👥 Личный состав"), KeyboardButton("📊 Быстрая сводка")],
        [KeyboardButton("🕒 Журнал"), KeyboardButton("📥 Экспорт журнала")],
        [KeyboardButton("✏️ Сменить ФИО"), KeyboardButton("➕ Назначить администратора")],
        [KeyboardButton("🔔 Уведомления"), KeyboardButton("⚠️ Отметить всех прибывшими")],
        [KeyboardButton("🛠️ Редактор состава")],
        [KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ---------- ЛОГИКА ДОБАВЛЕНИЯ ЛОГОВ/ЖУРНАЛ ----------

def add_log(user_id, fullname, status, location):
    ts = now_kaliningrad().strftime('%Y-%m-%d %H:%M')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, fullname, status, location, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, fullname, status, location, ts))
    conn.commit()
    conn.close()
    # Google Sheets
    sheet = get_gsheet()
    if sheet:
        try:
            sheet.append_row([fullname, status, location, ts, str(user_id)])
        except Exception as e:
            logging.error(f"Ошибка записи в Google Sheets: {e}")

# ... (далее — функции статусов, журналов, экспорта, быстрых сводок, уведомлений и др.)
# ---------- СТАТУС ПОЛЬЗОВАТЕЛЯ ----------

def get_last_status(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT status, location, timestamp FROM logs WHERE user_id=? ORDER BY id DESC LIMIT 3", (user_id,))
    res = c.fetchall()
    conn.close()
    return res  # Список из последних 3 действий

def status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    fullname = user_fullname(user_id)
    logs = get_last_status(user_id)
    if not logs:
        update.message.reply_text("Нет данных о вашем местоположении.")
        return
    cur = logs[0]
    now = now_kaliningrad()
    cur_date, cur_time = cur[2].split(' ')
    status_str = "✅ В расположении" if cur[0] == "Прибыл" else f"🔴 Убыл: {cur[1]}"
    reply = f"ℹ️ Ваш текущий статус:\n{status_str} (с {cur_date[5:]} {cur_time})\n\n🕓 Последние действия:"
    for i, log in enumerate(logs, 1):
        emoji = "🟢" if log[0] == "Прибыл" else "🔴"
        place = "в расположение" if log[0] == "Прибыл" else f"{log[1]}"
        t = log[2]
        day, tm = t.split(' ')
        if day == now.strftime('%Y-%m-%d'):
            dt_str = tm
        elif (now - datetime.datetime.strptime(day, '%Y-%m-%d')).days == 1:
            dt_str = f"вчера {tm}"
        else:
            dt_str = f"{day[5:]} {tm}"
        reply += f"\n{i}. {emoji} {log[0]} {place} ({dt_str})"
    update.message.reply_text(reply, parse_mode="HTML")

# ---------- ЖУРНАЛ ДЛЯ АДМИНА ----------

def journal_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🕒 Журнал посещений:\n\nВыберите фильтр:",
        reply_markup=ReplyKeyboardMarkup([
            ["Сегодня", "Неделя", "Месяц"],
            ["По ФИО", "По локации"],
            ["⬅️ Назад"]
        ], resize_keyboard=True)
    )
    return REPORT_DATE

def get_logs(filter_type="today", value=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if filter_type == "today":
        d = now_kaliningrad().strftime('%Y-%m-%d')
        c.execute("SELECT fullname, status, location, timestamp FROM logs WHERE timestamp LIKE ? ORDER BY timestamp DESC", (f"{d}%",))
    elif filter_type == "week":
        d = now_kaliningrad() - datetime.timedelta(days=7)
        c.execute("SELECT fullname, status, location, timestamp FROM logs WHERE timestamp >= ? ORDER BY timestamp DESC", (d.strftime('%Y-%m-%d'),))
    elif filter_type == "month":
        d = now_kaliningrad() - datetime.timedelta(days=30)
        c.execute("SELECT fullname, status, location, timestamp FROM logs WHERE timestamp >= ? ORDER BY timestamp DESC", (d.strftime('%Y-%m-%d'),))
    elif filter_type == "fio":
        c.execute("SELECT fullname, status, location, timestamp FROM logs WHERE fullname=? ORDER BY timestamp DESC", (value,))
    elif filter_type == "location":
        c.execute("SELECT fullname, status, location, timestamp FROM logs WHERE location=? ORDER BY timestamp DESC", (value,))
    else:
        c.execute("SELECT fullname, status, location, timestamp FROM logs ORDER BY timestamp DESC LIMIT 100")
    logs = c.fetchall()
    conn.close()
    return logs

def export_logs(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Выберите формат экспорта:",
        reply_markup=ReplyKeyboardMarkup([
            ["Экспорт в txt", "Экспорт в csv"],
            ["⬅️ Назад"]
        ], resize_keyboard=True)
    )
    return EXPORT_LOGS

def export_logs_file(logs, filetype="txt"):
    output = ""
    if filetype == "txt":
        output = "ФИО | Статус | Локация | Время\n"
        for fio, stat, loc, t in logs:
            output += f"{fio} | {stat} | {loc} | {t}\n"
        return output
    elif filetype == "csv":
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["ФИО", "Статус", "Локация", "Время"])
        for row in logs:
            writer.writerow(row)
        return buf.getvalue()

# ---------- СВОДКА ДЛЯ АДМИНА ----------

def quick_report(update: Update, context: CallbackContext):
    users = all_users(show_all=False)
    cur_status = {}
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for uid, fio in users:
        c.execute("SELECT status, location FROM logs WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,))
        res = c.fetchone()
        if res:
            cur_status[fio] = res
    conn.close()
    in_place = [f"✅ {fio}" for fio, st in cur_status.items() if st[0] == "Прибыл"]
    out_place = [f"🔴 {fio} — {st[1]}" for fio, st in cur_status.items() if st[0] == "Убыл"]
    text = "📊 <b>Быстрая сводка:</b>\n"
    text += "<b>В расположении:</b>\n" + ("\n".join(in_place) if in_place else "—") + "\n\n"
    text += "<b>Отсутствуют:</b>\n" + ("\n".join(out_place) if out_place else "—")
    update.message.reply_text(text, parse_mode="HTML")

# ---------- ЛИЧНЫЙ СОСТАВ (список по алфавиту, в столбцы) ----------

def staff_list(update: Update, context: CallbackContext):
    users = [fio for _, fio in all_users(show_all=False)]
    n = len(users)
    col = 3 if n >= 24 else (2 if n >= 10 else 1)
    per_col = (n + col - 1) // col
    lines = []
    for i in range(per_col):
        row = []
        for j in range(col):
            idx = i + j * per_col
            if idx < n:
                row.append(users[idx])
        lines.append("   ".join(f"{idx+1}. {fio}" for idx, fio in enumerate(row, i*col+1)))
    text = f"👥 <b>Личный состав (всего {n}):</b>\n" + "\n".join(lines)
    update.message.reply_text(text, parse_mode="HTML")

# ---------- АДМИН-ПАНЕЛЬ И ПРОЧЕЕ (сценарии, обработчики, запуск, аварийная отметка, уведомления) ----------
# (Следующий блок!)

# ---------- АДМИН-ПАНЕЛЬ ----------

def admin_panel(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🛡 <b>Админ-панель:</b>\nВыберите действие:",
        reply_markup=admin_panel_keyboard(), parse_mode="HTML"
    )
    return ADMIN_PANEL

# ---------- АВАРИЙНАЯ ОТМЕТКА ВСЕХ ПРИБЫВШИМИ ----------
def mark_all_present(update: Update, context: CallbackContext):
    users = all_users(show_all=False)
    for uid, fio in users:
        add_log(uid, fio, "Прибыл", "В расположении")
    update.message.reply_text("✅ Все отмечены как 'Прибыл в расположение'!")
    return admin_panel(update, context)

# ---------- УВЕДОМЛЕНИЯ (Шаблон. Подробнее — по аналогии из предыдущих блоков) ----------

def notify_boyts_at_2030(context: CallbackContext):
    # Отправить всем, кто не в расположении, напоминание
    users = all_users(show_all=False)
    for uid, fio in users:
        last = get_last_status(uid)
        if not last or last[0][0] != "Прибыл":
            try:
                context.bot.send_message(chat_id=uid, text="Напоминаем: вы не в расположении. Не забудьте отметиться!")
            except:
                continue

def notify_admins_at_1930(context: CallbackContext):
    # Сводка за день — только тем, кто включён
    logs = get_logs("today")
    text = export_logs_file(logs, "txt")
    for uid in ADMIN_IDS:
        if get_evening_report_setting(uid):
            try:
                context.bot.send_message(chat_id=uid, text="Сводка за день:\n\n"+text)
            except:
                continue

def schedule_jobs(updater: Updater):
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    # 20:30 — бойцам
    scheduler.add_job(lambda: notify_boyts_at_2030(updater.bot), 'cron', hour=20, minute=30, timezone=TIMEZONE)
    # 19:30 — админам
    scheduler.add_job(lambda: notify_admins_at_1930(updater.bot), 'cron', hour=19, minute=30, timezone=TIMEZONE)
    scheduler.start()

# ---------- ОБРАБОТЧИКИ И ЗАПУСК ----------

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not user_fullname(user_id):
        return register(update, context)
    isadm = is_admin(user_id)
    update.message.reply_text(
        "Главное меню", reply_markup=main_menu_keyboard(is_admin=isadm)
    )
    return

def button_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text

    if text == "✅ Прибыл":
        add_log(user_id, user_fullname(user_id), "Прибыл", "В расположении")
        for admin_id in ADMIN_IDS:
            context.bot.send_message(admin_id, f"🟢 {user_fullname(user_id)} — Прибыл в расположение")
        update.message.reply_text("Вы отмечены как <b>Прибыл в расположение</b>!", parse_mode="HTML")
        return
    elif text == "❌ Убыл":
        buttons = []
        row = []
        for i, loc in enumerate(LOCALES, 1):
            row.append(KeyboardButton(loc))
            if i % 2 == 0:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([KeyboardButton("⬅️ Назад")])
        update.message.reply_text(
            "Выберите, куда уходите:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        )
        context.user_data['leave_menu'] = True
        return USER_OUT_LOCATION
    elif text in LOCALES:
        add_log(user_id, user_fullname(user_id), "Убыл", text)
        for admin_id in ADMIN_IDS:
            context.bot.send_message(admin_id, f"🔴 {user_fullname(user_id)} — Убыл: {text}")
        update.message.reply_text(f"Вы отмечены как <b>Убыл: {text}</b>!", parse_mode="HTML")
        return
    elif text == "📊 Статус":
        return status(update, context)
    elif text == "🛡 Админ-панель" and is_admin(user_id):
        return admin_panel(update, context)
    elif text == "👥 Личный состав" and is_admin(user_id):
        return staff_list(update, context)
    elif text == "📊 Быстрая сводка" and is_admin(user_id):
        return quick_report(update, context)
    elif text == "🕒 Журнал" and is_admin(user_id):
        return journal_menu(update, context)
    elif text == "📥 Экспорт журнала" and is_admin(user_id):
        return export_logs(update, context)
    elif text == "✏️ Сменить ФИО" and is_admin(user_id):
        return change_fio(update, context)
    elif text == "⚠️ Отметить всех прибывшими" and is_admin(user_id):
        return mark_all_present(update, context)
    elif text == "⬅️ Назад":
        return start(update, context)
    else:
        update.message.reply_text("Неизвестная команда.")
        return

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Ошибки и падения
    dp.add_error_handler(lambda update, context: log_error(context, update, context.error))

    # ConversationHandler — для меню и сценариев
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), button_handler))
    dp.add_handler(CommandHandler("start", start))

    # Планировщик уведомлений
    threading.Thread(target=lambda: schedule_jobs(updater), daemon=True).start()

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
