# admins.py

import json
import os
from config import ADMINS_JSON, ADMIN_RIGHTS

def load_admins():
    """Загрузить всех админов из файла"""
    if not os.path.exists(ADMINS_JSON):
        with open(ADMINS_JSON, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(ADMINS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def save_admins(admins):
    with open(ADMINS_JSON, "w", encoding="utf-8") as f:
        json.dump(admins, f, ensure_ascii=False, indent=2)

def is_admin(tg_id, admins=None):
    if admins is None:
        admins = load_admins()
    return str(tg_id) in admins

def add_admin(tg_id, fio="(без ФИО)"):
    admins = load_admins()
    if str(tg_id) not in admins:
        admins[str(tg_id)] = {
            "fio": fio,
            "rights": [code for code, _, _ in ADMIN_RIGHTS]  # По умолчанию все права
        }
        save_admins(admins)

def delete_admin(tg_id):
    admins = load_admins()
    admins.pop(str(tg_id), None)
    save_admins(admins)

def get_admin_rights(tg_id):
    admins = load_admins()
    return admins.get(str(tg_id), {}).get("rights", [])

def set_admin_rights(tg_id, rights):
    admins = load_admins()
    if str(tg_id) in admins:
        admins[str(tg_id)]["rights"] = rights
        save_admins(admins)

def list_admins():
    admins = load_admins()
    return [
        f'<a href="tg://user?id={tid}">{data.get("fio", tid)}</a> — {tid}'
        for tid, data in admins.items()
    ]

def user_has_right(tg_id, right_code):
    rights = get_admin_rights(tg_id)
    return right_code in rights
