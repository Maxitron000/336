"""
База данных для бота учета персонала
"""
import sqlite3
import asyncio
import aiosqlite
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import json
import os

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = 'data/bot_database.db'):
        self.db_path = db_path
        self.connection = None
    
    async def init(self):
        """Инициализация базы данных"""
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Подключаемся к базе данных
            self.connection = await aiosqlite.connect(self.db_path)
            
            # Создаем таблицы
            await self._create_tables()
            
            logger.info("✅ База данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    async def _create_tables(self):
        """Создание таблиц базы данных"""
        async with self.connection.cursor() as cursor:
            # Таблица пользователей
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    location TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица отметок
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    location TEXT,
                    status TEXT DEFAULT 'present',
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, date)
                )
            ''')
            
            # Таблица событий (журнал)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Таблица настроек уведомлений
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_settings (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    daily_summary BOOLEAN DEFAULT TRUE,
                    reminders BOOLEAN DEFAULT TRUE,
                    silent_mode BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Создаем индексы для оптимизации
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
            
            await self.connection.commit()
    
    async def close(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            await self.connection.close()
    
    # Методы для работы с пользователями
    async def add_user(self, telegram_id: int, name: str, location: str = None) -> bool:
        """Добавление нового пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT OR REPLACE INTO users (telegram_id, name, location)
                    VALUES (?, ?, ?)
                ''', (telegram_id, name, location))
                
                user_id = cursor.lastrowid
                
                # Добавляем настройки уведомлений по умолчанию
                await cursor.execute('''
                    INSERT OR IGNORE INTO notification_settings (user_id)
                    VALUES (?)
                ''', (user_id,))
                
                await self.connection.commit()
                
                # Логируем событие
                await self.log_event(user_id, "user_added", f"Добавлен пользователь: {name}")
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Получение пользователя по Telegram ID"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT * FROM users WHERE telegram_id = ?
                ''', (telegram_id,))
                
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    async def update_user_name(self, telegram_id: int, new_name: str) -> bool:
        """Обновление имени пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    UPDATE users SET name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (new_name, telegram_id))
                
                if cursor.rowcount > 0:
                    await self.connection.commit()
                    
                    # Логируем событие
                    user = await self.get_user(telegram_id)
                    if user:
                        await self.log_event(user['id'], "name_changed", f"Имя изменено на: {new_name}")
                    
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Ошибка обновления имени: {e}")
            return False
    
    async def delete_user(self, telegram_id: int) -> bool:
        """Удаление пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                # Получаем информацию о пользователе для логирования
                user = await self.get_user(telegram_id)
                
                await cursor.execute('DELETE FROM users WHERE telegram_id = ?', (telegram_id,))
                
                if cursor.rowcount > 0:
                    await self.connection.commit()
                    
                    # Логируем событие
                    if user:
                        await self.log_event(None, "user_deleted", f"Удален пользователь: {user['name']}")
                    
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False
    
    async def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('SELECT * FROM users ORDER BY name')
                rows = await cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []
    
    # Методы для работы с отметками
    async def mark_attendance(self, telegram_id: int, location: str = None) -> bool:
        """Отметка присутствия пользователя"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return False
            
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT OR REPLACE INTO attendance (user_id, date, location)
                    VALUES (?, ?, ?)
                ''', (user['id'], date.today(), location))
                
                await self.connection.commit()
                
                # Логируем событие
                await self.log_event(user['id'], "attendance_marked", f"Отметка: {location or 'не указано'}")
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка отметки присутствия: {e}")
            return False
    
    async def get_attendance_today(self) -> List[Dict]:
        """Получение отметок за сегодня"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT u.name, u.location, a.time, a.status
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.date = ?
                    ORDER BY a.time
                ''', (date.today(),))
                
                rows = await cursor.fetchall()
                return [
                    {
                        'name': row[0],
                        'location': row[1],
                        'time': row[2],
                        'status': row[3]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Ошибка получения отметок: {e}")
            return []
    
    async def get_absent_users(self) -> List[Dict]:
        """Получение отсутствующих пользователей"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT u.id, u.name, u.location
                    FROM users u
                    LEFT JOIN attendance a ON u.id = a.user_id AND a.date = ?
                    WHERE a.id IS NULL
                    ORDER BY u.name
                ''', (date.today(),))
                
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'name': row[1],
                        'location': row[2]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Ошибка получения отсутствующих: {e}")
            return []
    
    # Статистические методы
    async def get_total_users(self) -> int:
        """Общее количество пользователей"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('SELECT COUNT(*) FROM users')
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка подсчета пользователей: {e}")
            return 0
    
    async def get_present_users(self) -> int:
        """Количество присутствующих сегодня"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ?', (date.today(),))
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка подсчета присутствующих: {e}")
            return 0
    
    async def get_absent_users_count(self) -> int:
        """Количество отсутствующих сегодня"""
        total = await self.get_total_users()
        present = await self.get_present_users()
        return total - present
    
    # Методы для журнала событий
    async def log_event(self, user_id: Optional[int], action: str, details: str = None):
        """Логирование события"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT INTO events (user_id, action, details)
                    VALUES (?, ?, ?)
                ''', (user_id, action, details))
                await self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка логирования события: {e}")
    
    async def get_events(self, limit: int = 100) -> List[Dict]:
        """Получение последних событий"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT e.action, e.details, e.timestamp, u.name
                    FROM events e
                    LEFT JOIN users u ON e.user_id = u.id
                    ORDER BY e.timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = await cursor.fetchall()
                return [
                    {
                        'action': row[0],
                        'details': row[1],
                        'timestamp': row[2],
                        'user_name': row[3] or 'Система'
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    # Методы для экспорта
    async def export_attendance_csv(self, start_date: date, end_date: date) -> str:
        """Экспорт отметок в CSV"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT u.name, a.date, a.time, a.location, a.status
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.date BETWEEN ? AND ?
                    ORDER BY a.date DESC, a.time DESC
                ''', (start_date, end_date))
                
                rows = await cursor.fetchall()
                
                csv_content = "Имя,Дата,Время,Локация,Статус\n"
                for row in rows:
                    csv_content += f"{row[0]},{row[1]},{row[2]},{row[3] or ''},{row[4]}\n"
                
                return csv_content
                
        except Exception as e:
            logger.error(f"Ошибка экспорта CSV: {e}")
            return ""
    
    # Методы для уведомлений
    async def get_notification_settings(self, telegram_id: int) -> Dict:
        """Получение настроек уведомлений пользователя"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return {}
            
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT * FROM notification_settings WHERE user_id = ?
                ''', (user['id'],))
                
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка получения настроек уведомлений: {e}")
            return {}
    
    async def update_notification_settings(self, telegram_id: int, settings: Dict) -> bool:
        """Обновление настроек уведомлений"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return False
            
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    UPDATE notification_settings 
                    SET enabled = ?, daily_summary = ?, reminders = ?, silent_mode = ?
                    WHERE user_id = ?
                ''', (
                    settings.get('enabled', True),
                    settings.get('daily_summary', True),
                    settings.get('reminders', True),
                    settings.get('silent_mode', False),
                    user['id']
                ))
                
                await self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления настроек уведомлений: {e}")
            return False