# notifications.py

import json
import random
from config import NOTIFICATIONS_JSON

def load_notifications():
    with open(NOTIFICATIONS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def random_bro_phrase():
    """Получить случайную “бро-фразу” для уведомления бойцам."""
    data = load_notifications()
    return random.choice(data["bro_phrases"])

def format_evening_reminder(fio):
    """Формирует личное напоминание бойцу с персональным обращением."""
    phrase = random_bro_phrase()
    return f"👋 <b>{fio}</b>!\n{phrase}"

def format_admin_notify_arrival(fio, tg_id, dt):
    data = load_notifications()
    template = data.get("admin_notify_arrival", "{fio} прибыл.")
    return template.format(fio=fio, tg_id=tg_id, dt=dt)

def format_admin_notify_departure(fio, tg_id, dt, location, comment):
    data = load_notifications()
    template = data.get("admin_notify_departure", "{fio} убыл.")
    return template.format(fio=fio, tg_id=tg_id, dt=dt, location=location, comment=comment)

def format_user_journal(entries, limit=3):
    if not entries:
        return "📋 Нет записей за сегодня."
    text = f"<b>Журнал за день (последние {limit}):</b>\n"
    for row in entries[-limit:]:
        dt, fio, act, loc, comm, uid = row
        line = f"{dt} — <b>{act}</b> ({loc})"
        if comm:
            line += f"\n💬 {comm}"
        text += f"\n{line}"
    return text

def format_profile_view(profile):
    fio = profile.get("fio", "—")
    created = profile.get("created", "—")
    return f"<b>👤 Профиль</b>\nФИО: <b>{fio}</b>\nСоздан: {created}"

def format_profile_edited(new_fio):
    return f"✅ ФИО успешно изменено на: <b>{new_fio}</b>"
def format_user_profile(profile):
    fio = profile.get("fio", "—")
    created = profile.get("created", "—")
    return f"<b>👤 Профиль</b>\nФИО: <b>{fio}</b>\nСоздан: {created}"

def format_admin_summary(summary_text=None):
    data = load_notifications()
    if summary_text:
        return summary_text
    return data.get("admin_summary", "🗂️ Краткая сводка (реализовать авто-группировку по локациям)")

def format_full_journal(logs):
    if not logs:
        return "📋 Журнал пуст."
    text = "<b>Журнал событий:</b>\n"
    for row in logs:
        dt, fio, act, loc, comm, uid = row
        text += f"{dt} — <b>{fio}</b>: {act} ({loc})"
        if comm:
            text += f"\n   💬 {comm}"
        text += "\n"
    return text

def format_export_done():
    return "📤 Экспорт успешно выполнен!"

def format_clear_done():
    return "🧹 Журнал успешно очищен!"
