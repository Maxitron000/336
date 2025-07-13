#!/usr/bin/env python3
"""
🔧 Скрипт настройки бота для PythonAnywhere
🎯 Оптимизированный для работы в условиях ограниченного места (500MB)
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta

def setup_lightweight_logging():
    """📋 Настройка облегченного логирования для PythonAnywhere"""
    
    # 📁 Создаем папку для логов если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 🔄 Настраиваем ротацию логов
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/bot.log',
                'maxBytes': 1024*1024*2,  # 2MB максимум
                'backupCount': 2,
                'encoding': 'utf8',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(log_config)
    print("✅ Настроена облегченная система логирования 📋")

def optimize_database():
    """🔧 Оптимизация базы данных для экономии места"""
    
    db_path = 'data/personnel.db'
    
    # 📁 Создаем папку для базы данных если её нет
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ⚡ Включаем WAL mode для лучшей производительности
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    
    # 🔄 Создаем автоочистку старых записей (старше 6 месяцев)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS cleanup_old_records
        AFTER INSERT ON arrivals
        BEGIN
            DELETE FROM arrivals 
            WHERE created_at < datetime('now', '-6 months');
        END;
    """)
    
    conn.commit()
    conn.close()
    print("✅ База данных оптимизирована для PythonAnywhere 💾")

def create_lightweight_export():
    """📄 Создание облегченной версии экспорта без pandas"""
    
    export_code = '''
import csv
import sqlite3
from datetime import datetime
import io

def export_to_csv_light(start_date=None, end_date=None):
    """📊 Облегченный экспорт в CSV без pandas"""
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    query = """
        SELECT u.full_name, a.location, a.status, a.created_at
        FROM arrivals a
        JOIN users u ON a.user_id = u.user_id
    """
    
    params = []
    if start_date:
        query += " WHERE a.created_at >= ?"
        params.append(start_date)
    if end_date:
        query += " AND a.created_at <= ?" if start_date else " WHERE a.created_at <= ?"
        params.append(end_date)
    
    query += " ORDER BY a.created_at DESC"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    # 💾 Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ФИО', 'Локация', 'Статус', 'Дата'])
    
    for row in results:
        writer.writerow(row)
    
    content = output.getvalue()
    output.close()
    conn.close()
    
    return content

def get_statistics_light():
    """📈 Получение статистики без pandas"""
    
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    
    # 📊 Общее количество записей
    cursor.execute("SELECT COUNT(*) FROM arrivals")
    total_records = cursor.fetchone()[0]
    
    # 👥 Количество уникальных пользователей
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    total_users = cursor.fetchone()[0]
    
    # 📅 Записи за сегодня
    cursor.execute("""
        SELECT COUNT(*) FROM arrivals 
        WHERE DATE(created_at) = DATE('now')
    """)
    today_records = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_records': total_records,
        'total_users': total_users,
        'today_records': today_records
    }
'''
    
    with open('export_light.py', 'w', encoding='utf-8') as f:
        f.write(export_code)
    
    print("✅ Создана облегченная версия экспорта 📄")

def create_optimized_config():
    """⚙️ Создание конфигурации для оптимизированной версии"""
    
    config_code = '''
import os
from dotenv import load_dotenv

load_dotenv()

# 🎯 Настройки для оптимизированной версии
OPTIMIZED_CONFIG = {
    'MAX_LOG_SIZE': 1024 * 1024 * 2,  # 2MB
    'MAX_DB_SIZE': 1024 * 1024 * 50,  # 50MB
    'CLEANUP_INTERVAL_DAYS': 180,     # 6 месяцев
    'MAX_USERS': 100,                 # Лимит пользователей
    'ENABLE_DETAILED_LOGGING': False,  # Отключаем детальные логи
    'ENABLE_EXPORT': True,            # Оставляем базовый экспорт
    'ENABLE_NOTIFICATIONS': True,     # Уведомления работают
}

# 📍 Локации с эмодзи
LOCATIONS_WITH_EMOJI = {
    "🏥 Поликлиника": "Поликлиника",
    "⚓ ОБРМП": "ОБРМП", 
    "🌆 Калининград": "Калининград",
    "🛒 Магазин": "Магазин",
    "🍲 Столовая": "Столовая",
    "🏨 Госпиталь": "Госпиталь",
    "⚙️ Рабочка": "Рабочка",
    "🩺 ВВК": "ВВК",
    "🏛️ МФЦ": "МФЦ",
    "🚔 Патруль": "Патруль"
}

# 🔑 Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]

# 💾 Настройки базы данных
DATABASE_PATH = 'data/personnel.db'
'''
    
    with open('config_optimized.py', 'w', encoding='utf-8') as f:
        f.write(config_code)
    
    print("✅ Создана конфигурация для оптимизированной версии ⚙️")

def main():
    """🚀 Основная функция настройки"""
    
    print("🚀 Настройка бота для PythonAnywhere...")
    print("📊 Оптимизация для лимита 500MB")
    
    setup_lightweight_logging()
    optimize_database()
    create_lightweight_export()
    create_optimized_config()
    
    print("\n✅ Настройка завершена! 🎉")
    print("💡 Рекомендации для PythonAnywhere:")
    print("   - 📦 Используйте requirements_optimized.txt")
    print("   - 🔑 Настройте переменные окружения BOT_TOKEN и ADMIN_IDS")
    print("   - 🧹 Регулярно очищайте логи (раз в месяц)")
    print("   - 📊 Мониторьте размер базы данных")
    print("   - 🚀 Используйте main_optimized.py для запуска")
    print("   - 🎯 Смотрите BOT_CHECKLIST.md для полного списка функций")

if __name__ == "__main__":
    main()