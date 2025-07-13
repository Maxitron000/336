"""
Утилиты для управления ботом учета персонала
"""

import os
import sqlite3
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import subprocess
import json

from database import get_db_connection, get_database_stats, get_all_users, get_location_logs
from utils import get_current_time, get_db_path, get_export_path, get_log_path

logger = logging.getLogger(__name__)

class SystemManager:
    """Менеджер системы для управления ботом"""
    
    def __init__(self):
        self.db_path = get_db_path()
        self.export_path = get_export_path()
        self.log_path = get_log_path()
    
    def create_backup(self) -> Optional[str]:
        """Создание резервной копии базы данных"""
        try:
            if not os.path.exists(self.db_path):
                logger.error("База данных не найдена")
                return None
            
            # Создаем директорию для бэкапов
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Генерируем имя файла бэкапа
            timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"personnel_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Копируем базу данных
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Резервная копия создана: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Восстановление из резервной копии"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Файл резервной копии не найден: {backup_path}")
                return False
            
            # Проверяем, что это SQLite база данных
            if not self._is_valid_sqlite_db(backup_path):
                logger.error("Файл не является корректной базой данных SQLite")
                return False
            
            # Создаем резервную копию текущей базы
            current_backup = self.create_backup()
            if not current_backup:
                logger.warning("Не удалось создать резервную копию текущей базы")
            
            # Восстанавливаем из бэкапа
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"База данных восстановлена из: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при восстановлении из резервной копии: {e}")
            return False
    
    def _is_valid_sqlite_db(self, db_path: str) -> bool:
        """Проверка корректности SQLite базы данных"""
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            conn.close()
            return True
        except sqlite3.Error:
            return False
    
    def get_system_info(self) -> Dict:
        """Получение информации о системе"""
        try:
            info = {
                'database': {},
                'files': {},
                'system': {},
                'performance': {}
            }
            
            # Информация о базе данных
            if os.path.exists(self.db_path):
                db_size = os.path.getsize(self.db_path)
                info['database'] = {
                    'size': db_size,
                    'path': self.db_path,
                    'stats': get_database_stats()
                }
            
            # Информация о файлах
            info['files'] = {
                'export_dir': self.export_path,
                'log_dir': self.log_path,
                'export_files': len(os.listdir(self.export_path)) if os.path.exists(self.export_path) else 0,
                'log_files': len(os.listdir(self.log_path)) if os.path.exists(self.log_path) else 0
            }
            
            # Системная информация
            info['system'] = {
                'python_version': subprocess.check_output(['python', '--version']).decode().strip(),
                'disk_usage': self._get_disk_usage(),
                'uptime': self._get_uptime()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о системе: {e}")
            return {}
    
    def _get_disk_usage(self) -> Dict:
        """Получение информации об использовании диска"""
        try:
            total, used, free = shutil.disk_usage(os.path.dirname(self.db_path))
            return {
                'total': total,
                'used': used,
                'free': free,
                'usage_percent': (used / total) * 100
            }
        except Exception:
            return {'total': 0, 'used': 0, 'free': 0, 'usage_percent': 0}
    
    def _get_uptime(self) -> str:
        """Получение времени работы системы"""
        try:
            if os.name == 'nt':  # Windows
                return "Недоступно на Windows"
            else:  # Unix-like
                uptime = subprocess.check_output(['uptime', '-p']).decode().strip()
                return uptime
        except Exception:
            return "Недоступно"
    
    def optimize_database(self) -> bool:
        """Оптимизация базы данных"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # VACUUM - перестроение базы данных
            cursor.execute("VACUUM;")
            
            # ANALYZE - обновление статистики
            cursor.execute("ANALYZE;")
            
            conn.commit()
            conn.close()
            
            logger.info("База данных оптимизирована")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при оптимизации базы данных: {e}")
            return False
    
    def check_database_integrity(self) -> Tuple[bool, List[str]]:
        """Проверка целостности базы данных"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Проверка целостности
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            
            issues = []
            if result[0] != 'ok':
                issues.append(f"Проблема целостности: {result[0]}")
            
            # Проверка внешних ключей
            cursor.execute("PRAGMA foreign_key_check;")
            fk_issues = cursor.fetchall()
            
            for issue in fk_issues:
                issues.append(f"Проблема внешних ключей: {issue}")
            
            conn.close()
            
            is_ok = len(issues) == 0
            logger.info(f"Проверка целостности: {'OK' if is_ok else 'Найдены проблемы'}")
            
            return is_ok, issues
            
        except Exception as e:
            logger.error(f"Ошибка при проверке целостности базы данных: {e}")
            return False, [f"Ошибка проверки: {e}"]
    
    def cleanup_old_files(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Очистка старых файлов"""
        try:
            cleanup_stats = {
                'exports': 0,
                'logs': 0,
                'backups': 0
            }
            
            cutoff_time = get_current_time() - timedelta(days=days_to_keep)
            
            # Очистка файлов экспорта
            if os.path.exists(self.export_path):
                for filename in os.listdir(self.export_path):
                    filepath = os.path.join(self.export_path, filename)
                    if os.path.isfile(filepath):
                        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if file_time < cutoff_time:
                            os.remove(filepath)
                            cleanup_stats['exports'] += 1
            
            # Очистка старых логов
            if os.path.exists(self.log_path):
                for filename in os.listdir(self.log_path):
                    if filename.endswith('.log'):
                        filepath = os.path.join(self.log_path, filename)
                        if os.path.isfile(filepath):
                            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                            if file_time < cutoff_time:
                                os.remove(filepath)
                                cleanup_stats['logs'] += 1
            
            # Очистка старых бэкапов
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            if os.path.exists(backup_dir):
                for filename in os.listdir(backup_dir):
                    if filename.endswith('.db'):
                        filepath = os.path.join(backup_dir, filename)
                        if os.path.isfile(filepath):
                            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                            if file_time < cutoff_time:
                                os.remove(filepath)
                                cleanup_stats['backups'] += 1
            
            logger.info(f"Очистка файлов завершена: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Ошибка при очистке старых файлов: {e}")
            return {'exports': 0, 'logs': 0, 'backups': 0}
    
    def get_performance_metrics(self) -> Dict:
        """Получение метрик производительности"""
        try:
            metrics = {}
            
            # Время отклика базы данных
            start_time = datetime.now()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users;")
            cursor.fetchone()
            conn.close()
            db_response_time = (datetime.now() - start_time).total_seconds()
            
            metrics['db_response_time'] = db_response_time
            
            # Размер базы данных
            if os.path.exists(self.db_path):
                metrics['db_size'] = os.path.getsize(self.db_path)
            
            # Использование памяти (приблизительно)
            import psutil
            process = psutil.Process()
            metrics['memory_usage'] = process.memory_info().rss
            metrics['cpu_percent'] = process.cpu_percent()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка при получении метрик производительности: {e}")
            return {}

class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self):
        self.config_dir = "config"
        os.makedirs(self.config_dir, exist_ok=True)
    
    def get_config(self, config_name: str) -> Dict:
        """Получение конфигурации"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_name}.json")
            
            if not os.path.exists(config_path):
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Ошибка при получении конфигурации {config_name}: {e}")
            return {}
    
    def save_config(self, config_name: str, config_data: Dict) -> bool:
        """Сохранение конфигурации"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_name}.json")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Конфигурация {config_name} сохранена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении конфигурации {config_name}: {e}")
            return False
    
    def get_notifications_config(self) -> Dict:
        """Получение конфигурации уведомлений"""
        return self.get_config("notifications")
    
    def save_notifications_config(self, config: Dict) -> bool:
        """Сохранение конфигурации уведомлений"""
        return self.save_config("notifications", config)

class LogAnalyzer:
    """Анализатор логов"""
    
    def __init__(self):
        self.log_path = get_log_path()
    
    def analyze_user_activity(self, days: int = 7) -> Dict:
        """Анализ активности пользователей"""
        try:
            # Получаем логи за указанный период
            logs = get_location_logs(limit=10000)
            
            # Фильтруем по дате
            cutoff_date = get_current_time() - timedelta(days=days)
            recent_logs = [
                log for log in logs 
                if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff_date
            ]
            
            # Анализируем активность
            activity_stats = {}
            for log in recent_logs:
                user_id = log['telegram_id']
                if user_id not in activity_stats:
                    activity_stats[user_id] = {
                        'full_name': log['full_name'],
                        'actions': 0,
                        'locations': set(),
                        'last_activity': log['timestamp']
                    }
                
                activity_stats[user_id]['actions'] += 1
                activity_stats[user_id]['locations'].add(log['location'])
            
            # Конвертируем set в list для JSON
            for user_id in activity_stats:
                activity_stats[user_id]['locations'] = list(activity_stats[user_id]['locations'])
            
            return activity_stats
            
        except Exception as e:
            logger.error(f"Ошибка при анализе активности пользователей: {e}")
            return {}
    
    def get_location_statistics(self, days: int = 30) -> Dict:
        """Получение статистики по локациям"""
        try:
            logs = get_location_logs(limit=10000)
            
            # Фильтруем по дате
            cutoff_date = get_current_time() - timedelta(days=days)
            recent_logs = [
                log for log in logs 
                if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff_date
            ]
            
            location_stats = {}
            for log in recent_logs:
                location = log['location']
                if location not in location_stats:
                    location_stats[location] = {
                        'arrivals': 0,
                        'departures': 0,
                        'unique_users': set()
                    }
                
                if log['action'] == 'arrived':
                    location_stats[location]['arrivals'] += 1
                else:
                    location_stats[location]['departures'] += 1
                
                location_stats[location]['unique_users'].add(log['telegram_id'])
            
            # Конвертируем set в count для JSON
            for location in location_stats:
                location_stats[location]['unique_users'] = len(location_stats[location]['unique_users'])
            
            return location_stats
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики по локациям: {e}")
            return {}
    
    def get_hourly_activity(self, days: int = 7) -> Dict:
        """Получение почасовой активности"""
        try:
            logs = get_location_logs(limit=10000)
            
            # Фильтруем по дате
            cutoff_date = get_current_time() - timedelta(days=days)
            recent_logs = [
                log for log in logs 
                if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff_date
            ]
            
            hourly_stats = {}
            for log in recent_logs:
                timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                hour = timestamp.hour
                
                if hour not in hourly_stats:
                    hourly_stats[hour] = 0
                
                hourly_stats[hour] += 1
            
            return hourly_stats
            
        except Exception as e:
            logger.error(f"Ошибка при получении почасовой активности: {e}")
            return {}

class MaintenanceManager:
    """Менеджер обслуживания"""
    
    def __init__(self):
        self.system_manager = SystemManager()
        self.config_manager = ConfigManager()
        self.log_analyzer = LogAnalyzer()
    
    def perform_maintenance(self) -> Dict:
        """Выполнение полного обслуживания"""
        try:
            results = {}
            
            # Создание резервной копии
            backup_path = self.system_manager.create_backup()
            results['backup'] = backup_path is not None
            
            # Оптимизация базы данных
            results['optimize'] = self.system_manager.optimize_database()
            
            # Проверка целостности
            is_ok, issues = self.system_manager.check_database_integrity()
            results['integrity'] = {'ok': is_ok, 'issues': issues}
            
            # Очистка старых файлов
            cleanup_stats = self.system_manager.cleanup_old_files()
            results['cleanup'] = cleanup_stats
            
            # Получение метрик
            metrics = self.system_manager.get_performance_metrics()
            results['metrics'] = metrics
            
            logger.info("Обслуживание завершено успешно")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении обслуживания: {e}")
            return {'error': str(e)}
    
    def get_maintenance_report(self) -> Dict:
        """Получение отчета об обслуживании"""
        try:
            report = {
                'timestamp': get_current_time().isoformat(),
                'system_info': self.system_manager.get_system_info(),
                'database_stats': get_database_stats(),
                'user_activity': self.log_analyzer.analyze_user_activity(),
                'location_stats': self.log_analyzer.get_location_statistics(),
                'hourly_activity': self.log_analyzer.get_hourly_activity()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка при создании отчета обслуживания: {e}")
            return {'error': str(e)}

# Глобальные экземпляры менеджеров
system_manager = SystemManager()
config_manager = ConfigManager()
log_analyzer = LogAnalyzer()
maintenance_manager = MaintenanceManager()

# Функции для быстрого доступа
def create_backup() -> Optional[str]:
    """Быстрое создание резервной копии"""
    return system_manager.create_backup()

def get_system_info() -> Dict:
    """Быстрое получение информации о системе"""
    return system_manager.get_system_info()

def optimize_database() -> bool:
    """Быстрая оптимизация базы данных"""
    return system_manager.optimize_database()

def perform_maintenance() -> Dict:
    """Быстрое выполнение обслуживания"""
    return maintenance_manager.perform_maintenance()

def get_maintenance_report() -> Dict:
    """Быстрое получение отчета обслуживания"""
    return maintenance_manager.get_maintenance_report()

def cleanup_old_files(days: int = 30) -> Dict[str, int]:
    """Быстрая очистка старых файлов"""
    return system_manager.cleanup_old_files(days)

def check_database_integrity() -> Tuple[bool, List[str]]:
    """Быстрая проверка целостности базы данных"""
    return system_manager.check_database_integrity()

def get_performance_metrics() -> Dict:
    """Быстрое получение метрик производительности"""
    return system_manager.get_performance_metrics()

def analyze_user_activity(days: int = 7) -> Dict:
    """Быстрый анализ активности пользователей"""
    return log_analyzer.analyze_user_activity(days)

def get_location_statistics(days: int = 30) -> Dict:
    """Быстрое получение статистики по локациям"""
    return log_analyzer.get_location_statistics(days)