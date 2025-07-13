"""
Система автоматического перезапуска бота
"""

import os
import sys
import time
import signal
import logging
import asyncio
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil

logger = logging.getLogger(__name__)

class AutoRestartSystem:
    """Система автоматического перезапуска"""
    
    def __init__(self, max_restarts: int = 10, restart_delay: int = 30):
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.restart_count = 0
        self.last_restart_time = None
        self.is_running = True
        self.restart_history = []
        self.max_history_size = 50
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"Получен сигнал {signum}, завершаем работу...")
        self.is_running = False
    
    async def start_monitoring(self):
        """Запуск мониторинга и автоматического перезапуска"""
        logger.info("🚀 Запуск системы автоматического перезапуска")
        
        while self.is_running:
            try:
                # Проверяем, работает ли бот
                if not await self._is_bot_running():
                    logger.warning("⚠️ Бот не отвечает, инициируем перезапуск")
                    
                    if await self._should_restart():
                        await self._perform_restart()
                    else:
                        logger.error(f"❌ Превышено максимальное количество перезапусков ({self.max_restarts})")
                        break
                
                # Ждем перед следующей проверкой
                await asyncio.sleep(60)  # Проверяем каждую минуту
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(30)
    
    async def _is_bot_running(self) -> bool:
        """Проверка, работает ли бот"""
        try:
            # Проверяем процесс Python с main.py
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'main.py' in ' '.join(cmdline):
                        # Проверяем, что процесс активен
                        if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки процесса бота: {e}")
            return False
    
    async def _should_restart(self) -> bool:
        """Проверка, следует ли выполнить перезапуск"""
        # Проверяем лимит перезапусков
        if self.restart_count >= self.max_restarts:
            return False
        
        # Проверяем время с последнего перезапуска
        if self.last_restart_time:
            time_since_last = datetime.now() - self.last_restart_time
            if time_since_last.total_seconds() < self.restart_delay:
                logger.info(f"⏳ Ждем перед следующим перезапуском...")
                return False
        
        return True
    
    async def _perform_restart(self):
        """Выполнение перезапуска"""
        try:
            logger.info(f"🔄 Выполняем перезапуск #{self.restart_count + 1}")
            
            # Записываем информацию о перезапуске
            restart_info = {
                'timestamp': datetime.now(),
                'restart_number': self.restart_count + 1,
                'reason': 'bot_not_responding',
                'status': 'starting'
            }
            
            # Останавливаем текущий процесс бота
            await self._stop_bot_process()
            
            # Ждем немного
            await asyncio.sleep(5)
            
            # Запускаем новый процесс
            success = await self._start_bot_process()
            
            if success:
                restart_info['status'] = 'completed'
                logger.info("✅ Перезапуск выполнен успешно")
            else:
                restart_info['status'] = 'failed'
                logger.error("❌ Ошибка перезапуска")
            
            # Обновляем счетчики
            self.restart_count += 1
            self.last_restart_time = datetime.now()
            
            # Сохраняем в историю
            self.restart_history.append(restart_info)
            if len(self.restart_history) > self.max_history_size:
                self.restart_history.pop(0)
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(self.restart_delay)
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения перезапуска: {e}")
    
    async def _stop_bot_process(self):
        """Остановка процесса бота"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'main.py' in ' '.join(cmdline):
                        logger.info(f"🛑 Останавливаем процесс бота (PID: {proc.info['pid']})")
                        proc.terminate()
                        
                        # Ждем завершения процесса
                        try:
                            proc.wait(timeout=10)
                        except psutil.TimeoutExpired:
                            logger.warning("⚠️ Процесс не завершился, принудительно завершаем")
                            proc.kill()
                        
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка остановки процесса: {e}")
    
    async def _start_bot_process(self) -> bool:
        """Запуск процесса бота"""
        try:
            # Определяем команду запуска
            if os.path.exists('run_bot.py'):
                cmd = [sys.executable, 'run_bot.py']
            elif os.path.exists('main.py'):
                cmd = [sys.executable, 'main.py']
            else:
                logger.error("❌ Не найден файл для запуска бота")
                return False
            
            # Запускаем процесс
            logger.info(f"🚀 Запускаем бота: {' '.join(cmd)}")
            
            # Запускаем в фоновом режиме
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Ждем немного для инициализации
            await asyncio.sleep(10)
            
            # Проверяем, что процесс запустился
            if process.poll() is None:  # Процесс все еще работает
                logger.info(f"✅ Бот запущен (PID: {process.pid})")
                return True
            else:
                logger.error("❌ Процесс бота завершился сразу после запуска")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return False
    
    async def force_restart(self) -> bool:
        """Принудительный перезапуск"""
        try:
            logger.info("🔄 Выполняем принудительный перезапуск")
            
            await self._stop_bot_process()
            await asyncio.sleep(5)
            
            success = await self._start_bot_process()
            
            if success:
                logger.info("✅ Принудительный перезапуск выполнен успешно")
            else:
                logger.error("❌ Ошибка принудительного перезапуска")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка принудительного перезапуска: {e}")
            return False
    
    async def get_restart_stats(self) -> Dict:
        """Получение статистики перезапусков"""
        try:
            stats = {
                'total_restarts': self.restart_count,
                'max_restarts': self.max_restarts,
                'restarts_remaining': max(0, self.max_restarts - self.restart_count),
                'last_restart_time': self.last_restart_time,
                'is_running': self.is_running
            }
            
            # Анализируем историю перезапусков
            if self.restart_history:
                recent_restarts = [
                    r for r in self.restart_history 
                    if r['timestamp'] > datetime.now() - timedelta(hours=24)
                ]
                
                stats['restarts_last_24h'] = len(recent_restarts)
                stats['successful_restarts'] = len([r for r in self.restart_history if r['status'] == 'completed'])
                stats['failed_restarts'] = len([r for r in self.restart_history if r['status'] == 'failed'])
                
                # Определяем тренд
                if len(recent_restarts) > 5:
                    stats['trend'] = 'high_restart_rate'
                elif len(recent_restarts) > 2:
                    stats['trend'] = 'moderate_restart_rate'
                else:
                    stats['trend'] = 'stable'
            else:
                stats['restarts_last_24h'] = 0
                stats['successful_restarts'] = 0
                stats['failed_restarts'] = 0
                stats['trend'] = 'no_data'
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики перезапусков: {e}")
            return {'error': str(e)}
    
    async def get_restart_history(self, hours: int = 24) -> List[Dict]:
        """Получение истории перезапусков"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_history = [
                r for r in self.restart_history 
                if r['timestamp'] >= cutoff_time
            ]
            return recent_history
        except Exception as e:
            logger.error(f"Ошибка получения истории перезапусков: {e}")
            return []
    
    async def reset_restart_counter(self):
        """Сброс счетчика перезапусков"""
        try:
            old_count = self.restart_count
            self.restart_count = 0
            self.last_restart_time = None
            
            logger.info(f"🔄 Счетчик перезапусков сброшен (было: {old_count})")
            
        except Exception as e:
            logger.error(f"Ошибка сброса счетчика: {e}")
    
    async def update_restart_settings(self, max_restarts: int = None, restart_delay: int = None):
        """Обновление настроек перезапуска"""
        try:
            if max_restarts is not None:
                self.max_restarts = max_restarts
                logger.info(f"🔄 Максимальное количество перезапусков изменено на: {max_restarts}")
            
            if restart_delay is not None:
                self.restart_delay = restart_delay
                logger.info(f"🔄 Задержка перезапуска изменена на: {restart_delay} секунд")
            
        except Exception as e:
            logger.error(f"Ошибка обновления настроек: {e}")
    
    def format_restart_history(self, history: List[Dict]) -> str:
        """Форматирование истории перезапусков"""
        if not history:
            return "📋 История перезапусков пуста"
        
        message = "📋 *История перезапусков:*\n\n"
        
        for restart in history[-10:]:  # Показываем последние 10
            timestamp = restart['timestamp'].strftime('%d.%m %H:%M')
            status_emoji = "✅" if restart['status'] == 'completed' else "❌"
            
            message += f"{status_emoji} {timestamp}\n"
            message += f"🔄 Перезапуск #{restart['restart_number']}\n"
            message += f"📋 Статус: {restart['status']}\n"
            message += "─" * 20 + "\n"
        
        return message
    
    async def emergency_restart(self) -> bool:
        """Экстренный перезапуск с полной очисткой"""
        try:
            logger.warning("🚨 Выполняем экстренный перезапуск")
            
            # Останавливаем все процессы Python
            await self._stop_all_python_processes()
            
            # Ждем
            await asyncio.sleep(10)
            
            # Сбрасываем счетчики
            self.restart_count = 0
            self.last_restart_time = None
            
            # Запускаем заново
            success = await self._start_bot_process()
            
            if success:
                logger.info("✅ Экстренный перезапуск выполнен успешно")
            else:
                logger.error("❌ Ошибка экстренного перезапуска")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка экстренного перезапуска: {e}")
            return False
    
    async def _stop_all_python_processes(self):
        """Остановка всех процессов Python"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                        cmdline = proc.info['cmdline']
                        if cmdline and ('main.py' in ' '.join(cmdline) or 'run_bot.py' in ' '.join(cmdline)):
                            logger.info(f"🛑 Останавливаем процесс Python (PID: {proc.info['pid']})")
                            proc.terminate()
                            
                            try:
                                proc.wait(timeout=5)
                            except psutil.TimeoutExpired:
                                proc.kill()
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка остановки процессов Python: {e}")