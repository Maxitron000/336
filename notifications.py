import json
import random
from telegram import Bot, ParseMode
from telegram.ext import JobQueue, CallbackContext
from datetime import time
import pytz
from database import get_all_users, get_all_admins, get_daily_stats
from utils import get_today_date, format_datetime, KALININGRAD_TZ

def load_notification_templates():
    try:
        with open('config/notifications.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "reminders": [
                "Бро, не забудь отметиться! 🤙",
                "Эй, воин! Пора отметить прибытие! 💪",
                "Привет! Ждем твою отметку о прибытии 😉",
                "Не забыл отметиться? Давай быстрее! ⏱️",
                "Твой статус еще не обновлен, дружище! 🔄"
            ],
            "arrival_template": "🟢 {name} прибыл в расположение\n⏰ {time}\n👤 TG: [{tg_id}](tg://user?id={tg_id})",
            "departure_template": "🔴 {name} убыл в {location}\n⏰ {time}\n👤 TG: [{tg_id}](tg://user?id={tg_id})"
        }

def notify_admins(bot: Bot, message: str):
    admins = get_all_admins()
    for admin in admins:
        try:
            bot.send_message(
                chat_id=admin['tg_id'],
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления админу {admin['tg_id']}: {e}")

def setup_notifications(job_queue: JobQueue):
    templates = load_notification_templates()

    job_queue.run_daily(
        send_evening_reminder,
        time=time(20, 30, tzinfo=KALININGRAD_TZ),
        context=templates,
        name="evening_reminder"
    )

    job_queue.run_daily(
        send_daily_summary,
        time=time(19, 0, tzinfo=KALININGRAD_TZ),
        context=templates,
        name="daily_summary"
    )

def send_evening_reminder(context: CallbackContext):
    templates = context.job.context
    reminders = templates.get("reminders", [])
    if not reminders:
        return

    message = random.choice(reminders)
    users = get_all_users()

    for user in users:
        if user['status'] != 'В расположении':
            try:
                context.bot.send_message(
                    chat_id=user['tg_id'],
                    text=message
                )
            except Exception as e:
                print(f"Ошибка отправки напоминания {user['tg_id']}: {e}")

def send_daily_summary(context: CallbackContext):
    templates = context.job.context
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

    admins = get_all_admins()
    for admin in admins:
        try:
            context.bot.send_message(
                chat_id=admin['tg_id'],
                text=summary
            )
        except Exception as e:
            print(f"Ошибка отправки сводки админу {admin['tg_id']}: {e}")