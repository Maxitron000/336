import asyncio
import os
import sys
import signal
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from database import Database
from config import Config

logger = logging.getLogger(__name__)

class AutoRestartSystem:
    """Система автоматического перезапуска бота"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.restart_interval = self.config.AUTO_RESTART_INTERVAL
        self.restart_count = 0
        self.last_restart_time: Optional[datetime] = None
        self.max_restarts_per_day = 10
        self.failed_restarts = 0
        self.successful_restarts = 0
        
    async def get_restart_stats(self) -> Dict[str, Any]:
        """Получить статистику перезапусков"""
        try:
            # Получаем данные из базы данных о перезапусках за последние 24 часа
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            
            # Здесь можно добавить запрос к базе данных для получения реальной статистики
            # Пока возвращаем базовые значения
            
            restarts_last_24h = await self._get_restarts_last_24h()
            
            return {
                'total_restarts': self.restart_count,
                'max_restarts': self.max_restarts_per_day,
                'restarts_remaining': max(0, self.max_restarts_per_day - restarts_last_24h),
                'restarts_last_24h': restarts_last_24h,
                'successful_restarts': self.successful_restarts,
                'failed_restarts': self.failed_restarts,
                'last_restart_time': self.last_restart_time,
                'restart_rate': self._calculate_restart_rate()
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики перезапусков: {e}")
            return {
                'total_restarts': 0,
                'max_restarts': self.max_restarts_per_day,
                'restarts_remaining': self.max_restarts_per_day,
                'restarts_last_24h': 0,
                'successful_restarts': 0,
                'failed_restarts': 0,
                'last_restart_time': None,
                'restart_rate': 'normal'
            }
    
    async def force_restart(self) -> bool:
        """Принудительный перезапуск системы"""
        try:
            logger.info("Выполняется принудительный перезапуск...")
            
            # Логируем событие
            await self._log_restart_event("force_restart")
            
            # Обновляем счетчики
            self.restart_count += 1
            self.last_restart_time = datetime.now()
            
            # Запускаем процесс перезапуска в фоновом режиме
            asyncio.create_task(self._perform_restart())
            
            self.successful_restarts += 1
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при принудительном перезапуске: {e}")
            self.failed_restarts += 1
            return False
    
    async def emergency_restart(self) -> bool:
        """Экстренный перезапуск системы"""
        try:
            logger.warning("Выполняется экстренный перезапуск...")
            
            # Логируем событие
            await self._log_restart_event("emergency_restart")
            
            # Обновляем счетчики
            self.restart_count += 1
            self.last_restart_time = datetime.now()
            
            # Немедленный перезапуск без задержки
            asyncio.create_task(self._perform_emergency_restart())
            
            self.successful_restarts += 1
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при экстренном перезапуске: {e}")
            self.failed_restarts += 1
            return False
    
    async def _get_restarts_last_24h(self) -> int:
        """Получить количество перезапусков за последние 24 часа"""
        try:
            # Здесь можно добавить запрос к базе данных
            # Пока возвращаем приблизительное значение
            return min(self.restart_count, 5)
        except Exception as e:
            logger.error(f"Ошибка при получении статистики за 24 часа: {e}")
            return 0
    
    def _calculate_restart_rate(self) -> str:
        """Рассчитать интенсивность перезапусков"""
        restarts_last_24h = min(self.restart_count, 5)
        
        if restarts_last_24h <= 2:
            return 'normal'
        elif restarts_last_24h <= 5:
            return 'moderate'
        else:
            return 'high'
    
    async def _log_restart_event(self, restart_type: str):
        """Логировать событие перезапуска"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f"[{timestamp}] Перезапуск типа: {restart_type}"
            logger.info(message)
            
            # Можно добавить запись в базу данных
            # await self.db.log_event(None, restart_type, message)
            
        except Exception as e:
            logger.error(f"Ошибка при логировании события перезапуска: {e}")
    
    async def _perform_restart(self):
        """Выполнить перезапуск с задержкой"""
        try:
            # Даем время на завершение текущих операций
            await asyncio.sleep(3)
            
            logger.info("Перезапуск системы...")
            
            # Попытка грациозного завершения
            os.kill(os.getpid(), signal.SIGTERM)
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении перезапуска: {e}")
    
    async def _perform_emergency_restart(self):
        """Выполнить экстренный перезапуск"""
        try:
            # Минимальная задержка для экстренного перезапуска
            await asyncio.sleep(1)
            
            logger.warning("Экстренный перезапуск системы...")
            
            # Принудительное завершение
            os.kill(os.getpid(), signal.SIGKILL)
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении экстренного перезапуска: {e}")
    
    async def check_restart_conditions(self) -> bool:
        """Проверить условия для автоматического перезапуска"""
        try:
            # Проверяем, не превышен ли лимит перезапусков
            restarts_last_24h = await self._get_restarts_last_24h()
            
            if restarts_last_24h >= self.max_restarts_per_day:
                logger.warning("Превышен лимит перезапусков за 24 часа")
                return False
            
            # Можно добавить дополнительные условия
            # Например, проверку загрузки системы, памяти и т.д.
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при проверке условий перезапуска: {e}")
            return False
    
    async def schedule_restart(self, delay_seconds: int = 0):
        """Запланировать перезапуск через определенное время"""
        try:
            if delay_seconds > 0:
                logger.info(f"Перезапуск запланирован через {delay_seconds} секунд")
                await asyncio.sleep(delay_seconds)
            
            if await self.check_restart_conditions():
                await self.force_restart()
            else:
                logger.warning("Условия для перезапуска не выполнены")
                
        except Exception as e:
            logger.error(f"Ошибка при планировании перезапуска: {e}")