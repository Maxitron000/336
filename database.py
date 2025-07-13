"""
База данных для бота учета персонала
"""
import sqlite3
import asyncio
import aiosqlite
import logging
import re
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
            # Таблица пользователей (обновленная структура с 3 ролями)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    location TEXT,
                    role TEXT DEFAULT 'soldier' CHECK (role IN ('soldier', 'admin', 'main_admin')),
                    can_get_notifications BOOLEAN DEFAULT FALSE,
                    show_in_reports BOOLEAN DEFAULT TRUE,
                    status TEXT DEFAULT 'absent',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
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
            
            # Таблица отметок (обновленная)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    location TEXT,
                    status TEXT DEFAULT 'present',
                    note TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, date)
                )
            ''')
            
            # Таблица детального журнала отметок
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
            
            # Таблица настроек уведомлений (обновленная)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_settings (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    daily_summary BOOLEAN DEFAULT TRUE,
                    reminders BOOLEAN DEFAULT TRUE,
                    arrival_notifications BOOLEAN DEFAULT TRUE,
                    departure_notifications BOOLEAN DEFAULT TRUE,
                    silent_mode BOOLEAN DEFAULT FALSE,
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
            
            # Создаем индексы для оптимизации
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_log_timestamp ON attendance_log(timestamp)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)')
            await cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            
            # Инициализируем базовые локации
            await self._init_default_locations()
            
            # Инициализируем шаблоны уведомлений
            await self._init_notification_templates()
            
            await self.connection.commit()
    
    async def _init_default_locations(self):
        """Инициализация базовых локаций для военной части"""
        default_locations = [
            ("🏢 В расположении", "В расположении воинской части"),
            ("� Больничный", "На больничном"),
            ("🏖️ Отпуск", "В отпуске"),
            ("📚 Обучение", "На обучении/курсах"),
            ("🚗 Командировка", "В командировке"),
            ("🏠 Увольнение", "В увольнении"),
            ("⚖️ Суд", "В суде"),
            ("🏛️ Военкомат", "В военкомате"),
            ("🏥 Госпиталь", "В госпитале"),
            ("📋 Служебная", "По служебной необходимости"),
            ("🏠 Домой", "Домой по семейным обстоятельствам"),
            ("🚑 Медицинская", "По медицинским показаниям"),
            ("📝 Документы", "По документам"),
            ("� Техобслуживание", "На техническом обслуживании"),
            ("📊 Учения", "На учениях"),
            ("🛡️ Караул", "В карауле"),
            ("🏃 Наряд", "В наряде"),
            ("📋 Дежурство", "В дежурстве"),
            ("🚨 Тревога", "По тревоге"),
            ("⚡ Срочная", "По срочному вызову")
        ]
        
        async with self.connection.cursor() as cursor:
            for name, description in default_locations:
                await cursor.execute('''
                    INSERT OR IGNORE INTO locations (name, description)
                    VALUES (?, ?)
                ''', (name, description))
    
    async def _init_notification_templates(self):
        """Инициализация шаблонов уведомлений"""
        templates = [
            ("reminder", "🔔 Напоминание: не забудьте отметиться!"),
            ("reminder", "⏰ Время отметиться в системе"),
            ("reminder", "📝 Ждем вашу отметку о присутствии"),
            ("reminder", "✅ Пожалуйста, подтвердите свое присутствие"),
            ("reminder", "🎯 Не забудьте отметиться сегодня"),
            ("reminder", "📊 Ожидаем вашу отметку для сводки"),
            ("reminder", "🕐 Время ежедневной отметки"),
            ("reminder", "📋 Требуется отметка о присутствии"),
            ("reminder", "🔍 Ждем подтверждения вашего статуса"),
            ("reminder", "📈 Отметка нужна для статистики"),
            ("daily_summary", "📊 Ежедневная сводка за {date}"),
            ("arrival", "✅ {name} прибыл в {location}"),
            ("departure", "🚪 {name} убыл в {location}"),
            ("user_added", "👤 Добавлен новый пользователь: {name}"),
            ("user_deleted", "🗑️ Удален пользователь: {name}"),
            ("system_alert", "⚠️ Системное уведомление: {message}")
        ]
        
        async with self.connection.cursor() as cursor:
            for template_type, template in templates:
                await cursor.execute('''
                    INSERT OR IGNORE INTO notification_templates (type, template)
                    VALUES (?, ?)
                ''', (template_type, template))

    @staticmethod
    def validate_full_name(name: str) -> Tuple[bool, str]:
        """
        Валидация ФИО
        Возвращает (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "ФИО не может быть пустым"
        
        name = name.strip()
        
        # Проверка минимальной длины
        if len(name) < 5:
            return False, "ФИО должно содержать минимум 5 символов"
        
        # Проверка на кириллицу
        if not re.match(r'^[а-яёА-ЯЁ\s\.]+$', name):
            return False, "ФИО должно содержать только кириллицу, пробелы и точки"
        
        # Проверка на минимум 2 части (фамилия и инициалы)
        parts = name.split()
        if len(parts) < 2:
            return False, "ФИО должно содержать минимум 2 части (например: Иванов И.И.)"
        
        # Проверка на бессмысленные строки
        meaningless_patterns = [
            r'^[А-ЯЁ]{1,3}$',  # Одна буква
            r'^[0-9]+$',       # Только цифры
            r'^[А-ЯЁ\s]+[0-9]+$',  # Буквы + цифры
            r'^[А-ЯЁ]{1,2}\.[А-ЯЁ]{1,2}\.$'  # Только инициалы
        ]
        
        for pattern in meaningless_patterns:
            if re.match(pattern, name):
                return False, "ФИО не может состоять только из инициалов или содержать цифры"
        
        return True, ""
    
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
    async def add_user(self, telegram_id: int, name: str, location: str = None) -> Tuple[bool, str]:
        """Добавление нового пользователя с валидацией"""
        try:
            # Валидация ФИО
            is_valid, error_msg = self.validate_full_name(name)
            if not is_valid:
                return False, error_msg
            
            # Проверка на существующего пользователя
            existing_user = await self.get_user(telegram_id)
            if existing_user:
                return False, "Пользователь с таким Telegram ID уже существует"
            
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT INTO users (telegram_id, name, location, status)
                    VALUES (?, ?, ?, 'absent')
                ''', (telegram_id, name, location))
                
                user_id = cursor.lastrowid
                
                # Добавляем настройки уведомлений по умолчанию
                await cursor.execute('''
                    INSERT INTO notification_settings (user_id)
                    VALUES (?)
                ''', (user_id,))
                
                await self.connection.commit()
                
                # Логируем событие
                await self.log_event(user_id, "user_added", f"Добавлен пользователь: {name}")
                
                return True, "Пользователь успешно добавлен"
                
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False, f"Ошибка добавления пользователя: {str(e)}"
    
    async def check_user_exists(self, telegram_id: int = None, name: str = None) -> bool:
        """Проверка существования пользователя по Telegram ID или имени"""
        try:
            async with self.connection.cursor() as cursor:
                if telegram_id:
                    await cursor.execute('SELECT 1 FROM users WHERE telegram_id = ?', (telegram_id,))
                elif name:
                    await cursor.execute('SELECT 1 FROM users WHERE name = ?', (name,))
                else:
                    return False
                
                return await cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Ошибка проверки существования пользователя: {e}")
            return False
    
    async def get_commanders(self) -> List[Dict]:
        """Получение всех командиров"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT * FROM users 
                    WHERE role IN ('admin', 'main_admin') 
                    ORDER BY name
                ''')
                rows = await cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения командиров: {e}")
            return []
    
    async def get_users_with_notifications(self) -> List[Dict]:
        """Получение пользователей с включенными уведомлениями"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT u.* FROM users u
                    INNER JOIN notification_settings ns ON u.id = ns.user_id
                    WHERE ns.enabled = TRUE AND u.can_get_notifications = TRUE
                    ORDER BY u.name
                ''')
                rows = await cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения пользователей с уведомлениями: {e}")
            return []
    
    async def update_user_status(self, telegram_id: int, status: str, location: str = None, note: str = None) -> bool:
        """Обновление статуса пользователя с логированием"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return False
            
            async with self.connection.cursor() as cursor:
                # Обновляем статус пользователя
                await cursor.execute('''
                    UPDATE users SET status = ?, location = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (status, location, telegram_id))
                
                # Добавляем запись в детальный журнал
                await cursor.execute('''
                    INSERT INTO attendance_log (user_id, action, location, note)
                    VALUES (?, ?, ?, ?)
                ''', (user['id'], status, location, note))
                
                # Обновляем или добавляем отметку за сегодня
                if status == 'present':
                    await cursor.execute('''
                        INSERT OR REPLACE INTO attendance (user_id, date, location, status, note)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user['id'], date.today(), location, status, note))
                
                await self.connection.commit()
                
                # Логируем событие
                action_desc = "прибыл" if status == "present" else "убыл"
                await self.log_event(user['id'], f"user_{action_desc}", f"{action_desc.title()}: {location or 'не указано'}")
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления статуса пользователя: {e}")
            return False
    
    async def get_user_status(self, telegram_id: int) -> Optional[str]:
        """Получение текущего статуса пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT status, location FROM users WHERE telegram_id = ?
                ''', (telegram_id,))
                row = await cursor.fetchone()
                
                if row:
                    status, location = row
                    if status == 'present' and location == 'В расположении':
                        return 'В расположении'
                    elif status == 'absent':
                        return f'Убыл в {location}' if location else 'Вне расположения'
                    else:
                        return 'В расположении'  # По умолчанию в расположении
                return None
        except Exception as e:
            logger.error(f"Ошибка получения статуса пользователя: {e}")
            return None
    
    # Методы для работы с локациями
    async def get_locations(self) -> List[Dict]:
        """Получение всех активных локаций"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT * FROM locations 
                    WHERE is_active = TRUE 
                    ORDER BY name
                ''')
                rows = await cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения локаций: {e}")
            return []
    
    async def add_location(self, name: str, description: str = None) -> bool:
        """Добавление новой локации"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT INTO locations (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                
                await self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления локации: {e}")
            return False
    
    async def delete_location(self, location_id: int) -> bool:
        """Удаление локации"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('DELETE FROM locations WHERE id = ?', (location_id,))
                await self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка удаления локации: {e}")
            return False
    
    # Методы для работы с детальным журналом
    async def get_attendance_log(self, user_id: int = None, limit: int = 50) -> List[Dict]:
        """Получение детального журнала отметок"""
        try:
            async with self.connection.cursor() as cursor:
                if user_id:
                    await cursor.execute('''
                        SELECT al.*, u.name 
                        FROM attendance_log al
                        INNER JOIN users u ON al.user_id = u.id
                        WHERE al.user_id = ?
                        ORDER BY al.timestamp DESC
                        LIMIT ?
                    ''', (user_id, limit))
                else:
                    await cursor.execute('''
                        SELECT al.*, u.name 
                        FROM attendance_log al
                        INNER JOIN users u ON al.user_id = u.id
                        ORDER BY al.timestamp DESC
                        LIMIT ?
                    ''', (limit,))
                
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения журнала отметок: {e}")
            return []
    
    # Методы для работы с шаблонами уведомлений
    async def get_notification_template(self, template_type: str) -> Optional[str]:
        """Получение случайного шаблона уведомления по типу"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT template FROM notification_templates
                    WHERE type = ? AND is_active = TRUE
                    ORDER BY RANDOM()
                    LIMIT 1
                ''', (template_type,))
                
                row = await cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            logger.error(f"Ошибка получения шаблона уведомления: {e}")
            return None
    
    # Методы для валидации и проверок
    async def can_delete_user(self, telegram_id: int) -> Tuple[bool, str]:
        """Проверка возможности удаления пользователя"""
        try:
            user = await self.get_user(telegram_id)
            if not user:
                return False, "Пользователь не найден"
            
            # Проверяем, не пытается ли пользователь удалить себя
            # (это будет проверяться в обработчике)
            
            # Проверяем, не является ли последним администратором
            if user['role'] in ('admin', 'main_admin'):
                admin_count = await self.get_admin_count()
                if admin_count <= 1:
                    return False, "Нельзя удалить последнего администратора"
            
            return True, "Пользователь может быть удален"
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности удаления: {e}")
            return False, f"Ошибка проверки: {str(e)}"
    
    async def get_admin_count(self) -> int:
        """Получение количества администраторов"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('SELECT COUNT(*) FROM users WHERE role IN (\'admin\', \'main_admin\')')
                row = await cursor.fetchone()
                return row[0] if row else 0
                
        except Exception as e:
            logger.error(f"Ошибка получения количества админов: {e}")
            return 0
    
    async def get_commander_count(self) -> int:
        """Получение количества командиров"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('SELECT COUNT(*) FROM users WHERE role IN (\'admin\', \'main_admin\')')
                row = await cursor.fetchone()
                return row[0] if row else 0
                
        except Exception as e:
            logger.error(f"Ошибка получения количества командиров: {e}")
            return 0
    
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
    async def mark_attendance(self, telegram_id: int, location: str = None, note: str = None) -> Tuple[bool, str]:
        """Отметка прибытия в расположение части"""
        try:
            # Получаем пользователя
            user = await self.get_user(telegram_id)
            if not user:
                return False, "Пользователь не найден"
            
            today = date.today()
            
            # Проверяем, есть ли уже отметка за сегодня
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT status, location FROM attendance 
                    WHERE user_id = ? AND date = ?
                ''', (user['id'], today))
                existing = await cursor.fetchone()
            
            if existing:
                current_status, current_location = existing
                if current_status == 'present' and current_location == 'В расположении':
                    return False, "Вы уже отмечены в расположении"
            
            # Отмечаем прибытие в расположение
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT OR REPLACE INTO attendance (user_id, date, time, location, status, note)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?, 'present', ?)
                ''', (user['id'], today, 'В расположении', note))
                
                # Обновляем статус пользователя
                await cursor.execute('''
                    UPDATE users SET status = 'present', location = 'В расположении', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user['id'],))
                
                # Логируем событие
                await cursor.execute('''
                    INSERT INTO attendance_log (user_id, action, location, note, timestamp)
                    VALUES (?, 'arrived', 'В расположении', ?, CURRENT_TIMESTAMP)
                ''', (user['id'], note))
                
                # Логируем событие
                await self.log_event(user['id'], 'arrived', f"Прибыл в расположение части{f' - {note}' if note else ''}")
            
            await self.connection.commit()
            
            # Отправляем уведомления командирам
            if self.notification_system:
                await self.notification_system.send_arrival_notification(user['name'], 'В расположении', note)
            
            return True, "✅ Вы отмечены в расположении части"
            
        except Exception as e:
            logger.error(f"Ошибка отметки прибытия: {e}")
            return False, "Ошибка при отметке прибытия"
    
    async def mark_departure(self, telegram_id: int, location: str = None, note: str = None) -> Tuple[bool, str]:
        """Отметка убытия из расположения части"""
        try:
            # Получаем пользователя
            user = await self.get_user(telegram_id)
            if not user:
                return False, "Пользователь не найден"
            
            # Если локация не указана, используем "Вне расположения"
            if not location or location == 'В расположении':
                location = 'Вне расположения'
            
            today = date.today()
            
            # Проверяем, есть ли уже отметка за сегодня
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT status, location FROM attendance 
                    WHERE user_id = ? AND date = ?
                ''', (user['id'], today))
                existing = await cursor.fetchone()
            
            if existing:
                current_status, current_location = existing
                if current_status == 'absent' and current_location != 'В расположении':
                    return False, f"Вы уже отмечены убывшим в {current_location}"
            
            # Отмечаем убытие из расположения
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    INSERT OR REPLACE INTO attendance (user_id, date, time, location, status, note)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?, 'absent', ?)
                ''', (user['id'], today, location, note))
                
                # Обновляем статус пользователя
                await cursor.execute('''
                    UPDATE users SET status = 'absent', location = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (location, user['id'],))
                
                # Логируем событие
                await cursor.execute('''
                    INSERT INTO attendance_log (user_id, action, location, note, timestamp)
                    VALUES (?, 'left', ?, ?, CURRENT_TIMESTAMP)
                ''', (user['id'], location, note))
                
                # Логируем событие
                await self.log_event(user['id'], 'left', f"Убыл в {location}{f' - {note}' if note else ''}")
            
            await self.connection.commit()
            
            # Отправляем уведомления командирам
            if self.notification_system:
                await self.notification_system.send_departure_notification(user['name'], location, note)
            
            return True, f"✅ Вы отмечены убывшим в {location}"
            
        except Exception as e:
            logger.error(f"Ошибка отметки убытия: {e}")
            return False, "Ошибка при отметке убытия"
    
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
        """Получение отсутствующих пользователей (только show_in_reports=True)"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT u.id, u.name, u.location, u.status
                    FROM users u
                    WHERE u.show_in_reports = TRUE AND u.status = 'absent'
                    ORDER BY u.name
                ''')
                
                rows = await cursor.fetchall()
                return [
                    {
                        'id': row[0],
                        'name': row[1],
                        'location': row[2],
                        'status': row[3]
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
        """Количество присутствующих сегодня (только show_in_reports=True)"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE show_in_reports = TRUE AND status = 'present'
                ''')
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
    
    async def get_user_role(self, telegram_id: int) -> str:
        """Получение роли пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT role FROM users WHERE telegram_id = ?
                ''', (telegram_id,))
                row = await cursor.fetchone()
                return row[0] if row else 'soldier'
        except Exception as e:
            logger.error(f"Ошибка получения роли пользователя: {e}")
            return 'soldier'
    
    async def set_user_role(self, telegram_id: int, role: str) -> bool:
        """Установка роли пользователя"""
        if role not in ['soldier', 'admin', 'main_admin']:
            return False
        
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE telegram_id = ?
                ''', (role, telegram_id))
                await self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка установки роли пользователя: {e}")
            return False
    
    async def is_admin(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь админом или главным админом"""
        role = await self.get_user_role(telegram_id)
        return role in ['admin', 'main_admin']
    
    async def is_main_admin(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь главным админом"""
        role = await self.get_user_role(telegram_id)
        return role == 'main_admin'
    
    async def get_admins(self) -> List[Dict]:
        """Получение списка всех администраторов"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT telegram_id, name, role, created_at 
                    FROM users 
                    WHERE role IN ('admin', 'main_admin') 
                    ORDER BY role DESC, name
                ''')
                rows = await cursor.fetchall()
                return [
                    {
                        'telegram_id': row[0],
                        'name': row[1],
                        'role': row[2],
                        'created_at': row[3]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Ошибка получения списка админов: {e}")
            return []
    
    async def get_main_admin(self) -> Optional[Dict]:
        """Получение главного администратора"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute('''
                    SELECT telegram_id, name, created_at 
                    FROM users 
                    WHERE role = 'main_admin' 
                    LIMIT 1
                ''')
                row = await cursor.fetchone()
                if row:
                    return {
                        'telegram_id': row[0],
                        'name': row[1],
                        'created_at': row[2]
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка получения главного админа: {e}")
            return None