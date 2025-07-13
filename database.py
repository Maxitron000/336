"""
База данных для бота учета персонала
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pytz
from utils import get_timezone

DB_PATH = os.getenv('DB_PATH', 'data/personnel.db')

def init_db():
    """Инициализация базы данных"""
    # Создаем директорию если её нет
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей с системой ролей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            username TEXT,
            role TEXT DEFAULT 'soldier' CHECK (role IN ('soldier', 'admin', 'main_admin')),
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Добавляем колонку role если её нет (для обратной совместимости)
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'role' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "soldier"')
        # Обновляем существующих админов
        cursor.execute('UPDATE users SET role = "admin" WHERE is_admin = 1')
    
    # Добавляем колонку is_admin если её нет (для обратной совместимости)
    if 'is_admin' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
        cursor.execute('UPDATE users SET is_admin = 1 WHERE role IN ("admin", "main_admin")')
    
    # Таблица записей о местоположении
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS location_logs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            location TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица активных сессий (кто где сейчас находится)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            location TEXT NOT NULL,
            entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица админских операций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY,
            admin_id INTEGER,
            action TEXT NOT NULL,
            target_user_id INTEGER,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users (id),
            FOREIGN KEY (target_user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def close_db():
    """Закрытие соединения с базой данных"""
    pass  # SQLite не требует явного закрытия

# Функции для работы с пользователями
def add_user(telegram_id: int, full_name: str, username: str = None, role: str = 'soldier') -> bool:
    """Добавление нового пользователя с ролью"""
    if role not in ['soldier', 'admin', 'main_admin']:
        role = 'soldier'
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Определяем статус админа
        is_admin = 1 if role in ['admin', 'main_admin'] else 0
        
        cursor.execute('''
            INSERT INTO users (telegram_id, full_name, username, role, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, full_name, username, role, is_admin))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получение пользователя по telegram_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None

def get_all_users() -> List[Dict[str, Any]]:
    """Получение всех пользователей"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users ORDER BY full_name')
    users = cursor.fetchall()
    
    conn.close()
    return [dict(user) for user in users]

def update_user_activity(telegram_id: int):
    """Обновление времени последней активности пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET last_activity = CURRENT_TIMESTAMP 
        WHERE telegram_id = ?
    ''', (telegram_id,))
    
    conn.commit()
    conn.close()

def set_user_role(telegram_id: int, role: str) -> bool:
    """Установка роли пользователя (soldier, admin, main_admin)"""
    if role not in ['soldier', 'admin', 'main_admin']:
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновляем роль и статус админа
        is_admin = 1 if role in ['admin', 'main_admin'] else 0
        
        cursor.execute('''
            UPDATE users 
            SET role = ?, is_admin = ?
            WHERE telegram_id = ?
        ''', (role, is_admin, telegram_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_user_role(telegram_id: int) -> str:
    """Получение роли пользователя"""
    user = get_user(telegram_id)
    if user:
        return user.get('role', 'soldier')
    return 'soldier'

def is_main_admin(telegram_id: int) -> bool:
    """Проверка является ли пользователь главным админом"""
    return get_user_role(telegram_id) == 'main_admin'

def is_admin_or_main_admin(telegram_id: int) -> bool:
    """Проверка является ли пользователь админом или главным админом"""
    role = get_user_role(telegram_id)
    return role in ['admin', 'main_admin']

def get_all_admins() -> List[Dict[str, Any]]:
    """Получение всех админов и главных админов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users 
        WHERE role IN ('admin', 'main_admin') 
        ORDER BY role DESC, full_name
    ''')
    admins = cursor.fetchall()
    
    conn.close()
    return [dict(admin) for admin in admins]

def get_main_admins() -> List[Dict[str, Any]]:
    """Получение всех главных админов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users 
        WHERE role = 'main_admin' 
        ORDER BY full_name
    ''')
    main_admins = cursor.fetchall()
    
    conn.close()
    return [dict(admin) for admin in main_admins]

def delete_user(telegram_id: int) -> bool:
    """Удаление пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем user_id
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        
        if not user:
            return False
        
        user_id = user['id']
        
        # Удаляем связанные записи
        cursor.execute('DELETE FROM location_logs WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM active_sessions WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM admin_logs WHERE target_user_id = ?', (user_id,))
        
        # Удаляем пользователя
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# Функции для работы с записями местоположения
def add_location_log(telegram_id: int, location: str, action: str) -> bool:
    """Добавление записи о местоположении"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем user_id
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        
        if not user:
            return False
        
        user_id = user['id']
        
        # Добавляем запись
        cursor.execute('''
            INSERT INTO location_logs (user_id, location, action)
            VALUES (?, ?, ?)
        ''', (user_id, location, action))
        
        # Обновляем активную сессию
        if action == 'arrived':
            # Удаляем предыдущую активную сессию
            cursor.execute('DELETE FROM active_sessions WHERE user_id = ?', (user_id,))
            # Добавляем новую активную сессию
            cursor.execute('''
                INSERT INTO active_sessions (user_id, location)
                VALUES (?, ?)
            ''', (user_id, location))
        elif action == 'left':
            # Удаляем активную сессию
            cursor.execute('DELETE FROM active_sessions WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_user_current_location(telegram_id: int) -> Optional[str]:
    """Получение текущего местоположения пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT location FROM active_sessions 
        WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)
    ''', (telegram_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['location'] if result else None

def get_location_logs(limit: int = 100, user_filter: str = None, date_filter: str = None) -> List[Dict[str, Any]]:
    """Получение логов местоположения с фильтрами"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT l.*, u.full_name, u.telegram_id
        FROM location_logs l
        JOIN users u ON l.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if user_filter:
        query += ' AND u.full_name LIKE ?'
        params.append(f'%{user_filter}%')
    
    if date_filter:
        query += ' AND DATE(l.timestamp) = ?'
        params.append(date_filter)
    
    query += ' ORDER BY l.timestamp DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    conn.close()
    return [dict(log) for log in logs]

def get_user_location_history(telegram_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Получение истории местоположений пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM location_logs 
        WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)
        AND timestamp >= datetime('now', '-{} days')
        ORDER BY timestamp DESC
    '''.format(days), (telegram_id,))
    
    logs = cursor.fetchall()
    conn.close()
    
    return [dict(log) for log in logs]

def get_active_users_by_location() -> Dict[str, List[Dict[str, Any]]]:
    """Получение активных пользователей по локациям"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.location, u.full_name, u.telegram_id, s.entered_at
        FROM active_sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.location, u.full_name
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    locations = {}
    for result in results:
        location = result['location']
        if location not in locations:
            locations[location] = []
        locations[location].append(dict(result))
    
    return locations

def get_users_without_location() -> List[Dict[str, Any]]:
    """Получение пользователей, которые не указали местоположение"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.* FROM users u
        LEFT JOIN active_sessions s ON u.id = s.user_id
        WHERE s.id IS NULL
        ORDER BY u.full_name
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    return [dict(user) for user in users]

# Функции для работы с админскими операциями
def add_admin_log(admin_id: int, action: str, target_user_id: int = None, details: str = None):
    """Добавление записи об административной операции"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, action, target_user_id, details))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_admin_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Получение логов административных операций"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT l.*, u1.full_name as admin_name, u2.full_name as target_name
        FROM admin_logs l
        JOIN users u1 ON l.admin_id = u1.id
        LEFT JOIN users u2 ON l.target_user_id = u2.id
        ORDER BY l.timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    logs = cursor.fetchall()
    conn.close()
    
    return [dict(log) for log in logs]

# Функции для очистки данных
def clear_location_logs(period: str = 'all') -> int:
    """Очистка логов местоположений"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if period == 'day':
        cursor.execute('''
            DELETE FROM location_logs 
            WHERE timestamp < datetime('now', '-1 day')
        ''')
    elif period == 'week':
        cursor.execute('''
            DELETE FROM location_logs 
            WHERE timestamp < datetime('now', '-7 days')
        ''')
    elif period == 'month':
        cursor.execute('''
            DELETE FROM location_logs 
            WHERE timestamp < datetime('now', '-30 days')
        ''')
    elif period == 'all':
        cursor.execute('DELETE FROM location_logs')
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count

def clear_admin_logs(period: str = 'all') -> int:
    """Очистка логов административных операций"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if period == 'day':
        cursor.execute('''
            DELETE FROM admin_logs 
            WHERE timestamp < datetime('now', '-1 day')
        ''')
    elif period == 'week':
        cursor.execute('''
            DELETE FROM admin_logs 
            WHERE timestamp < datetime('now', '-7 days')
        ''')
    elif period == 'month':
        cursor.execute('''
            DELETE FROM admin_logs 
            WHERE timestamp < datetime('now', '-30 days')
        ''')
    elif period == 'all':
        cursor.execute('DELETE FROM admin_logs')
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count

def clear_all_locations() -> int:
    """Очистка всех активных местоположений (все покинули)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем всех пользователей с активными сессиями
    cursor.execute('''
        SELECT s.user_id, u.telegram_id, s.location
        FROM active_sessions s
        JOIN users u ON s.user_id = u.id
    ''')
    
    active_users = cursor.fetchall()
    
    # Добавляем записи о выходе для всех
    for user in active_users:
        cursor.execute('''
            INSERT INTO location_logs (user_id, location, action)
            VALUES (?, ?, 'left')
        ''', (user['user_id'], user['location']))
    
    # Очищаем активные сессии
    cursor.execute('DELETE FROM active_sessions')
    
    count = len(active_users)
    conn.commit()
    conn.close()
    
    return count

def mark_all_as_arrived(location: str) -> int:
    """Отметить всех пользователей как прибывших в определенное место"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем всех пользователей
    cursor.execute('SELECT id, telegram_id FROM users')
    all_users = cursor.fetchall()
    
    count = 0
    for user in all_users:
        user_id = user['id']
        
        # Удаляем предыдущую активную сессию
        cursor.execute('DELETE FROM active_sessions WHERE user_id = ?', (user_id,))
        
        # Добавляем новую активную сессию
        cursor.execute('''
            INSERT INTO active_sessions (user_id, location)
            VALUES (?, ?)
        ''', (user_id, location))
        
        # Добавляем запись в лог
        cursor.execute('''
            INSERT INTO location_logs (user_id, location, action)
            VALUES (?, ?, 'arrived')
        ''', (user_id, location))
        
        count += 1
    
    conn.commit()
    conn.close()
    
    return count

def get_database_stats() -> Dict[str, int]:
    """Получение статистики базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Количество пользователей
    cursor.execute('SELECT COUNT(*) FROM users')
    stats['users'] = cursor.fetchone()[0]
    
    # Количество админов
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
    stats['admins'] = cursor.fetchone()[0]
    
    # Количество записей в логах
    cursor.execute('SELECT COUNT(*) FROM location_logs')
    stats['location_logs'] = cursor.fetchone()[0]
    
    # Количество активных сессий
    cursor.execute('SELECT COUNT(*) FROM active_sessions')
    stats['active_sessions'] = cursor.fetchone()[0]
    
    # Количество админских логов
    cursor.execute('SELECT COUNT(*) FROM admin_logs')
    stats['admin_logs'] = cursor.fetchone()[0]
    
    conn.close()
    return stats