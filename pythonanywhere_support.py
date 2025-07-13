"""
Поддержка PythonAnywhere для бота
"""

import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import Database
from monitoring import BotHealthMonitor
from backup import BackupSystem
from notifications import NotificationSystem
from config import Config

logger = logging.getLogger(__name__)

class PythonAnywhereSupport:
    """Поддержка PythonAnywhere"""
    
    def __init__(self, db: Database, notification_system: NotificationSystem = None):
        self.db = db
        self.notification_system = notification_system
        self.config = Config()
        self.health_monitor = BotHealthMonitor(db)
        self.backup_system = BackupSystem()
        
        # Настройки для PythonAnywhere
        self.is_pythonanywhere = self._detect_pythonanywhere()
        self.auto_backup_enabled = True
        self.health_check_enabled = True
        self.cleanup_enabled = True
    
    def _detect_pythonanywhere(self) -> bool:
        """Определение, запущен ли бот на PythonAnywhere"""
        try:
            # Проверяем переменные окружения PythonAnywhere
            if 'PYTHONANYWHERE_SITE' in os.environ:
                return True
            
            # Проверяем путь к файлам
            if '/home/' in os.getcwd() and 'pythonanywhere' in os.getcwd().lower():
                return True
            
            # Проверяем наличие файлов PythonAnywhere
            if os.path.exists('/var/log/pythonanywhere.log'):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка определения PythonAnywhere: {e}")
            return False
    
    async def setup_pythonanywhere(self):
        """Настройка для PythonAnywhere"""
        if not self.is_pythonanywhere:
            logger.info("Не PythonAnywhere, пропускаем настройку")
            return
        
        try:
            logger.info("🔧 Настройка для PythonAnywhere...")
            
            # Создаем необходимые директории
            directories = ['logs', 'data', 'exports', 'backups', 'config']
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            # Настраиваем логирование для PythonAnywhere
            self._setup_pythonanywhere_logging()
            
            # Проверяем и создаем базу данных
            await self._setup_database()
            
            # Настраиваем автоматические задачи
            await self._setup_automated_tasks()
            
            logger.info("✅ Настройка PythonAnywhere завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки PythonAnywhere: {e}")
    
    def _setup_pythonanywhere_logging(self):
        """Настройка логирования для PythonAnywhere"""
        try:
            # Создаем специальный лог-файл для PythonAnywhere
            log_file = 'logs/pythonanywhere.log'
            
            # Настраиваем дополнительный обработчик
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Добавляем к корневому логгеру
            logging.getLogger().addHandler(file_handler)
            
            logger.info(f"📝 Логирование PythonAnywhere настроено: {log_file}")
            
        except Exception as e:
            logger.error(f"Ошибка настройки логирования: {e}")
    
    async def _setup_database(self):
        """Настройка базы данных для PythonAnywhere"""
        try:
            # Проверяем подключение к БД
            if not await self.db.is_connected():
                logger.warning("⚠️ База данных не подключена, инициализируем...")
                await self.db.init()
            
            # Проверяем таблицы
            total_users = await self.db.get_total_users()
            logger.info(f"📊 База данных готова, пользователей: {total_users}")
            
        except Exception as e:
            logger.error(f"Ошибка настройки БД: {e}")
    
    async def _setup_automated_tasks(self):
        """Настройка автоматических задач"""
        try:
            # Создаем файл с задачами для PythonAnywhere
            tasks_file = 'pythonanywhere_tasks.py'
            
            tasks_content = '''#!/usr/bin/env python3
"""
Автоматические задачи для PythonAnywhere
Запускается через планировщик PythonAnywhere
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pythonanywhere_support import PythonAnywhereSupport
from database import Database
from notifications import NotificationSystem
from config import Config
import asyncio

async def run_daily_tasks():
    """Выполнение ежедневных задач"""
    try:
        # Инициализируем компоненты
        config = Config()
        db = Database()
        await db.init()
        
        notification_system = NotificationSystem(None, db)
        support = PythonAnywhereSupport(db, notification_system)
        
        # Выполняем задачи
        await support.run_daily_maintenance()
        
    except Exception as e:
        print(f"Ошибка выполнения ежедневных задач: {e}")

async def run_health_check():
    """Проверка здоровья системы"""
    try:
        config = Config()
        db = Database()
        await db.init()
        
        notification_system = NotificationSystem(None, db)
        support = PythonAnywhereSupport(db, notification_system)
        
        await support.run_health_check()
        
    except Exception as e:
        print(f"Ошибка проверки здоровья: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        task_type = sys.argv[1]
        
        if task_type == "daily":
            asyncio.run(run_daily_tasks())
        elif task_type == "health":
            asyncio.run(run_health_check())
        else:
            print("Неизвестный тип задачи")
    else:
        print("Укажите тип задачи: daily или health")
'''
            
            with open(tasks_file, 'w', encoding='utf-8') as f:
                f.write(tasks_content)
            
            # Делаем файл исполняемым
            os.chmod(tasks_file, 0o755)
            
            logger.info(f"✅ Файл автоматических задач создан: {tasks_file}")
            
        except Exception as e:
            logger.error(f"Ошибка создания автоматических задач: {e}")
    
    async def run_daily_maintenance(self):
        """Выполнение ежедневного обслуживания"""
        try:
            logger.info("🔧 Выполнение ежедневного обслуживания...")
            
            # Создаем автоматический бэкап
            if self.auto_backup_enabled:
                await self._create_auto_backup()
            
            # Очищаем старые логи
            if self.cleanup_enabled:
                await self._cleanup_old_logs()
            
            # Проверяем здоровье системы
            if self.health_check_enabled:
                await self._run_health_check()
            
            # Очищаем старые экспорты
            await self._cleanup_old_exports()
            
            logger.info("✅ Ежедневное обслуживание завершено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка ежедневного обслуживания: {e}")
    
    async def _create_auto_backup(self):
        """Создание автоматического бэкапа"""
        try:
            logger.info("💾 Создание автоматического бэкапа...")
            
            backup_info = await self.backup_system.create_backup('auto')
            
            if backup_info['status'] == 'completed':
                logger.info(f"✅ Автоматический бэкап создан: {backup_info['name']}")
                
                # Уведомляем админов
                if self.notification_system:
                    await self.notification_system.send_admin_notification(
                        "auto_backup", f"Автоматический бэкап создан: {backup_info['name']}"
                    )
            else:
                logger.error(f"❌ Ошибка создания автоматического бэкапа: {backup_info.get('error')}")
                
        except Exception as e:
            logger.error(f"Ошибка создания автоматического бэкапа: {e}")
    
    async def _cleanup_old_logs(self):
        """Очистка старых логов"""
        try:
            import glob
            from datetime import datetime, timedelta
            
            # Удаляем логи старше 30 дней
            cutoff_date = datetime.now() - timedelta(days=30)
            
            log_files = glob.glob('logs/*.log')
            deleted_count = 0
            
            for log_file in log_files:
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_time < cutoff_date:
                        os.remove(log_file)
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Не удалось удалить лог {log_file}: {e}")
            
            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} старых логов")
                
        except Exception as e:
            logger.error(f"Ошибка очистки логов: {e}")
    
    async def _run_health_check(self):
        """Запуск проверки здоровья"""
        try:
            logger.info("🏥 Выполнение проверки здоровья...")
            
            health_data = await self.health_monitor.perform_health_check()
            
            # Если есть критические проблемы, уведомляем админов
            if health_data['overall_status'] in ['critical', 'error']:
                if self.notification_system:
                    await self.notification_system.send_bot_error_notification(
                        f"Критические проблемы: {health_data['overall_status']}",
                        "Автоматическая проверка здоровья"
                    )
            
            logger.info(f"✅ Проверка здоровья завершена: {health_data['overall_status']}")
            
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья: {e}")
    
    async def _cleanup_old_exports(self):
        """Очистка старых экспортов"""
        try:
            import glob
            from datetime import datetime, timedelta
            
            # Удаляем экспорты старше 7 дней
            cutoff_date = datetime.now() - timedelta(days=7)
            
            export_files = glob.glob('exports/*')
            deleted_count = 0
            
            for export_file in export_files:
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(export_file))
                    if file_time < cutoff_date:
                        os.remove(export_file)
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Не удалось удалить экспорт {export_file}: {e}")
            
            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} старых экспортов")
                
        except Exception as e:
            logger.error(f"Ошибка очистки экспортов: {e}")
    
    async def run_health_check(self):
        """Запуск проверки здоровья (для планировщика)"""
        await self._run_health_check()
    
    def get_pythonanywhere_info(self) -> Dict:
        """Получение информации о PythonAnywhere"""
        try:
            info = {
                'is_pythonanywhere': self.is_pythonanywhere,
                'auto_backup_enabled': self.auto_backup_enabled,
                'health_check_enabled': self.health_check_enabled,
                'cleanup_enabled': self.cleanup_enabled,
                'current_directory': os.getcwd(),
                'python_version': sys.version,
                'environment_variables': {}
            }
            
            # Собираем переменные окружения PythonAnywhere
            pythonanywhere_vars = [
                'PYTHONANYWHERE_SITE',
                'PYTHONANYWHERE_USERNAME',
                'PYTHONANYWHERE_DOMAIN'
            ]
            
            for var in pythonanywhere_vars:
                if var in os.environ:
                    info['environment_variables'][var] = os.environ[var]
            
            return info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации PythonAnywhere: {e}")
            return {'error': str(e)}
    
    def format_pythonanywhere_info(self, info: Dict) -> str:
        """Форматирование информации о PythonAnywhere"""
        try:
            message = "🐍 *Информация о PythonAnywhere*\n\n"
            
            if info['is_pythonanywhere']:
                message += "✅ Запущен на PythonAnywhere\n"
            else:
                message += "❌ Не PythonAnywhere\n"
            
            message += f"📁 Директория: {info['current_directory']}\n"
            message += f"🐍 Python: {info['python_version'][:50]}...\n"
            
            message += f"\n⚙️ *Настройки:*\n"
            message += f"💾 Автобэкап: {'✅' if info['auto_backup_enabled'] else '❌'}\n"
            message += f"🏥 Проверка здоровья: {'✅' if info['health_check_enabled'] else '❌'}\n"
            message += f"🧹 Очистка: {'✅' if info['cleanup_enabled'] else '❌'}\n"
            
            if info['environment_variables']:
                message += f"\n🔧 *Переменные окружения:*\n"
                for var, value in info['environment_variables'].items():
                    message += f"• {var}: {value}\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка форматирования информации: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def update_pythonanywhere_settings(self, settings: Dict):
        """Обновление настроек PythonAnywhere"""
        try:
            if 'auto_backup_enabled' in settings:
                self.auto_backup_enabled = settings['auto_backup_enabled']
                logger.info(f"Автобэкап: {'включен' if self.auto_backup_enabled else 'отключен'}")
            
            if 'health_check_enabled' in settings:
                self.health_check_enabled = settings['health_check_enabled']
                logger.info(f"Проверка здоровья: {'включена' if self.health_check_enabled else 'отключена'}")
            
            if 'cleanup_enabled' in settings:
                self.cleanup_enabled = settings['cleanup_enabled']
                logger.info(f"Очистка: {'включена' if self.cleanup_enabled else 'отключена'}")
            
            logger.info("✅ Настройки PythonAnywhere обновлены")
            
        except Exception as e:
            logger.error(f"Ошибка обновления настроек: {e}")