# utils.py
import os
import re
import pytz
from datetime import datetime, timedelta
from config import TIMEZONE

def now_str():
    return datetime.now().strftime('%d.%m.%Y %H:%M')

def validate_fio(fio: str) -> bool:
    """Валидация ФИО — только кириллица, минимум две буквы, формат 'Иванов И.И.' или 'Иванов Иван'."""
    fio = fio.strip()
    # Русские буквы, пробелы, точки
    pattern = r'^[А-ЯЁ][а-яё]+(\s[А-ЯЁ]\.[А-ЯЁ]\.|(\s[А-ЯЁ][а-яё]+){1,2})$'
    return bool(re.match(pattern, fio))
def ensure_dirs():
    """Создаёт все нужные папки для бота."""
    for folder in ["logs", "exports"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
def now_str(fmt='%d.%m.%Y %H:%M'):
    """Текущее время по Калининграду (или твоему TZ) в строке."""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).strftime(fmt)

def auto_delete_message(context, message, delay=30):
    """Автоматически удаляет сообщение через delay секунд."""
    if not message:
        return
    chat_id = message.chat_id
    message_id = message.message_id

    def delete_later(context):
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass

    context.job_queue.run_once(delete_later, delay)

def days_ago(n):
    """Дата n дней назад (используется для фильтрации журналов)."""
    tz = pytz.timezone(TIMEZONE)
    return (datetime.now(tz) - timedelta(days=n)).date()

def format_tg_id(tg_id):
    """Кликабельный Telegram ID."""
    return f'<a href="tg://user?id={tg_id}">{tg_id}</a>'

def plural(num, singular, plural):
    """Корректное склонение по числу."""
    return singular if num == 1 else plural

def gen_user_id():
    """Генерация уникального ID для бойца (если нет Telegram)."""
    return int(datetime.now().timestamp() * 1000000)

def is_valid_time(val):
    """Проверка времени формата HH:MM."""
    try:
        h, m = map(int, val.split(":"))
        return 0 <= h < 24 and 0 <= m < 60
    except Exception:
        return False
