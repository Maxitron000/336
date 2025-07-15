#!/usr/bin/env python3
"""
Система автоматического перезапуска для бота
"""

import os
import sys
import subprocess
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AutoRestartSystem:
    """Система автоматического перезапуска бота"""
    
    def __init__(self):
        self.restart_count = 0
        self.max_restarts = 50  # Максимальное количество перезапусков
        self.restart_times = []
        self.last_restart_time = None
        self.successful_restarts = 0
        self.failed_restarts = 0
        
    async def get_restart_stats(self) -> Dict:
        """Получение статистики перезапусков"""
        try:
            # Подсчет перезапусков за последние 24 часа
            now = datetime.now()
            last_24h = now - timedelta(hours=24)
            restarts_last_24h = len([t for t in self.restart_times if t > last_24h])
            
            # Определение тренда
            trend = "stable"
            if restarts_last_24h > 20:
                trend = "high_restart_rate"
            elif restarts_last_24h > 10:
                trend = "moderate_restart_rate"
            elif not self.restart_times:
                trend = "no_data"
            
            return {
                'total_restarts': len(self.restart_times),
                'max_restarts': self.max_restarts,
                'restarts_remaining': self.max_restarts - len(self.restart_times),
                'restarts_last_24h': restarts_last_24h,
                'successful_restarts': self.successful_restarts,
                'failed_restarts': self.failed_restarts,
                'last_restart_time': self.last_restart_time,
                'trend': trend
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики перезапусков: {e}")
            return {'error': str(e)}
    
    async def force_restart(self) -> bool:
        """Принудительный перезапуск бота"""
        try:
            logger.info("Выполняется принудительный перезапуск...")
            
            # Записываем время перезапуска
            self.last_restart_time = datetime.now()
            self.restart_times.append(self.last_restart_time)
            
            # Запускаем перезапуск в отдельном потоке, чтобы не блокировать
            asyncio.create_task(self._perform_restart())
            
            self.successful_restarts += 1
            return True
            
        except Exception as e:
            logger.error(f"Ошибка принудительного перезапуска: {e}")
            self.failed_restarts += 1
            return False
    
    async def emergency_restart(self) -> bool:
        """Экстренный перезапуск"""
        try:
            logger.warning("Выполняется экстренный перезапуск...")
            
            # Записываем время перезапуска
            self.last_restart_time = datetime.now()
            self.restart_times.append(self.last_restart_time)
            
            # Немедленный перезапуск
            asyncio.create_task(self._perform_emergency_restart())
            
            self.successful_restarts += 1
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экстренного перезапуска: {e}")
            self.failed_restarts += 1
            return False
    
    async def _perform_restart(self):
        """Выполнение перезапуска"""
        try:
            # Подождать немного перед перезапуском
            await asyncio.sleep(3)
            
            # Запустить скрипт перезапуска
            if os.path.exists("2_start.sh"):
                subprocess.Popen(["/bin/bash", "2_start.sh"])
            else:
                # Альтернативный способ
                subprocess.Popen([sys.executable, "main.py"])
            
            # Завершить текущий процесс
            await asyncio.sleep(1)
            os._exit(0)
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении перезапуска: {e}")
    
    async def _perform_emergency_restart(self):
        """Выполнение экстренного перезапуска"""
        try:
            # Немедленный перезапуск без ожидания
            if os.path.exists("2_start.sh"):
                subprocess.Popen(["/bin/bash", "2_start.sh"])
            else:
                subprocess.Popen([sys.executable, "main.py"])
            
            # Завершить процесс
            os._exit(0)
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении экстренного перезапуска: {e}")
    
    def restart_bot(self):
        """Обычный перезапуск (для совместимости со старым кодом)"""
        print(f"{datetime.now()}: Перезапуск бота...")
        
        # Останавливаем старый процесс
        subprocess.run("pkill -f 'python.*main.py'", shell=True)
        
        # Ждем немного
        time.sleep(5)
        
        # Запускаем новый процесс
        subprocess.Popen(["/bin/bash", "2_start.sh"])