#!/usr/bin/env python3
"""
🔄 Система автоматического перезапуска бота
"""

import asyncio
import logging
import os
import sys
import time
import signal
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AutoRestartSystem:
    """Система автоматического перезапуска бота"""
    
    def __init__(self):
        self.restart_count = 0
        self.last_restart_time = None
        self.restart_log = []
        self.max_restarts_per_hour = 10
        self.emergency_mode = False
        
    async def get_restart_stats(self) -> Dict:
        """Получение статистики перезапусков"""
        try:
            now = datetime.now()
            
            # Подсчитываем перезапуски за последний час
            recent_restarts = [
                restart for restart in self.restart_log
                if restart['time'] > now - timedelta(hours=1)
            ]
            
            # Время работы процесса
            process = psutil.Process(os.getpid())
            uptime = datetime.now() - datetime.fromtimestamp(process.create_time())
            
            stats = {
                'total_restarts': self.restart_count,
                'recent_restarts': len(recent_restarts),
                'last_restart': self.last_restart_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_restart_time else 'Никогда',
                'uptime': str(uptime).split('.')[0],
                'emergency_mode': self.emergency_mode,
                'memory_usage': f"{process.memory_info().rss / 1024 / 1024:.1f} MB",
                'cpu_percent': f"{process.cpu_percent():.1f}%",
                'pid': process.pid,
                'restart_history': self.restart_log[-5:] if self.restart_log else []
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики перезапусков: {e}")
            return {
                'total_restarts': self.restart_count,
                'recent_restarts': 0,
                'last_restart': 'Неизвестно',
                'uptime': 'Неизвестно',
                'emergency_mode': self.emergency_mode,
                'error': str(e)
            }
    
    async def force_restart(self) -> bool:
        """Принудительный перезапуск бота"""
        try:
            logger.info("🔄 Принудительный перезапуск бота...")
            
            # Проверяем лимит перезапусков
            if not self._check_restart_limit():
                logger.warning("❌ Превышен лимит перезапусков")
                return False
            
            # Записываем событие перезапуска
            self._log_restart("force", "Принудительный перезапуск через админ-панель")
            
            # Планируем перезапуск
            asyncio.create_task(self._perform_restart(delay=3))
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка принудительного перезапуска: {e}")
            return False
    
    async def emergency_restart(self) -> bool:
        """Экстренный перезапуск бота"""
        try:
            logger.critical("🚨 ЭКСТРЕННЫЙ ПЕРЕЗАПУСК БОТА!")
            
            # Включаем режим экстренного перезапуска
            self.emergency_mode = True
            
            # Записываем событие
            self._log_restart("emergency", "Экстренный перезапуск через админ-панель")
            
            # Немедленный перезапуск
            asyncio.create_task(self._perform_restart(delay=1))
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экстренного перезапуска: {e}")
            return False
    
    def _check_restart_limit(self) -> bool:
        """Проверка лимита перезапусков"""
        now = datetime.now()
        recent_restarts = [
            restart for restart in self.restart_log
            if restart['time'] > now - timedelta(hours=1)
        ]
        
        return len(recent_restarts) < self.max_restarts_per_hour
    
    def _log_restart(self, restart_type: str, reason: str):
        """Логирование перезапуска"""
        restart_info = {
            'time': datetime.now(),
            'type': restart_type,
            'reason': reason,
            'count': self.restart_count + 1
        }
        
        self.restart_log.append(restart_info)
        self.restart_count += 1
        self.last_restart_time = datetime.now()
        
        # Ограничиваем размер лога
        if len(self.restart_log) > 100:
            self.restart_log = self.restart_log[-50:]
    
    async def _perform_restart(self, delay: int = 5):
        """Выполнение перезапуска"""
        try:
            logger.info(f"⏳ Перезапуск через {delay} секунд...")
            await asyncio.sleep(delay)
            
            # Получаем путь к скрипту
            script_path = sys.argv[0]
            
            # Пытаемся перезапустить через системные команды
            if os.name == 'posix':  # Linux/Unix
                # Пытаемся найти подходящий скрипт перезапуска
                if os.path.exists('start_daily.sh'):
                    os.system('nohup ./start_daily.sh &')
                elif os.path.exists('start.py'):
                    os.system(f'nohup python3 start.py &')
                else:
                    os.system(f'nohup python3 {script_path} &')
            else:  # Windows
                os.system(f'start python {script_path}')
            
            # Завершаем текущий процесс
            logger.info("🔄 Завершение текущего процесса...")
            os.kill(os.getpid(), signal.SIGTERM)
            
        except Exception as e:
            logger.error(f"Ошибка выполнения перезапуска: {e}")
            
            # Аварийное завершение
            try:
                sys.exit(1)
            except:
                os._exit(1)
    
    def schedule_restart(self, delay_seconds: int = 300):
        """Планирование перезапуска"""
        try:
            logger.info(f"⏰ Запланирован перезапуск через {delay_seconds} секунд")
            
            self._log_restart("scheduled", f"Запланированный перезапуск через {delay_seconds} сек")
            
            # Создаем задачу перезапуска
            asyncio.create_task(self._perform_restart(delay=delay_seconds))
            
        except Exception as e:
            logger.error(f"Ошибка планирования перезапуска: {e}")
    
    def reset_emergency_mode(self):
        """Сброс режима экстренного перезапуска"""
        self.emergency_mode = False
        logger.info("✅ Режим экстренного перезапуска отключен")