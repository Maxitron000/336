#!/usr/bin/env python3
"""
Скрипт для принудительного создания базы данных
Используйте этот скрипт если база данных не создается автоматически
"""

import os
import asyncio
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_database():
    """Создание базы данных"""
    try:
        print("🔧 СОЗДАНИЕ БАЗЫ ДАННЫХ")
        print("=" * 50)
        
        # Создаем необходимые директории
        directories = ['data', 'logs', 'exports']
        for directory in directories:
            path = Path(directory)
            if not path.exists():
                path.mkdir(exist_ok=True)
                print(f"✅ Создана директория: {directory}/")
            else:
                print(f"✅ Директория существует: {directory}/")
        
        # Импортируем и создаем базу данных
        from database import Database
        
        print("\n📦 ИНИЦИАЛИЗАЦИЯ БД")
        print("-" * 30)
        
        # Создаем экземпляр базы данных
        db = Database()
        print(f"📍 Путь к БД: {db.db_path}")
        
        # Создаем абсолютный путь для отладки
        abs_path = os.path.abspath(db.db_path)
        print(f"📍 Абсолютный путь: {abs_path}")
        
        # Инициализируем базу данных
        await db.init()
        print("✅ База данных инициализирована")
        
        # Проверяем подключение
        is_connected = await db.is_connected()
        if is_connected:
            print("✅ Подключение к БД активно")
            
            # Добавляем тестового пользователя для проверки
            test_result = await db.add_user(
                telegram_id=123456789,
                name="Тестовый пользователь",
                location="Тестовая локация"
            )
            
            if test_result:
                print("✅ Тестовый пользователь добавлен")
                
                # Удаляем тестового пользователя
                await db.delete_user(123456789)
                print("✅ Тестовый пользователь удален")
            else:
                print("⚠️ Не удалось добавить тестового пользователя")
        else:
            print("❌ Не удалось подключиться к БД")
        
        # Закрываем соединение
        await db.close()
        print("✅ Соединение закрыто")
        
        # Проверяем что файл создался
        if os.path.exists(db.db_path):
            size = os.path.getsize(db.db_path)
            print(f"\n📄 РЕЗУЛЬТАТ")
            print("-" * 30)
            print(f"✅ Файл БД создан: {db.db_path}")
            print(f"📏 Размер файла: {size} байт")
            
            # Проверяем структуру БД
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Таблиц создано: {len(tables)}")
            for table in tables:
                print(f"   - {table[0]}")
            conn.close()
            
        else:
            print("❌ Файл БД не был создан")
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("🎉 СОЗДАНИЕ БД ЗАВЕРШЕНО")
    print("=" * 50)
    return True

async def verify_database():
    """Проверка базы данных"""
    try:
        print("\n🔍 ПРОВЕРКА БД")
        print("=" * 50)
        
        from database import Database
        
        db = Database()
        
        # Проверяем что файл существует
        if not os.path.exists(db.db_path):
            print("❌ Файл БД не найден")
            return False
            
        # Подключаемся к существующей БД
        await db.init()
        
        # Получаем статистику
        total_users = await db.get_total_users()
        print(f"👥 Всего пользователей: {total_users}")
        
        present_users = await db.get_present_users()
        print(f"✅ Присутствуют: {present_users}")
        
        absent_users = await db.get_absent_users_count()
        print(f"❌ Отсутствуют: {absent_users}")
        
        await db.close()
        print("✅ База данных работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False

def main():
    """Главная функция"""
    print("🗄️ СОЗДАНИЕ БАЗЫ ДАННЫХ")
    print("=" * 50)
    print("Этот скрипт создаст базу данных для бота")
    print("Используйте его если БД не создается автоматически")
    print()
    
    # Создаем базу данных
    success = asyncio.run(create_database())
    
    if success:
        # Проверяем созданную БД
        asyncio.run(verify_database())
        print("\n✅ ГОТОВО! Теперь можно запускать бота.")
    else:
        print("\n❌ ОШИБКА! База данных не была создана.")
        print("Проверьте права доступа и повторите попытку.")

if __name__ == "__main__":
    main()