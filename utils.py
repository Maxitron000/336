import re
import os
import json
import pytz
import time
from datetime import datetime

# Настройка часового пояса (можно изменить в .env файле)
import os
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Kaliningrad')
KALININGRAD_TZ = pytz.timezone(TIMEZONE)

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
    """Загружает локации из JSON файла"""
    try:
        with open('data/locations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Создаем файл с локациями по умолчанию, если его нет
        default_locations = [
            {"id": 1, "emoji": "🏥", "name": "Поликлиника", "description": "Медицинское учреждение"},
            {"id": 2, "emoji": "⚓", "name": "ОБРМП", "description": "Отдельная бригада морской пехоты"},
            {"id": 3, "emoji": "🌆", "name": "Калининград", "description": "Город"},
            {"id": 4, "emoji": "🛒", "name": "Магазин", "description": "Торговые точки"},
            {"id": 5, "emoji": "🍲", "name": "Столовая", "description": "Место питания"},
            {"id": 6, "emoji": "🏨", "name": "Госпиталь", "description": "Военный госпиталь"},
            {"id": 7, "emoji": "⚙️", "name": "Рабочка", "description": "Рабочее место, мастерские"},
            {"id": 8, "emoji": "🩺", "name": "ВВК", "description": "Военно-врачебная комиссия"},
            {"id": 9, "emoji": "🏛️", "name": "МФЦ", "description": "Многофункциональный центр"},
            {"id": 10, "emoji": "🚓", "name": "Патруль", "description": "Патрульная служба"}
        ]
        
        # Создаем папку data, если её нет
        os.makedirs('data', exist_ok=True)
        
        # Сохраняем локации в файл
        with open('data/locations.json', 'w', encoding='utf-8') as f:
            json.dump(default_locations, f, ensure_ascii=False, indent=2)
        
        return default_locations

def get_current_time():
    return datetime.now(KALININGRAD_TZ)

def get_today_date():
    return get_current_time().strftime("%Y-%m-%d")

def format_datetime(dt):
    if dt.tzinfo is None:
        dt = KALININGRAD_TZ.localize(dt)
    return dt.strftime("%d.%m.%Y %H:%M")