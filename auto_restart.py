#!/usr/bin/env python3
"""
Система автоматического перезапуска бота
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class AutoRestartSystem:
    """Система автоматического перезапуска бота"""
    
    def __init__(self, db=None, notification_system=None):
        self.db = db
        self.notification_system = notification_system
        self.restart_flag_file = Path("restart_flag.tmp")
        self.restart_count = 0
        self.max_restarts = 5
        
    async def check_restart_conditions(self):
        """Проверяет условия для перезапуска"""
        try:
            # Проверяем флаг перезапуска
            if self.restart_flag_file.exists():
                logger.info("Найден флаг перезапуска")
                return True
                
            # Проверяем количество перезапусков
            if self.restart_count >= self.max_restarts:
                logger.warning(f"Превышено максимальное количество перезапусков: {self.max_restarts}")
                return False
                
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при проверке условий перезапуска: {e}")
            return False
    
    async def create_restart_flag(self):
        """Создает флаг для перезапуска"""
        try:
            with open(self.restart_flag_file, 'w') as f:
                f.write(f"restart_requested_at={datetime.now().isoformat()}\n")
            logger.info("Флаг перезапуска создан")
            
        except Exception as e:
            logger.error(f"Ошибка при создании флага перезапуска: {e}")
    
    async def remove_restart_flag(self):
        """Удаляет флаг перезапуска"""
        try:
            if self.restart_flag_file.exists():
                self.restart_flag_file.unlink()
                logger.info("Флаг перезапуска удален")
                
        except Exception as e:
            logger.error(f"Ошибка при удалении флага перезапуска: {e}")
    
    async def restart_bot(self):
        """Перезапускает бота"""
        try:
            logger.info("Начинаем перезапуск бота...")
            
            # Увеличиваем счетчик перезапусков
            self.restart_count += 1
            
            # Уведомляем о перезапуске
            if self.notification_system:
                await self.notification_system.send_admin_notification(
                    "🔄 Бот перезапускается...",
                    "system_restart"
                )
            
            # Удаляем флаг перезапуска
            await self.remove_restart_flag()
            
            # Перезапускаем процесс
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except Exception as e:
            logger.error(f"Ошибка при перезапуске бота: {e}")
            if self.notification_system:
                await self.notification_system.send_admin_notification(
                    f"❌ Ошибка перезапуска: {e}",
                    "system_error"
                )
    
    async def schedule_restart(self, delay_seconds=5):
        """Планирует перезапуск через указанное время"""
        try:
            logger.info(f"Планируем перезапуск через {delay_seconds} секунд")
            
            # Создаем флаг перезапуска
            await self.create_restart_flag()
            
            # Ждем указанное время
            await asyncio.sleep(delay_seconds)
            
            # Перезапускаем
            await self.restart_bot()
            
        except Exception as e:
            logger.error(f"Ошибка при планировании перезапуска: {e}")
    
    async def force_restart(self):
        """Принудительный перезапуск без проверок"""
        try:
            logger.warning("Принудительный перезапуск бота")
            
            if self.notification_system:
                await self.notification_system.send_admin_notification(
                    "⚠️ Принудительный перезапуск бота",
                    "force_restart"
                )
            
            # Сбрасываем счетчик
            self.restart_count = 0
            
            # Перезапускаем
            await self.restart_bot()
            
        except Exception as e:
            logger.error(f"Ошибка при принудительном перезапуске: {e}")
    
    async def get_restart_status(self):
        """Возвращает статус системы перезапуска"""
        return {
            "restart_count": self.restart_count,
            "max_restarts": self.max_restarts,
            "restart_flag_exists": self.restart_flag_file.exists(),
            "can_restart": self.restart_count < self.max_restarts
        }
    
    async def reset_restart_count(self):
        """Сбрасывает счетчик перезапусков"""
        self.restart_count = 0
        logger.info("Счетчик перезапусков сброшен")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            await self.remove_restart_flag()
            logger.info("Система автоперезапуска очищена")
            
        except Exception as e:
            logger.error(f"Ошибка при очистке системы автоперезапуска: {e}")