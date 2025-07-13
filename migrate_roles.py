#!/usr/bin/env python3
"""
Миграционный скрипт для обновления системы ролей
Обновляет старую систему is_admin/is_commander на новую систему ролей:
- soldier (боец)
- admin (админ) 
- main_admin (главный админ)
"""

import asyncio
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_roles.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RoleMigration:
    def __init__(self, db_path: str = 'data/bot_database.db'):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def create_backup(self) -> bool:
        """Создание резервной копии базы данных"""
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            logger.info(f"✅ Резервная копия создана: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания резервной копии: {e}")
            return False
    
    def check_old_structure(self) -> bool:
        """Проверка наличия старой структуры"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем наличие старых колонок
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            has_old_structure = 'is_admin' in columns or 'is_commander' in columns
            has_new_structure = 'role' in columns
            
            conn.close()
            
            if has_old_structure and not has_new_structure:
                logger.info("✅ Обнаружена старая структура ролей")
                return True
            elif has_new_structure:
                logger.info("✅ Новая структура ролей уже существует")
                return False
            else:
                logger.info("ℹ️ Структура ролей не найдена, создаем новую")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки структуры: {e}")
            return False
    
    def migrate_roles(self) -> bool:
        """Миграция ролей"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем текущую структуру
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Если новая структура уже есть, пропускаем миграцию
            if 'role' in columns:
                logger.info("✅ Новая структура ролей уже существует")
                conn.close()
                return True
            
            # Добавляем новую колонку role
            logger.info("📝 Добавляем колонку role...")
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'soldier'")
            
            # Мигрируем существующие роли
            logger.info("🔄 Мигрируем существующие роли...")
            
            # Получаем всех пользователей (проверяем какие колонки есть)
            if 'is_admin' in columns and 'is_commander' in columns:
                cursor.execute("SELECT id, telegram_id, name, is_admin, is_commander FROM users")
                users = cursor.fetchall()
                
                for user_id, telegram_id, name, is_admin, is_commander in users:
                    # Определяем новую роль
                    if is_admin:
                        new_role = 'main_admin'  # Первый админ становится главным
                    elif is_commander:
                        new_role = 'admin'  # Командиры становятся админами
                    else:
                        new_role = 'soldier'  # Остальные становятся бойцами
                    
                    # Обновляем роль
                    cursor.execute(
                        "UPDATE users SET role = ? WHERE id = ?",
                        (new_role, user_id)
                    )
                    
                    logger.info(f"👤 {name} (ID: {telegram_id}) -> {new_role}")
            
            # Создаем новую таблицу с полной структурой
            logger.info("🔒 Создаем новую структуру таблицы...")
            cursor.execute("""
                CREATE TABLE users_new (
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
            """)
            
            # Копируем данные (только существующие колонки)
            existing_columns = []
            for column in columns:
                if column in ['id', 'telegram_id', 'name', 'role']:
                    existing_columns.append(column)
            
            if existing_columns:
                columns_str = ', '.join(existing_columns)
                cursor.execute(f"""
                    INSERT INTO users_new ({columns_str})
                    SELECT {columns_str}
                    FROM users
                """)
            
            # Удаляем старую таблицу и переименовываем новую
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            
            # Создаем индексы
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Миграция ролей завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции ролей: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Проверка результатов миграции"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем структуру
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'role' not in columns:
                logger.error("❌ Колонка role не найдена")
                return False
            
            # Проверяем данные
            cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
            role_counts = cursor.fetchall()
            
            logger.info("📊 Статистика ролей после миграции:")
            for role, count in role_counts:
                logger.info(f"  {role}: {count} пользователей")
            
            # Проверяем корректность ролей
            cursor.execute("SELECT COUNT(*) FROM users WHERE role NOT IN ('soldier', 'admin', 'main_admin')")
            invalid_roles = cursor.fetchone()[0]
            
            if invalid_roles > 0:
                logger.error(f"❌ Найдено {invalid_roles} некорректных ролей")
                return False
            
            conn.close()
            logger.info("✅ Проверка миграции прошла успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки миграции: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Запуск полной миграции"""
        logger.info("🚀 Начинаем миграцию системы ролей...")
        
        # Создаем резервную копию
        if not self.create_backup():
            return False
        
        # Проверяем необходимость миграции
        if not self.check_old_structure():
            logger.info("ℹ️ Миграция не требуется")
            return True
        
        # Выполняем миграцию
        if not self.migrate_roles():
            return False
        
        # Проверяем результаты
        if not self.verify_migration():
            return False
        
        logger.info("🎉 Миграция системы ролей завершена успешно!")
        return True

def main():
    """Главная функция"""
    print("🔄 Миграция системы ролей Telegram бота")
    print("=" * 50)
    
    migration = RoleMigration()
    
    if migration.run_migration():
        print("\n✅ Миграция завершена успешно!")
        print(f"📁 Резервная копия: {migration.backup_path}")
        print("\n📋 Что изменилось:")
        print("• Удалены колонки is_admin и is_commander")
        print("• Добавлена колонка role с значениями: soldier, admin, main_admin")
        print("• is_admin=True -> main_admin")
        print("• is_commander=True -> admin")
        print("• Остальные -> soldier")
    else:
        print("\n❌ Миграция завершилась с ошибками!")
        print("Проверьте лог файл: migration_roles.log")

if __name__ == "__main__":
    main()