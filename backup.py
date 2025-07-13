"""
Система резервного копирования для бота
"""

import os
import shutil
import sqlite3
import logging
import zipfile
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import aiosqlite

logger = logging.getLogger(__name__)

class BackupSystem:
    """Система резервного копирования"""
    
    def __init__(self, db_path: str = 'data/bot_database.db'):
        self.db_path = db_path
        self.backup_dir = 'backups'
        self.max_backups = 10  # Максимальное количество бэкапов
        
        # Создаем директорию для бэкапов
        os.makedirs(self.backup_dir, exist_ok=True)
    
    async def create_backup(self, backup_type: str = 'manual') -> Dict:
        """Создание резервной копии"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{backup_type}_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Создаем директорию для бэкапа
            os.makedirs(backup_path, exist_ok=True)
            
            backup_info = {
                'timestamp': timestamp,
                'type': backup_type,
                'name': backup_name,
                'path': backup_path,
                'files': [],
                'size': 0,
                'status': 'creating'
            }
            
            # Копируем базу данных
            if await self._backup_database(backup_path, backup_info):
                backup_info['files'].append('database.db')
            
            # Копируем конфигурационные файлы
            if self._backup_config_files(backup_path, backup_info):
                backup_info['files'].extend(['config.py', 'notifications.json'])
            
            # Копируем логи
            if self._backup_logs(backup_path, backup_info):
                backup_info['files'].append('logs/')
            
            # Создаем архив
            archive_path = await self._create_archive(backup_path, backup_name)
            if archive_path:
                backup_info['archive_path'] = archive_path
                backup_info['size'] = os.path.getsize(archive_path)
                backup_info['status'] = 'completed'
                
                # Удаляем временную директорию
                shutil.rmtree(backup_path)
                
                # Очищаем старые бэкапы
                await self._cleanup_old_backups()
                
                logger.info(f"✅ Резервная копия создана: {backup_name}")
                return backup_info
            else:
                backup_info['status'] = 'failed'
                logger.error("❌ Ошибка создания архива бэкапа")
                return backup_info
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания бэкапа: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    async def _backup_database(self, backup_path: str, backup_info: Dict) -> bool:
        """Резервное копирование базы данных"""
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"Файл БД не найден: {self.db_path}")
                return False
            
            # Создаем копию БД
            db_backup_path = os.path.join(backup_path, 'database.db')
            
            # Копируем файл БД
            shutil.copy2(self.db_path, db_backup_path)
            
            # Проверяем целостность копии
            if await self._verify_database_backup(db_backup_path):
                backup_info['db_size'] = os.path.getsize(db_backup_path)
                return True
            else:
                logger.error("❌ Ошибка верификации копии БД")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка копирования БД: {e}")
            return False
    
    async def _verify_database_backup(self, db_path: str) -> bool:
        """Проверка целостности резервной копии БД"""
        try:
            async with aiosqlite.connect(db_path) as conn:
                # Проверяем основные таблицы
                tables = ['users', 'attendance', 'events', 'notification_settings']
                for table in tables:
                    async with conn.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
                        row = await cursor.fetchone()
                        if row is None:
                            return False
                return True
        except Exception as e:
            logger.error(f"Ошибка верификации БД: {e}")
            return False
    
    def _backup_config_files(self, backup_path: str, backup_info: Dict) -> bool:
        """Резервное копирование конфигурационных файлов"""
        try:
            config_dir = os.path.join(backup_path, 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            # Копируем config.py
            if os.path.exists('config.py'):
                shutil.copy2('config.py', os.path.join(config_dir, 'config.py'))
            
            # Копируем notifications.json
            notifications_path = 'config/notifications.json'
            if os.path.exists(notifications_path):
                shutil.copy2(notifications_path, os.path.join(config_dir, 'notifications.json'))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка копирования конфигурации: {e}")
            return False
    
    def _backup_logs(self, backup_path: str, backup_info: Dict) -> bool:
        """Резервное копирование логов"""
        try:
            logs_dir = os.path.join(backup_path, 'logs')
            if os.path.exists('logs'):
                shutil.copytree('logs', logs_dir, dirs_exist_ok=True)
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка копирования логов: {e}")
            return False
    
    async def _create_archive(self, backup_path: str, backup_name: str) -> Optional[str]:
        """Создание архива бэкапа"""
        try:
            archive_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            return archive_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания архива: {e}")
            return None
    
    async def _cleanup_old_backups(self):
        """Очистка старых резервных копий"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Сортируем по времени создания (новые первыми)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Удаляем лишние бэкапы
            if len(backup_files) > self.max_backups:
                for file_path, _ in backup_files[self.max_backups:]:
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ Удален старый бэкап: {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка удаления бэкапа {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых бэкапов: {e}")
    
    async def restore_backup(self, backup_name: str) -> Dict:
        """Восстановление из резервной копии"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            if not os.path.exists(backup_path):
                return {
                    'status': 'error',
                    'error': 'Резервная копия не найдена'
                }
            
            # Создаем временную директорию для восстановления
            temp_dir = os.path.join(self.backup_dir, 'temp_restore')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Распаковываем архив
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            restore_info = {
                'backup_name': backup_name,
                'status': 'restoring',
                'files_restored': []
            }
            
            # Восстанавливаем базу данных
            db_backup_path = os.path.join(temp_dir, 'database.db')
            if os.path.exists(db_backup_path):
                # Создаем бэкап текущей БД
                current_backup = f"{self.db_path}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if os.path.exists(self.db_path):
                    shutil.copy2(self.db_path, current_backup)
                
                # Восстанавливаем БД
                shutil.copy2(db_backup_path, self.db_path)
                restore_info['files_restored'].append('database.db')
            
            # Восстанавливаем конфигурацию
            config_backup_dir = os.path.join(temp_dir, 'config')
            if os.path.exists(config_backup_dir):
                if os.path.exists(os.path.join(config_backup_dir, 'config.py')):
                    shutil.copy2(os.path.join(config_backup_dir, 'config.py'), 'config.py')
                    restore_info['files_restored'].append('config.py')
                
                if os.path.exists(os.path.join(config_backup_dir, 'notifications.json')):
                    os.makedirs('config', exist_ok=True)
                    shutil.copy2(os.path.join(config_backup_dir, 'notifications.json'), 'config/notifications.json')
                    restore_info['files_restored'].append('notifications.json')
            
            # Очищаем временную директорию
            shutil.rmtree(temp_dir)
            
            restore_info['status'] = 'completed'
            logger.info(f"✅ Восстановление завершено: {backup_name}")
            
            return restore_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def list_backups(self) -> List[Dict]:
        """Получение списка резервных копий"""
        try:
            backups = []
            
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    file_stat = os.stat(file_path)
                    
                    backup_info = {
                        'name': file,
                        'size': file_stat.st_size,
                        'created': datetime.fromtimestamp(file_stat.st_ctime),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime)
                    }
                    
                    # Извлекаем тип бэкапа из имени
                    if 'manual' in file:
                        backup_info['type'] = 'manual'
                    elif 'auto' in file:
                        backup_info['type'] = 'auto'
                    elif 'scheduled' in file:
                        backup_info['type'] = 'scheduled'
                    else:
                        backup_info['type'] = 'unknown'
                    
                    backups.append(backup_info)
            
            # Сортируем по времени создания (новые первыми)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка бэкапов: {e}")
            return []
    
    async def get_backup_info(self, backup_name: str) -> Optional[Dict]:
        """Получение информации о конкретном бэкапе"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            if not os.path.exists(backup_path):
                return None
            
            file_stat = os.stat(backup_path)
            
            # Читаем содержимое архива
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                file_list = zipf.namelist()
                total_size = sum(zipf.getinfo(f).file_size for f in file_list)
            
            return {
                'name': backup_name,
                'size': file_stat.st_size,
                'compressed_size': total_size,
                'files_count': len(file_list),
                'files': file_list,
                'created': datetime.fromtimestamp(file_stat.st_ctime),
                'modified': datetime.fromtimestamp(file_stat.st_mtime)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о бэкапе: {e}")
            return None
    
    async def delete_backup(self, backup_name: str) -> bool:
        """Удаление резервной копии"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
                logger.info(f"🗑️ Удален бэкап: {backup_name}")
                return True
            else:
                logger.warning(f"Бэкап не найден: {backup_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления бэкапа: {e}")
            return False
    
    async def create_scheduled_backup(self) -> Dict:
        """Создание запланированного бэкапа"""
        return await self.create_backup('scheduled')
    
    async def create_auto_backup(self) -> Dict:
        """Создание автоматического бэкапа"""
        return await self.create_backup('auto')
    
    def format_backup_size(self, size_bytes: int) -> str:
        """Форматирование размера файла"""
        if size_bytes == 0:
            return "0 Б"
        
        size_names = ["Б", "КБ", "МБ", "ГБ"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    async def get_backup_stats(self) -> Dict:
        """Получение статистики бэкапов"""
        try:
            backups = await self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size': 0,
                    'oldest_backup': None,
                    'newest_backup': None,
                    'backup_types': {}
                }
            
            total_size = sum(b['size'] for b in backups)
            oldest_backup = min(b['created'] for b in backups)
            newest_backup = max(b['created'] for b in backups)
            
            # Статистика по типам
            backup_types = {}
            for backup in backups:
                backup_type = backup['type']
                if backup_type not in backup_types:
                    backup_types[backup_type] = {
                        'count': 0,
                        'total_size': 0
                    }
                backup_types[backup_type]['count'] += 1
                backup_types[backup_type]['total_size'] += backup['size']
            
            return {
                'total_backups': len(backups),
                'total_size': total_size,
                'total_size_formatted': self.format_backup_size(total_size),
                'oldest_backup': oldest_backup,
                'newest_backup': newest_backup,
                'backup_types': backup_types
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики бэкапов: {e}")
            return {
                'error': str(e)
            }