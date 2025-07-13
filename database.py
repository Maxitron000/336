import sqlite3
import os
import logging
from utils import get_current_time

DB_NAME = "data/personnel.db"

def init_db():
    # Создаем папку data, если её нет
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        status TEXT DEFAULT 'unknown',
        location TEXT DEFAULT '',
        last_action TIMESTAMP,
        is_admin BOOLEAN DEFAULT FALSE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        location TEXT,
        comment TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE NOT NULL,
        permissions TEXT DEFAULT 'view,export'
    )
    ''')

    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        try:
            admin_id = int(admin_id)
            cursor.execute('''
            INSERT OR IGNORE INTO admins (tg_id, permissions)
            VALUES (?, ?)
            ''', (admin_id, "full"))

            cursor.execute('''
            INSERT OR IGNORE INTO users (tg_id, full_name, is_admin)
            VALUES (?, ?, ?)
            ''', (admin_id, f"Admin-{admin_id}", True))
        except ValueError:
            logging.error("Некорректный формат ADMIN_ID!")

    conn.commit()
    conn.close()
    logging.info("База данных инициализирована")

def get_user(tg_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(tg_id, full_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO users (tg_id, full_name)
        VALUES (?, ?)
        ''', (tg_id, full_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def log_action(user_id, action, location=None, comment=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    current_time = get_current_time()

    cursor.execute('''
    INSERT INTO logs (user_id, action, location, comment, timestamp)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, action, location, comment, current_time))

    if action == "Прибыл":
        cursor.execute('''
        UPDATE users SET status = 'В расположении', location = 'База', last_action = ?
        WHERE id = ?
        ''', (current_time, user_id))
    elif action == "Убыл":
        cursor.execute('''
        UPDATE users SET status = 'Вне базы', location = ?, last_action = ?
        WHERE id = ?
        ''', (location, current_time, user_id))

    conn.commit()
    conn.close()
    return current_time

def get_user_logs(user_id, limit=3):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
    SELECT action, location, comment, timestamp
    FROM logs
    WHERE user_id = ?
    ORDER BY timestamp DESC
    LIMIT ?
    ''', (user_id, limit))

    logs = cursor.fetchall()
    conn.close()
    return logs

def get_all_logs(date=None):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if date:
        cursor.execute('''
        SELECT u.full_name, l.action, l.location, l.comment, l.timestamp
        FROM logs l
        JOIN users u ON l.user_id = u.id
        WHERE DATE(l.timestamp) = ?
        ORDER BY l.timestamp DESC
        ''', (date,))
    else:
        cursor.execute('''
        SELECT u.full_name, l.action, l.location, l.comment, l.timestamp
        FROM logs l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.timestamp DESC
        ''')

    logs = cursor.fetchall()
    conn.close()
    return logs

def is_admin(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admins WHERE tg_id = ?", (tg_id,))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def get_all_admins():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins")
    admins = cursor.fetchall()
    conn.close()
    return admins

def get_daily_stats(date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT location, COUNT(*) as count
    FROM logs
    WHERE DATE(timestamp) = ? AND action = 'Убыл'
    GROUP BY location
    ''', (date,))

    stats = cursor.fetchall()
    conn.close()
    return stats

def add_user(full_name, tg_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        if tg_id:
            cursor.execute('''
            INSERT INTO users (tg_id, full_name)
            VALUES (?, ?)
            ''', (tg_id, full_name))
        else:
            cursor.execute('''
            INSERT INTO users (full_name)
            VALUES (?)
            ''', (full_name,))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    cursor.execute("DELETE FROM logs WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

def clear_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM logs")

    conn.commit()
    conn.close()