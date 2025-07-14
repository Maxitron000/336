#!/usr/bin/env python3
"""
Диагностический скрипт для проверки проблем с базой данных
"""

import os
import sys
import asyncio
import sqlite3
from pathlib import Path

def check_directories():
    """Проверка существования и прав на директории"""
    print("=" * 50)
    print("ПРОВЕРКА ДИРЕКТОРИЙ")
    print("=" * 50)
    
    directories = ['data', 'logs', 'exports']
    for dir_name in directories:
        dir_path = Path(dir_name)
        print(f"📁 {dir_name}/")
        print(f"   Существует: {'✅ Да' if dir_path.exists() else '❌ Нет'}")
        
        if dir_path.exists():
            print(f"   Права чтения: {'✅ Да' if os.access(dir_path, os.R_OK) else '❌ Нет'}")
            print(f"   Права записи: {'✅ Да' if os.access(dir_path, os.W_OK) else '❌ Нет'}")
        else:
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"   Создана: ✅ Успешно")
            except Exception as e:
                print(f"   Ошибка создания: ❌ {e}")
        print()

def check_database_file():
    """Проверка файла базы данных"""
    print("=" * 50)
    print("ПРОВЕРКА ФАЙЛА БД")
    print("=" * 50)
    
    db_paths = [
        'data/bot_database.db',
        './data/bot_database.db',
        os.path.abspath('data/bot_database.db')
    ]
    
    for db_path in db_paths:
        print(f"📄 {db_path}")
        if os.path.exists(db_path):
            print(f"   Существует: ✅ Да")
            print(f"   Размер: {os.path.getsize(db_path)} байт")
            
            # Проверяем подключение
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"   Таблиц: {len(tables)}")
                for table in tables:
                    print(f"     - {table[0]}")
                conn.close()
                print(f"   Подключение: ✅ Успешно")
            except Exception as e:
                print(f"   Ошибка подключения: ❌ {e}")
        else:
            print(f"   Существует: ❌ Нет")
        print()

def check_environment():
    """Проверка переменных окружения"""
    print("=" * 50)
    print("ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ")
    print("=" * 50)
    
    env_vars = ['BOT_TOKEN', 'DB_PATH', 'ADMIN_IDS']
    for var in env_vars:
        value = os.getenv(var, 'НЕ УСТАНОВЛЕНА')
        if var == 'BOT_TOKEN' and value != 'НЕ УСТАНОВЛЕНА':
            value = value[:10] + '***'  # Скрываем токен
        print(f"{var}: {value}")
    print()

def check_current_location():
    """Проверка текущего расположения"""
    print("=" * 50)
    print("ТЕКУЩЕЕ РАСПОЛОЖЕНИЕ")
    print("=" * 50)
    
    print(f"Рабочая директория: {os.getcwd()}")
    print(f"Скрипт находится: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Python путь: {sys.executable}")
    print()

async def test_database_creation():
    """Тест создания базы данных"""
    print("=" * 50)
    print("ТЕСТ СОЗДАНИЯ БД")
    print("=" * 50)
    
    try:
        # Импортируем наш класс базы данных
        from database import Database
        
        # Создаем экземпляр
        db = Database()
        print(f"✅ Экземпляр Database создан")
        print(f"   Путь к БД: {db.db_path}")
        
        # Инициализируем
        await db.init()
        print(f"✅ База данных инициализирована")
        
        # Проверяем подключение
        is_connected = await db.is_connected()
        print(f"   Подключение активно: {'✅ Да' if is_connected else '❌ Нет'}")
        
        # Закрываем соединение
        await db.close()
        print(f"✅ Соединение закрыто")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция диагностики"""
    print("🔍 ДИАГНОСТИКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    check_current_location()
    check_environment()
    check_directories()
    check_database_file()
    
    # Тест создания БД
    try:
        asyncio.run(test_database_creation())
    except Exception as e:
        print(f"❌ Ошибка в тесте создания БД: {e}")
    
    print("=" * 50)
    print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 50)

if __name__ == "__main__":
    main()