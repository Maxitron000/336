#!/usr/bin/env python3
"""
Полезные инструменты для управления ботом
"""

import os
import sqlite3
import json
import argparse
from datetime import datetime, timedelta
from database import DB_NAME, init_db
from utils import load_locations, format_datetime

def backup_database():
    """Создает резервную копию базы данных"""
    if not os.path.exists(DB_NAME):
        print("❌ База данных не найдена!")
        return
    
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/personnel_backup_{timestamp}.db"
    
    import shutil
    shutil.copy2(DB_NAME, backup_file)
    print(f"✅ Резервная копия создана: {backup_file}")

def show_statistics():
    """Показывает статистику по боту"""
    if not os.path.exists(DB_NAME):
        print("❌ База данных не найдена!")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    admin_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM logs")
    total_actions = cursor.fetchone()[0]
    
    # Статистика за сегодня
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM logs WHERE DATE(timestamp) = ?", (today,))
    today_actions = cursor.fetchone()[0]
    
    # Статистика по статусам
    cursor.execute("SELECT status, COUNT(*) FROM users GROUP BY status")
    status_stats = cursor.fetchall()
    
    print("📊 Статистика бота")
    print("=" * 50)
    print(f"👥 Всего пользователей: {total_users}")
    print(f"👑 Администраторов: {admin_users}")
    print(f"📝 Всего действий: {total_actions}")
    print(f"📅 Действий сегодня: {today_actions}")
    print("\n📍 Статусы пользователей:")
    for status, count in status_stats:
        print(f"   {status}: {count}")
    
    conn.close()

def clean_old_logs(days=30):
    """Удаляет логи старше указанного количества дней"""
    if not os.path.exists(DB_NAME):
        print("❌ База данных не найдена!")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_date,))
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"🗑️ Удалено старых записей: {deleted}")

def add_admin(tg_id, permissions="full"):
    """Добавляет нового администратора"""
    if not os.path.exists(DB_NAME):
        print("❌ База данных не найдена!")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO admins (tg_id, permissions) VALUES (?, ?)",
            (tg_id, permissions)
        )
        cursor.execute(
            "UPDATE users SET is_admin = 1 WHERE tg_id = ?",
            (tg_id,)
        )
        conn.commit()
        print(f"✅ Администратор {tg_id} добавлен с правами: {permissions}")
    except sqlite3.IntegrityError:
        print(f"⚠️ Пользователь {tg_id} уже является администратором")
    
    conn.close()

def list_users():
    """Показывает список всех пользователей"""
    if not os.path.exists(DB_NAME):
        print("❌ База данных не найдена!")
        return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tg_id, full_name, status, location, last_action, is_admin 
        FROM users 
        ORDER BY is_admin DESC, full_name
    """)
    
    users = cursor.fetchall()
    
    print("👥 Список пользователей")
    print("=" * 80)
    print(f"{'ID':<12} {'ФИО':<20} {'Статус':<15} {'Локация':<15} {'Админ':<5}")
    print("-" * 80)
    
    for tg_id, name, status, location, last_action, is_admin in users:
        admin_mark = "👑" if is_admin else "👤"
        print(f"{tg_id:<12} {name:<20} {status:<15} {location:<15} {admin_mark:<5}")
    
    conn.close()

def validate_config():
    """Проверяет конфигурацию бота"""
    print("🔍 Проверка конфигурации...")
    
    # Проверка .env файла
    if os.path.exists('.env'):
        print("✅ Файл .env найден")
        with open('.env', 'r') as f:
            content = f.read()
            if 'TELEGRAM_BOT_TOKEN' in content:
                print("✅ TELEGRAM_BOT_TOKEN настроен")
            else:
                print("❌ TELEGRAM_BOT_TOKEN не найден в .env")
    else:
        print("❌ Файл .env не найден")
    
    # Проверка структуры папок
    folders = ['data', 'config', 'logs', 'exports']
    for folder in folders:
        if os.path.exists(folder):
            print(f"✅ Папка {folder} существует")
        else:
            print(f"⚠️ Папка {folder} не найдена")
    
    # Проверка файлов конфигурации
    files = {
        'data/locations.json': 'Локации',
        'config/notifications.json': 'Уведомления'
    }
    
    for file_path, description in files.items():
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"⚠️ {description} не найден: {file_path}")

def main():
    parser = argparse.ArgumentParser(description='Инструменты для управления ботом')
    parser.add_argument('command', choices=[
        'backup', 'stats', 'clean', 'add-admin', 'users', 'check'
    ], help='Команда для выполнения')
    parser.add_argument('--days', type=int, default=30, help='Количество дней для очистки')
    parser.add_argument('--tg-id', type=int, help='Telegram ID для добавления админа')
    parser.add_argument('--permissions', default='full', help='Права администратора')
    
    args = parser.parse_args()
    
    if args.command == 'backup':
        backup_database()
    elif args.command == 'stats':
        show_statistics()
    elif args.command == 'clean':
        clean_old_logs(args.days)
    elif args.command == 'add-admin':
        if not args.tg_id:
            print("❌ Укажите --tg-id для добавления администратора")
            return
        add_admin(args.tg_id, args.permissions)
    elif args.command == 'users':
        list_users()
    elif args.command == 'check':
        validate_config()

if __name__ == '__main__':
    main()