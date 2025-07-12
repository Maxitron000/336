# database.py

import os
import csv
import json
from datetime import datetime
from config import LOGS_FOLDER, USERS_JSON, LOGS_PAGE_SIZE, EXPORT_FOLDER

def ensure_dirs():
    """Создать все нужные папки при первом запуске."""
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    os.makedirs(EXPORT_FOLDER, exist_ok=True)
    if not os.path.exists(USERS_JSON):
        with open(USERS_JSON, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)

# --- Работа с пользователями ---

def load_users():
    if not os.path.exists(USERS_JSON):
        return {}
    with open(USERS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_JSON, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def add_user(user_id, fio):
    users = load_users()
    if user_id is None:
        user_id = max([int(uid) for uid in users.keys()] + [0]) + 1
    users[str(user_id)] = {"fio": fio, "created": now_str()}
    save_users(users)
    return user_id

def update_fio(user_id, new_fio):
    users = load_users()
    users[str(user_id)]["fio"] = new_fio
    save_users(users)

def delete_user(user_id):
    users = load_users()
    users.pop(str(user_id), None)
    save_users(users)

def get_user_profile(user_id):
    users = load_users()
    return users.get(str(user_id), {"fio": "Не найден"})

def get_all_users():
    users = load_users()
    return [{"id": k, "fio": v["fio"], "created": v.get("created")} for k, v in users.items()]

# --- Журнал ---

def logs_path_for_today():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOGS_FOLDER, f"{today}.csv")

def add_log_entry(fio, action, location, comment, user_id):
    ensure_dirs()
    row = [now_str(), fio, action, location, comment, user_id]
    file_path = logs_path_for_today()
    with open(file_path, "a", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def read_logs(fio=None, max_count=100):
    file_path = logs_path_for_today()
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if fio:
        rows = [row for row in rows if row[1] == fio]
    return rows[-max_count:]

def clear_logs():
    file_path = logs_path_for_today()
    if os.path.exists(file_path):
        os.remove(file_path)

def get_status(user_id):
    file_path = logs_path_for_today()
    if not os.path.exists(file_path):
        return "В расположении"
    with open(file_path, "r", encoding="utf-8") as f:
        logs = list(csv.reader(f))
    logs = [log for log in logs if log[5] == str(user_id)]
    if not logs:
        return "В расположении"
    last = logs[-1]
    return "В расположении" if last[2] == "Прибыл" else f"Убыл ({last[3]})"

# --- Экспорт журнала ---

def export_logs(fmt="csv"):
    file_path = logs_path_for_today()
    if not os.path.exists(file_path):
        return None
    export_name = f"export_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.{fmt}"
    export_path = os.path.join(EXPORT_FOLDER, export_name)
    if fmt == "csv":
        import shutil
        shutil.copyfile(file_path, export_path)
    elif fmt == "xlsx":
        import pandas as pd
        df = pd.read_csv(file_path, names=["Время", "ФИО", "Действие", "Локация", "Комментарий", "ID"])
        df.to_excel(export_path, index=False)
    elif fmt == "pdf":
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Журнал событий", ln=True, align="C")
        with open(file_path, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                pdf.cell(0, 8, " | ".join(row), ln=True)
        pdf.output(export_path)
    return export_path

# --- Инициализация при запуске ---

ensure_dirs()
