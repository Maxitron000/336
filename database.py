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
    
    def __init__(self, db_path: str = None):
        # Если путь не указан, берем из конфигурации
        if db_path is None:
            try:
                from config import Config
                config = Config()
                db_path = config.DB_PATH
            except:
                # Fallback на стандартный путь
                db_path = 'data/bot_database.db'
        
        # Убеждаемся что используем абсолютный путь
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
            
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
                    status TEXT DEFAULT 'в_части',
                    last_status_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Добавляем новые колонки если они не существуют
            try:
                await cursor.execute('ALTER TABLE users ADD COLUMN status TEXT DEFAULT "в_части"')
            except:
                pass
            
            try:
                await cursor.execute('ALTER TABLE users ADD COLUMN last_status_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except:
                pass
            
            try:
                await cursor.execute('ALTER TABLE users ADD COLUMN username TEXT')
            except:
                pass
            
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
            
            # Таблица прав доступа для командиров
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS commander_permissions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    can_view_personnel BOOLEAN DEFAULT TRUE,
                    can_manage_personnel BOOLEAN DEFAULT FALSE,
                    can_export_data BOOLEAN DEFAULT FALSE,
                    can_view_journal BOOLEAN DEFAULT TRUE,
                    can_clear_journal BOOLEAN DEFAULT FALSE,
                    can_manage_notifications BOOLEAN DEFAULT FALSE,
                    can_view_stats BOOLEAN DEFAULT TRUE,
                    can_force_operations BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    
    async def is_connected(self) -> bool:
        """Проверка подключения к базе данных"""
        try:
            if not self.connection:
                return False
            
            # Пробуем выполнить простой запрос
            async with self.connection.cursor() as cursor:
                await cursor.execute('SELECT 1')
                await cursor.fetchone()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки подключения к БД: {e}")
            return False
    
    # Методы для работы с пользователями
    async def add_user(self, telegram_id: int, name: str, location: str = None, username: str = None) -> bool:
        """Добавление нового пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT OR REPLACE INTO users (telegram_id, name, location, username)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, name, location, username))
                
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
    
    async def get_events(self, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """Получение событий с фильтрами"""
        try:
            # Базовый запрос
            query = '''
                SELECT e.action, e.details, e.timestamp, u.name, u.username
                FROM events e
                LEFT JOIN users u ON e.user_id = u.id
            '''
            
            conditions = []
            params = []
            
            # Применяем фильтры
            if filters:
                if filters.get('start_date'):
                    conditions.append("DATE(e.timestamp) >= ?")
                    params.append(filters['start_date'])
                
                if filters.get('end_date'):
                    conditions.append("DATE(e.timestamp) <= ?")
                    params.append(filters['end_date'])
                
                if filters.get('user_name'):
                    conditions.append("u.name LIKE ?")
                    params.append(f"%{filters['user_name']}%")
                
                if filters.get('action'):
                    conditions.append("e.action LIKE ?")
                    params.append(f"%{filters['action']}%")
                
                if filters.get('period'):
                    period = filters['period']
                    if period == 'today':
                        conditions.append("DATE(e.timestamp) = DATE('now')")
                    elif period == 'week':
                        conditions.append("DATE(e.timestamp) >= DATE('now', '-7 days')")
                    elif period == 'month':
                        conditions.append("DATE(e.timestamp) >= DATE('now', '-30 days')")
            
            # Добавляем условия к запросу
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY e.timestamp DESC LIMIT ?'
            params.append(limit)
            
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params)
                
                rows = await cursor.fetchall()
                return [
                    {
                        'action': row[0],
                        'details': row[1],
                        'timestamp': row[2],
                        'user_name': row[3] or 'Система',
                        'username': row[4]
                    }
                    for row in rows
                                  ]
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    async def get_events_stats(self, filters: Dict = None) -> Dict:
        """Получение статистики по журналу событий"""
        try:
            # Базовый запрос для подсчета событий по типам
            query = '''
                SELECT e.action, COUNT(*) as count
                FROM events e
                LEFT JOIN users u ON e.user_id = u.id
            '''
            
            conditions = []
            params = []
            
            # Применяем те же фильтры что и в get_events
            if filters:
                if filters.get('start_date'):
                    conditions.append("DATE(e.timestamp) >= ?")
                    params.append(filters['start_date'])
                
                if filters.get('end_date'):
                    conditions.append("DATE(e.timestamp) <= ?")
                    params.append(filters['end_date'])
                
                if filters.get('user_name'):
                    conditions.append("u.name LIKE ?")
                    params.append(f"%{filters['user_name']}%")
                
                if filters.get('period'):
                    period = filters['period']
                    if period == 'today':
                        conditions.append("DATE(e.timestamp) = DATE('now')")
                    elif period == 'week':
                        conditions.append("DATE(e.timestamp) >= DATE('now', '-7 days')")
                    elif period == 'month':
                        conditions.append("DATE(e.timestamp) >= DATE('now', '-30 days')")
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' GROUP BY e.action ORDER BY count DESC'
            
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                
                stats = {
                    'total_events': sum(row[1] for row in rows),
                    'by_action': {row[0]: row[1] for row in rows}
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики событий: {e}")
            return {}

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
    
    # Новые методы для работы со статусами солдат
    async def set_soldier_status(self, telegram_id: int, status: str, location: str = None) -> bool:
        """Установка статуса солдата"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return False
            
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    UPDATE users 
                    SET status = ?, location = ?, last_status_change = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (status, location, telegram_id))
                
                await self.connection.commit()
                
                # Логируем событие
                await self.log_event(user['id'], status, f"Локация: {location}" if location else None)
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка установки статуса: {e}")
            return False
    
    async def get_soldier_status(self, telegram_id: int) -> Optional[Dict]:
        """Получение статуса солдата"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return None
            
            return {
                'name': user['name'],
                'status': user.get('status', 'в_части'),
                'location': user.get('location'),
                'last_status_change': user.get('last_status_change'),
                'telegram_id': user['telegram_id']
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return None
    
    async def get_soldiers_by_status(self, status: str) -> List[Dict]:
        """Получение списка солдат по статусу"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT telegram_id, name, location, last_status_change, status
                    FROM users 
                    WHERE status = ? AND is_admin = FALSE
                    ORDER BY name
                ''', (status,))
                
                rows = await cursor.fetchall()
                
                soldiers = []
                for row in rows:
                    soldiers.append({
                        'telegram_id': row[0],
                        'name': row[1],
                        'location': row[2],
                        'last_status_change': row[3],
                        'status': row[4]
                    })
                
                return soldiers
                
        except Exception as e:
            logger.error(f"Ошибка получения солдат по статусу: {e}")
            return []
    
    async def get_soldiers_in_unit(self) -> List[Dict]:
        """Получение солдат в части"""
        return await self.get_soldiers_by_status('в_части')
    
    async def get_soldiers_away(self) -> List[Dict]:
        """Получение солдат вне части"""
        return await self.get_soldiers_by_status('вне_части')
    
    async def get_soldiers_count_by_status(self, status: str) -> int:
        """Получение количества солдат по статусу"""
        soldiers = await self.get_soldiers_by_status(status)
        return len(soldiers)
    
    async def get_soldiers_away_by_location(self) -> Dict[str, List[Dict]]:
        """Получение солдат вне части, сгруппированных по локациям"""
        try:
            soldiers_away = await self.get_soldiers_away()
            
            locations = {}
            for soldier in soldiers_away:
                location = soldier.get('location') or 'не указано'
                if location not in locations:
                    locations[location] = []
                locations[location].append(soldier)
            
            return locations
            
        except Exception as e:
            logger.error(f"Ошибка группировки по локациям: {e}")
            return {}
    
    async def mark_soldier_arrival(self, telegram_id: int) -> bool:
        """Отметка прибытия солдата в часть"""
        return await self.set_soldier_status(telegram_id, 'в_части', None)
    
    async def mark_soldier_departure(self, telegram_id: int, location: str) -> bool:
        """Отметка убытия солдата из части"""
        return await self.set_soldier_status(telegram_id, 'вне_части', location)
    
    async def is_soldier_in_unit(self, telegram_id: int) -> bool:
        """Проверка, находится ли солдат в части"""
        status = await self.get_soldier_status(telegram_id)
        return status and status.get('status') == 'в_части'
    
    async def is_soldier_away(self, telegram_id: int) -> bool:
        """Проверка, находится ли солдат вне части"""
        status = await self.get_soldier_status(telegram_id)
        return status and status.get('status') == 'вне_части'
    
    # Методы для работы с правами командиров
    async def get_commander_permissions(self, telegram_id: int) -> Optional[Dict]:
        """Получение прав доступа командира"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return None
                
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT * FROM commander_permissions WHERE user_id = ?
                ''', (user['id'],))
                
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    # Создаем права по умолчанию для командира
                    await self.create_default_commander_permissions(user['id'])
                    return await self.get_commander_permissions(telegram_id)
                    
        except Exception as e:
            logger.error(f"Ошибка получения прав командира: {e}")
            return None
    
    async def create_default_commander_permissions(self, user_id: int) -> bool:
        """Создание прав по умолчанию для командира"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT OR IGNORE INTO commander_permissions (user_id)
                    VALUES (?)
                ''', (user_id,))
                await self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка создания прав командира: {e}")
            return False
    
    async def update_commander_permissions(self, telegram_id: int, permissions: Dict) -> bool:
        """Обновление прав доступа командира"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return False
                
            # Проверяем существуют ли права для этого пользователя
            existing_permissions = await self.get_commander_permissions(telegram_id)
            if not existing_permissions:
                await self.create_default_commander_permissions(user['id'])
            
            async with self.connection.cursor() as cursor:
                update_fields = []
                values = []
                
                for permission, value in permissions.items():
                    if permission.startswith('can_'):
                        update_fields.append(f"{permission} = ?")
                        values.append(value)
                
                if update_fields:
                    values.append(user['id'])
                    await cursor.execute(f'''
                        UPDATE commander_permissions 
                        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', values)
                    await self.connection.commit()
                    
                    # Логируем изменение прав
                    await self.log_event(user['id'], "permissions_updated", f"Обновлены права доступа: {permissions}")
                    return True
                    
        except Exception as e:
            logger.error(f"Ошибка обновления прав командира: {e}")
            return False
    
    async def check_commander_permission(self, telegram_id: int, permission: str) -> bool:
        """Проверка конкретного права доступа командира"""
        try:
            permissions = await self.get_commander_permissions(telegram_id)
            if not permissions:
                return False
                
            return permissions.get(permission, False)
            
        except Exception as e:
            logger.error(f"Ошибка проверки права доступа: {e}")
            return False

    async def get_user_info(self, telegram_id: int) -> Optional[Dict]:
        """Возвращает краткую информацию о пользователе (имя, статус, локация)."""
        user = await self.get_user(telegram_id)
        if not user:
            return None
        # Гарантируем наличие ключей, даже если колонка могла отсутствовать или быть NULL
        return {
            "full_name": user.get("name"),
            "status": user.get("status", "в_части"),
            "location": user.get("location")
        }