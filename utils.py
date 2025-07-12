import re
import os
import json
import pytz
import time
from datetime import datetime

# Устанавливаем часовой пояс Калининграда
KALININGRAD_TZ = pytz.timezone('Europe/Kaliningrad')

# Кэш для защиты от быстрых нажатий
LAST_ACTION_TIME = {}

def is_action_allowed(user_id, action):
    current_time = time.time()
    last_time = LAST_ACTION_TIME.get(user_id, {}).get(action, 0)

    # 3 секунды между действиями
    if current_time - last_time < 3:
        return False

    LAST_ACTION_TIME.setdefault(user_id, {})[action] = current_time
    return True

def validate_full_name(name):
    pattern = r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.[А-ЯЁ]\.$"
    return re.match(pattern, name) is not None

def load_locations():
    try:
        with open('data/locations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return [
            {"id": 1, "emoji": "🏥", "name": "Поликлиника"},
            {"id": 2, "emoji": "⚓", "name": "ОБРМП"},
            {"id": 3, "emoji": "🌆", "name": "Калининград"},
            {"id": 4, "emoji": "🛒", "name": "Магазин"},
            {"id": 5, "emoji": "🍲", "name": "Столовая"},
            {"id": 6, "emoji": "🏨", "name": "Госпиталь"},
            {"id": 7, "emoji": "⚙️", "name": "Рабочка"},
            {"id": 8, "emoji": "🩺", "name": "ВВК"},
            {"id": 9, "emoji": "🏛️", "name": "МФЦ"},
            {"id": 10, "emoji": "🚓", "name": "Патруль"}
        ]

def get_current_time():
    return datetime.now(KALININGRAD_TZ)

def get_today_date():
    return get_current_time().strftime("%Y-%m-%d")

def format_datetime(dt):
    if dt.tzinfo is None:
        dt = KALININGRAD_TZ.localize(dt)
    return dt.strftime("%d.%m.%Y %H:%M")