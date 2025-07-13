"""
Система мониторинга здоровья бота
"""

import os
import psutil
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import Database
from config import Config

logger = logging.getLogger(__name__)

class BotHealthMonitor:
    """Система мониторинга здоровья бота"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.health_history = []
        self.max_history_size = 100
    
    async def perform_health_check(self) -> Dict:
        """Выполнение полной проверки здоровья бота"""
        try:
            health_data = {
                'timestamp': datetime.now(),
                'bot_status': await self._check_bot_status(),
                'database_status': await self._check_database_status(),
                'system_status': await self._check_system_status(),
                'performance_status': await self._check_performance_status(),
                'overall_status': 'unknown'
            }
            
            # Определяем общий статус
            health_data['overall_status'] = self._determine_overall_status(health_data)
            
            # Сохраняем в историю
            self.health_history.append(health_data)
            if len(self.health_history) > self.max_history_size:
                self.health_history.pop(0)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья: {e}")
            return {
                'timestamp': datetime.now(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    async def _check_bot_status(self) -> Dict:
        """Проверка статуса бота"""
        try:
            # Проверяем доступность бота
            bot_status = {
                'status': 'unknown',
                'details': {},
                'issues': []
            }
            
            # Проверяем файлы бота
            required_files = ['main.py', 'config.py', 'database.py']
            missing_files = []
            
            for file in required_files:
                if not os.path.exists(file):
                    missing_files.append(file)
            
            if missing_files:
                bot_status['issues'].append(f"Отсутствуют файлы: {', '.join(missing_files)}")
                bot_status['status'] = 'critical'
            else:
                bot_status['status'] = 'ok'
                bot_status['details']['files'] = 'Все файлы на месте'
            
            # Проверяем конфигурацию
            try:
                if not self.config.BOT_TOKEN:
                    bot_status['issues'].append("BOT_TOKEN не настроен")
                    bot_status['status'] = 'critical'
                else:
                    bot_status['details']['config'] = 'Конфигурация корректна'
            except Exception as e:
                bot_status['issues'].append(f"Ошибка конфигурации: {str(e)}")
                bot_status['status'] = 'critical'
            
            return bot_status
            
        except Exception as e:
            logger.error(f"Ошибка проверки статуса бота: {e}")
            return {
                'status': 'error',
                'details': {},
                'issues': [f"Ошибка проверки: {str(e)}"]
            }
    
    async def _check_database_status(self) -> Dict:
        """Проверка статуса базы данных"""
        try:
            db_status = {
                'status': 'unknown',
                'details': {},
                'issues': []
            }
            
            # Проверяем подключение
            if await self.db.is_connected():
                db_status['status'] = 'ok'
                db_status['details']['connection'] = 'Подключение активно'
            else:
                db_status['status'] = 'critical'
                db_status['issues'].append("Нет подключения к БД")
                return db_status
            
            # Проверяем таблицы
            try:
                total_users = await self.db.get_total_users()
                db_status['details']['users_count'] = total_users
                
                # Проверяем целостность
                if total_users >= 0:
                    db_status['details']['integrity'] = 'Данные корректны'
                else:
                    db_status['issues'].append("Проблемы с целостностью данных")
                    db_status['status'] = 'warning'
                    
            except Exception as e:
                db_status['issues'].append(f"Ошибка чтения данных: {str(e)}")
                db_status['status'] = 'critical'
            
            # Проверяем размер файла БД
            try:
                db_path = self.config.DB_PATH
                if os.path.exists(db_path):
                    size_mb = os.path.getsize(db_path) / (1024 * 1024)
                    db_status['details']['size_mb'] = f"{size_mb:.2f} МБ"
                    
                    if size_mb > 100:  # Предупреждение при большом размере
                        db_status['issues'].append("Большой размер БД")
                        if db_status['status'] == 'ok':
                            db_status['status'] = 'warning'
                else:
                    db_status['issues'].append("Файл БД не найден")
                    db_status['status'] = 'critical'
                    
            except Exception as e:
                db_status['issues'].append(f"Ошибка проверки размера БД: {str(e)}")
            
            return db_status
            
        except Exception as e:
            logger.error(f"Ошибка проверки БД: {e}")
            return {
                'status': 'error',
                'details': {},
                'issues': [f"Ошибка проверки БД: {str(e)}"]
            }
    
    async def _check_system_status(self) -> Dict:
        """Проверка системного статуса"""
        try:
            system_status = {
                'status': 'unknown',
                'details': {},
                'issues': []
            }
            
            # Проверяем использование CPU
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                system_status['details']['cpu_percent'] = f"{cpu_percent:.1f}%"
                
                if cpu_percent > 80:
                    system_status['issues'].append("Высокая нагрузка CPU")
                    system_status['status'] = 'warning'
                elif cpu_percent > 95:
                    system_status['issues'].append("Критическая нагрузка CPU")
                    system_status['status'] = 'critical'
                else:
                    system_status['status'] = 'ok'
                    
            except Exception as e:
                system_status['issues'].append(f"Ошибка проверки CPU: {str(e)}")
            
            # Проверяем использование памяти
            try:
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                system_status['details']['memory_percent'] = f"{memory_percent:.1f}%"
                system_status['details']['memory_available'] = f"{memory.available / (1024**3):.1f} ГБ"
                
                if memory_percent > 80:
                    system_status['issues'].append("Высокое использование памяти")
                    if system_status['status'] == 'ok':
                        system_status['status'] = 'warning'
                elif memory_percent > 95:
                    system_status['issues'].append("Критическое использование памяти")
                    system_status['status'] = 'critical'
                    
            except Exception as e:
                system_status['issues'].append(f"Ошибка проверки памяти: {str(e)}")
            
            # Проверяем диск
            try:
                disk = psutil.disk_usage('.')
                disk_percent = (disk.used / disk.total) * 100
                system_status['details']['disk_percent'] = f"{disk_percent:.1f}%"
                system_status['details']['disk_free'] = f"{disk.free / (1024**3):.1f} ГБ"
                
                if disk_percent > 90:
                    system_status['issues'].append("Мало места на диске")
                    if system_status['status'] == 'ok':
                        system_status['status'] = 'warning'
                        
            except Exception as e:
                system_status['issues'].append(f"Ошибка проверки диска: {str(e)}")
            
            return system_status
            
        except Exception as e:
            logger.error(f"Ошибка проверки системы: {e}")
            return {
                'status': 'error',
                'details': {},
                'issues': [f"Ошибка проверки системы: {str(e)}"]
            }
    
    async def _check_performance_status(self) -> Dict:
        """Проверка производительности"""
        try:
            performance_status = {
                'status': 'unknown',
                'details': {},
                'issues': []
            }
            
            # Проверяем статистику пользователей
            try:
                total_users = await self.db.get_total_users()
                present_users = await self.db.get_present_users()
                absent_users = await self.db.get_absent_users_count()
                
                performance_status['details']['total_users'] = total_users
                performance_status['details']['present_users'] = present_users
                performance_status['details']['absent_users'] = absent_users
                
                if total_users > 0:
                    attendance_rate = (present_users / total_users) * 100
                    performance_status['details']['attendance_rate'] = f"{attendance_rate:.1f}%"
                    
                    if attendance_rate < 50:
                        performance_status['issues'].append("Низкая посещаемость")
                        performance_status['status'] = 'warning'
                    elif attendance_rate < 30:
                        performance_status['issues'].append("Критически низкая посещаемость")
                        performance_status['status'] = 'critical'
                    else:
                        performance_status['status'] = 'ok'
                else:
                    performance_status['status'] = 'ok'
                    performance_status['details']['attendance_rate'] = 'Нет данных'
                    
            except Exception as e:
                performance_status['issues'].append(f"Ошибка проверки статистики: {str(e)}")
                performance_status['status'] = 'error'
            
            # Проверяем последние события
            try:
                recent_events = await self.db.get_events(10)
                performance_status['details']['recent_events'] = len(recent_events)
                
                if len(recent_events) == 0:
                    performance_status['issues'].append("Нет активности")
                    if performance_status['status'] == 'ok':
                        performance_status['status'] = 'warning'
                        
            except Exception as e:
                performance_status['issues'].append(f"Ошибка проверки событий: {str(e)}")
            
            return performance_status
            
        except Exception as e:
            logger.error(f"Ошибка проверки производительности: {e}")
            return {
                'status': 'error',
                'details': {},
                'issues': [f"Ошибка проверки производительности: {str(e)}"]
            }
    
    def _determine_overall_status(self, health_data: Dict) -> str:
        """Определение общего статуса здоровья"""
        statuses = [
            health_data['bot_status']['status'],
            health_data['database_status']['status'],
            health_data['system_status']['status'],
            health_data['performance_status']['status']
        ]
        
        if 'critical' in statuses:
            return 'critical'
        elif 'error' in statuses:
            return 'error'
        elif 'warning' in statuses:
            return 'warning'
        elif all(status == 'ok' for status in statuses):
            return 'ok'
        else:
            return 'unknown'
    
    async def get_health_report(self) -> str:
        """Получение отчета о здоровье в текстовом формате"""
        try:
            health_data = await self.perform_health_check()
            
            report = f"🏥 *Отчет о здоровье бота*\n\n"
            report += f"📅 Дата: {health_data['timestamp'].strftime('%d.%m.%Y %H:%M:%S')}\n"
            report += f"📊 Общий статус: {self._get_status_emoji(health_data['overall_status'])} {health_data['overall_status'].upper()}\n\n"
            
            # Статус бота
            bot_status = health_data['bot_status']
            report += f"🤖 *Статус бота:* {self._get_status_emoji(bot_status['status'])}\n"
            for detail, value in bot_status['details'].items():
                report += f"  • {detail}: {value}\n"
            for issue in bot_status['issues']:
                report += f"  ⚠️ {issue}\n"
            report += "\n"
            
            # Статус БД
            db_status = health_data['database_status']
            report += f"🗄️ *База данных:* {self._get_status_emoji(db_status['status'])}\n"
            for detail, value in db_status['details'].items():
                report += f"  • {detail}: {value}\n"
            for issue in db_status['issues']:
                report += f"  ⚠️ {issue}\n"
            report += "\n"
            
            # Системный статус
            sys_status = health_data['system_status']
            report += f"🖥️ *Система:* {self._get_status_emoji(sys_status['status'])}\n"
            for detail, value in sys_status['details'].items():
                report += f"  • {detail}: {value}\n"
            for issue in sys_status['issues']:
                report += f"  ⚠️ {issue}\n"
            report += "\n"
            
            # Производительность
            perf_status = health_data['performance_status']
            report += f"📈 *Производительность:* {self._get_status_emoji(perf_status['status'])}\n"
            for detail, value in perf_status['details'].items():
                report += f"  • {detail}: {value}\n"
            for issue in perf_status['issues']:
                report += f"  ⚠️ {issue}\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка создания отчета о здоровье: {e}")
            return f"❌ Ошибка создания отчета: {str(e)}"
    
    def _get_status_emoji(self, status: str) -> str:
        """Получение эмодзи для статуса"""
        status_emojis = {
            'ok': '✅',
            'warning': '⚠️',
            'critical': '🚨',
            'error': '❌',
            'unknown': '❓'
        }
        return status_emojis.get(status, '❓')
    
    async def get_health_history(self, hours: int = 24) -> List[Dict]:
        """Получение истории здоровья за указанное время"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_history = [
                h for h in self.health_history 
                if h['timestamp'] >= cutoff_time
            ]
            return recent_history
        except Exception as e:
            logger.error(f"Ошибка получения истории здоровья: {e}")
            return []
    
    async def get_health_trends(self) -> Dict:
        """Получение трендов здоровья"""
        try:
            if len(self.health_history) < 2:
                return {'trend': 'insufficient_data'}
            
            # Анализируем последние 10 проверок
            recent_checks = self.health_history[-10:]
            
            status_counts = {}
            for check in recent_checks:
                status = check['overall_status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Определяем тренд
            if status_counts.get('critical', 0) > 0:
                trend = 'deteriorating'
            elif status_counts.get('warning', 0) > len(recent_checks) / 2:
                trend = 'concerning'
            elif status_counts.get('ok', 0) == len(recent_checks):
                trend = 'stable'
            else:
                trend = 'fluctuating'
            
            return {
                'trend': trend,
                'status_distribution': status_counts,
                'checks_analyzed': len(recent_checks)
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа трендов: {e}")
            return {'trend': 'error', 'error': str(e)}