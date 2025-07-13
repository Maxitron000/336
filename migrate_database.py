#!/usr/bin/env python3
"""
Скрипт миграции базы данных для обновления структуры
"""

import asyncio
import sqlite3
import logging
from datetime import datetime
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    """Миграция базы данных к новой структуре"""
    try:
        logger.info("🔄 Начинаем миграцию базы данных...")
        
        # Подключаемся к базе данных
        db = Database()
        await db.init()
        
        # Проверяем текущую структуру
        await check_current_structure()
        
        # Выполняем миграции
        await migrate_users_table()
        await migrate_attendance_table()
        await create_new_tables()
        await migrate_data()
        
        logger.info("✅ Миграция завершена успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        raise
    finally:
        await db.close()

async def check_current_structure():
    """Проверка текущей структуры базы данных"""
    logger.info("🔍 Проверяем текущую структуру...")
    
    async with db.connection.cursor() as cursor:
        # Проверяем существующие таблицы
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        logger.info(f"Найдены таблицы: {table_names}")

async def migrate_users_table():
    """Миграция таблицы пользователей"""
    logger.info("👥 Мигрируем таблицу пользователей...")
    
    try:
        async with db.connection.cursor() as cursor:
            # Проверяем, есть ли новые поля
            await cursor.execute("PRAGMA table_info(users)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Добавляем новые поля, если их нет
            new_fields = [
                ("is_commander", "BOOLEAN DEFAULT FALSE"),
                ("can_get_notifications", "BOOLEAN DEFAULT FALSE"),
                ("show_in_reports", "BOOLEAN DEFAULT TRUE"),
                ("status", "TEXT DEFAULT 'absent'")
            ]
            
            for field_name, field_type in new_fields:
                if field_name not in column_names:
                    await cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                    logger.info(f"Добавлено поле: {field_name}")
            
            await db.connection.commit()
            
    except Exception as e:
        logger.error(f"Ошибка миграции таблицы пользователей: {e}")
        raise

async def migrate_attendance_table():
    """Миграция таблицы отметок"""
    logger.info("📊 Мигрируем таблицу отметок...")
    
    try:
        async with db.connection.cursor() as cursor:
            # Проверяем, есть ли поле note
            await cursor.execute("PRAGMA table_info(attendance)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if "note" not in column_names:
                await cursor.execute("ALTER TABLE attendance ADD COLUMN note TEXT")
                logger.info("Добавлено поле: note")
            
            await db.connection.commit()
            
    except Exception as e:
        logger.error(f"Ошибка миграции таблицы отметок: {e}")
        raise

async def create_new_tables():
    """Создание новых таблиц"""
    logger.info("🏗️ Создаем новые таблицы...")
    
    try:
        async with db.connection.cursor() as cursor:
            # Таблица локаций
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица детального журнала
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance_log (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    location TEXT,
                    note TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Таблица шаблонов уведомлений
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_templates (
                    id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL,
                    template TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Обновляем таблицу настроек уведомлений
            await cursor.execute("PRAGMA table_info(notification_settings)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            new_fields = [
                ("arrival_notifications", "BOOLEAN DEFAULT TRUE"),
                ("departure_notifications", "BOOLEAN DEFAULT TRUE")
            ]
            
            for field_name, field_type in new_fields:
                if field_name not in column_names:
                    await cursor.execute(f"ALTER TABLE notification_settings ADD COLUMN {field_name} {field_type}")
                    logger.info(f"Добавлено поле: {field_name}")
            
            await db.connection.commit()
            
    except Exception as e:
        logger.error(f"Ошибка создания новых таблиц: {e}")
        raise

async def migrate_data():
    """Миграция данных"""
    logger.info("📦 Мигрируем данные...")
    
    try:
        async with db.connection.cursor() as cursor:
            # Обновляем статусы пользователей на основе отметок за сегодня
            await cursor.execute('''
                UPDATE users 
                SET status = 'present' 
                WHERE id IN (
                    SELECT DISTINCT user_id 
                    FROM attendance 
                    WHERE date = DATE('now')
                )
            ''')
            
            updated_count = cursor.rowcount
            logger.info(f"Обновлены статусы {updated_count} пользователей")
            
            # Создаем записи в детальном журнале на основе существующих отметок
            await cursor.execute('''
                INSERT INTO attendance_log (user_id, action, location, timestamp)
                SELECT user_id, 'present', location, time
                FROM attendance
                WHERE date = DATE('now')
            ''')
            
            inserted_count = cursor.rowcount
            logger.info(f"Создано {inserted_count} записей в журнале")
            
            await db.connection.commit()
            
    except Exception as e:
        logger.error(f"Ошибка миграции данных: {e}")
        raise

async def backup_database():
    """Создание резервной копии перед миграцией"""
    import shutil
    import os
    
    try:
        backup_path = f"data/bot_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2("data/bot_database.db", backup_path)
        logger.info(f"✅ Резервная копия создана: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Ошибка создания резервной копии: {e}")
        raise

if __name__ == "__main__":
    # Создаем резервную копию
    backup_path = asyncio.run(backup_database())
    
    # Выполняем миграцию
    asyncio.run(migrate_database())
    
    print(f"\n🎉 Миграция завершена!")
    print(f"📁 Резервная копия: {backup_path}")
    print(f"📊 Новая структура базы данных готова к использованию.")