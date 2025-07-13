"""
Система экспорта данных для бота учета персонала
"""

import os
import csv
import logging
import io
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from io import BytesIO
import asyncio
import aiofiles

from database import get_location_logs, get_all_users, get_admin_logs, get_active_users_by_location
from utils import get_current_time, format_datetime, get_export_path

logger = logging.getLogger(__name__)

async def export_data(format_type: str, period: Optional[str] = None, user_filter: Optional[str] = None) -> Optional[str]:
    """
    Экспорт данных в указанном формате
    
    Args:
        format_type: Формат экспорта (csv, excel, pdf)
        period: Период для экспорта (day, week, month, all)
        user_filter: Фильтр по пользователю
    
    Returns:
        Путь к созданному файлу или None в случае ошибки
    """
    try:
        # Получаем данные для экспорта
        logs_data = get_location_logs(limit=10000, user_filter=user_filter)
        users_data = get_all_users()
        
        if not logs_data:
            logger.warning("Нет данных для экспорта")
            return None
        
        # Создаем директорию для экспорта
        export_dir = get_export_path()
        os.makedirs(export_dir, exist_ok=True)
        
        # Генерируем имя файла
        timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
        filename = f"personnel_export_{timestamp}"
        
        if format_type == "csv":
            return await export_to_csv(logs_data, users_data, export_dir, filename)
        elif format_type == "excel":
            return await export_to_excel(logs_data, users_data, export_dir, filename)
        elif format_type == "pdf":
            return await export_to_pdf(logs_data, users_data, export_dir, filename)
        else:
            logger.error(f"Неподдерживаемый формат экспорта: {format_type}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при экспорте данных: {e}")
        return None

async def export_to_csv(logs_data: List[Dict], users_data: List[Dict], export_dir: str, filename: str) -> str:
    """Экспорт данных в CSV формат"""
    try:
        filepath = os.path.join(export_dir, f"{filename}.csv")
        
        # Подготавливаем данные для экспорта
        export_data = []
        
        for log in logs_data:
            export_data.append({
                'Дата и время': format_datetime(log['timestamp']),
                'ФИО': log['full_name'],
                'Telegram ID': log['telegram_id'],
                'Действие': 'Прибыл' if log['action'] == 'arrived' else 'Покинул',
                'Локация': log['location']
            })
        
        # Формируем CSV в памяти
        output = io.StringIO()
        
        fieldnames = ['Дата и время', 'ФИО', 'Telegram ID', 'Действие', 'Локация']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(export_data)
        
        csv_content = output.getvalue()
        
        # Записываем асинхронно
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: open(filepath, 'w', encoding='utf-8').write(csv_content)
        )
        
        logger.info(f"Экспорт CSV завершен: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте в CSV: {e}")
        raise

async def export_to_excel(logs_data: List[Dict], users_data: List[Dict], export_dir: str, filename: str) -> str:
    """Экспорт данных в Excel формат"""
    try:
        filepath = os.path.join(export_dir, f"{filename}.xlsx")
        
        # Создаем Excel файл с несколькими листами
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Лист с журналом действий
            logs_df = pd.DataFrame([
                {
                    'Дата и время': format_datetime(log['timestamp']),
                    'ФИО': log['full_name'],
                    'Telegram ID': log['telegram_id'],
                    'Действие': 'Прибыл' if log['action'] == 'arrived' else 'Покинул',
                    'Локация': log['location']
                }
                for log in logs_data
            ])
            logs_df.to_excel(writer, sheet_name='Журнал действий', index=False)
            
            # Лист с пользователями
            users_df = pd.DataFrame([
                {
                    'ФИО': user['full_name'],
                    'Telegram ID': user['telegram_id'],
                    'Username': user.get('username', ''),
                    'Администратор': 'Да' if user.get('is_admin') else 'Нет',
                    'Дата регистрации': format_datetime(user['registered_at']) if user.get('registered_at') else '',
                    'Последняя активность': format_datetime(user['last_activity']) if user.get('last_activity') else ''
                }
                for user in users_data
            ])
            users_df.to_excel(writer, sheet_name='Пользователи', index=False)
            
            # Лист с текущими локациями
            active_locations = get_active_users_by_location()
            current_locations = []
            
            for location, users in active_locations.items():
                for user in users:
                    current_locations.append({
                        'ФИО': user['full_name'],
                        'Telegram ID': user['telegram_id'],
                        'Локация': location,
                        'Время прибытия': format_datetime(user['entered_at'])
                    })
            
            if current_locations:
                locations_df = pd.DataFrame(current_locations)
                locations_df.to_excel(writer, sheet_name='Текущие локации', index=False)
            
            # Лист со статистикой
            stats_data = generate_statistics_data(logs_data, users_data)
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)
        
        logger.info(f"Экспорт Excel завершен: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте в Excel: {e}")
        raise

async def export_to_pdf(logs_data: List[Dict], users_data: List[Dict], export_dir: str, filename: str) -> str:
    """Экспорт данных в PDF формат"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        filepath = os.path.join(export_dir, f"{filename}.pdf")
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
        )
        
        title = Paragraph("Отчет по учету персонала", title_style)
        story.append(title)
        
        # Информация о создании отчета
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
        )
        
        current_time = get_current_time()
        info_text = f"Отчет создан: {current_time.strftime('%d.%m.%Y %H:%M')}<br/>Всего записей: {len(logs_data)}<br/>Пользователей в системе: {len(users_data)}"
        info = Paragraph(info_text, info_style)
        story.append(info)
        
        # Таблица с журналом действий
        story.append(Paragraph("Журнал действий", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Подготавливаем данные для таблицы
        table_data = [['Дата и время', 'ФИО', 'Действие', 'Локация']]
        
        for log in logs_data[:50]:  # Ограничиваем количество записей для PDF
            table_data.append([
                format_datetime(log['timestamp'], 'short'),
                log['full_name'],
                'Прибыл' if log['action'] == 'arrived' else 'Покинул',
                log['location']
            ])
        
        # Создаем таблицу
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Статистика
        story.append(Spacer(1, 20))
        story.append(Paragraph("Статистика", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Получаем активные локации
        active_locations = get_active_users_by_location()
        
        if active_locations:
            stats_text = "<b>Текущее распределение по локациям:</b><br/>"
            for location, users in active_locations.items():
                stats_text += f"• {location}: {len(users)} чел.<br/>"
        else:
            stats_text = "Все локации пусты"
        
        stats = Paragraph(stats_text, styles['Normal'])
        story.append(stats)
        
        # Создаем PDF
        doc.build(story)
        
        logger.info(f"Экспорт PDF завершен: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте в PDF: {e}")
        raise

def generate_statistics_data(logs_data: List[Dict], users_data: List[Dict]) -> List[Dict]:
    """Генерация данных для статистики"""
    try:
        # Подсчитываем статистику по действиям
        actions_count = {}
        locations_count = {}
        users_activity = {}
        
        for log in logs_data:
            # Статистика по действиям
            action = 'Прибытие' if log['action'] == 'arrived' else 'Убытие'
            actions_count[action] = actions_count.get(action, 0) + 1
            
            # Статистика по локациям
            location = log['location']
            locations_count[location] = locations_count.get(location, 0) + 1
            
            # Статистика по пользователям
            user = log['full_name']
            users_activity[user] = users_activity.get(user, 0) + 1
        
        # Формируем данные для таблицы
        stats_data = []
        
        # Добавляем статистику по действиям
        stats_data.append({'Категория': 'Действия', 'Название': '', 'Количество': ''})
        for action, count in actions_count.items():
            stats_data.append({'Категория': '', 'Название': action, 'Количество': count})
        
        # Добавляем статистику по локациям
        stats_data.append({'Категория': 'Локации', 'Название': '', 'Количество': ''})
        for location, count in sorted(locations_count.items(), key=lambda x: x[1], reverse=True):
            stats_data.append({'Категория': '', 'Название': location, 'Количество': count})
        
        # Добавляем топ активных пользователей
        stats_data.append({'Категория': 'Активные пользователи', 'Название': '', 'Количество': ''})
        for user, count in sorted(users_activity.items(), key=lambda x: x[1], reverse=True)[:10]:
            stats_data.append({'Категория': '', 'Название': user, 'Количество': count})
        
        return stats_data
        
    except Exception as e:
        logger.error(f"Ошибка при генерации статистики: {e}")
        return []

async def export_admin_logs(format_type: str) -> Optional[str]:
    """Экспорт административных логов"""
    try:
        admin_logs = get_admin_logs(limit=1000)
        
        if not admin_logs:
            logger.warning("Нет административных логов для экспорта")
            return None
        
        export_dir = get_export_path()
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
        filename = f"admin_logs_{timestamp}"
        
        if format_type == "csv":
            filepath = os.path.join(export_dir, f"{filename}.csv")
            
            async with aiofiles.open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Дата и время', 'Администратор', 'Действие', 'Цель', 'Детали']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for log in admin_logs:
                    writer.writerow({
                        'Дата и время': format_datetime(log['timestamp']),
                        'Администратор': log['admin_name'],
                        'Действие': log['action'],
                        'Цель': log.get('target_name', ''),
                        'Детали': log.get('details', '')
                    })
            
            return filepath
            
        elif format_type == "excel":
            filepath = os.path.join(export_dir, f"{filename}.xlsx")
            
            df = pd.DataFrame([
                {
                    'Дата и время': format_datetime(log['timestamp']),
                    'Администратор': log['admin_name'],
                    'Действие': log['action'],
                    'Цель': log.get('target_name', ''),
                    'Детали': log.get('details', '')
                }
                for log in admin_logs
            ])
            
            df.to_excel(filepath, index=False)
            return filepath
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте административных логов: {e}")
        return None

async def export_users_data(format_type: str) -> Optional[str]:
    """Экспорт данных пользователей"""
    try:
        users_data = get_all_users()
        active_locations = get_active_users_by_location()
        
        if not users_data:
            logger.warning("Нет пользователей для экспорта")
            return None
        
        export_dir = get_export_path()
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
        filename = f"users_data_{timestamp}"
        
        # Подготавливаем данные с текущими локациями
        users_with_locations = []
        for user in users_data:
            current_location = None
            for location, location_users in active_locations.items():
                if any(u['telegram_id'] == user['telegram_id'] for u in location_users):
                    current_location = location
                    break
            
            users_with_locations.append({
                'ФИО': user['full_name'],
                'Telegram ID': user['telegram_id'],
                'Username': user.get('username', ''),
                'Администратор': 'Да' if user.get('is_admin') else 'Нет',
                'Текущая локация': current_location or 'Не указана',
                'Дата регистрации': format_datetime(user['registered_at']) if user.get('registered_at') else '',
                'Последняя активность': format_datetime(user['last_activity']) if user.get('last_activity') else ''
            })
        
        if format_type == "csv":
            filepath = os.path.join(export_dir, f"{filename}.csv")
            
            async with aiofiles.open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ФИО', 'Telegram ID', 'Username', 'Администратор', 'Текущая локация', 'Дата регистрации', 'Последняя активность']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(users_with_locations)
            
            return filepath
            
        elif format_type == "excel":
            filepath = os.path.join(export_dir, f"{filename}.xlsx")
            
            df = pd.DataFrame(users_with_locations)
            df.to_excel(filepath, index=False)
            return filepath
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте данных пользователей: {e}")
        return None

async def cleanup_old_exports(days_to_keep: int = 7):
    """Очистка старых файлов экспорта"""
    try:
        export_dir = get_export_path()
        
        if not os.path.exists(export_dir):
            return
        
        current_time = get_current_time()
        cutoff_time = current_time - timedelta(days=days_to_keep)
        
        deleted_count = 0
        for filename in os.listdir(export_dir):
            filepath = os.path.join(export_dir, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_time:
                    os.remove(filepath)
                    deleted_count += 1
        
        logger.info(f"Очищено {deleted_count} старых файлов экспорта")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке старых экспортов: {e}")

def get_export_info() -> Dict:
    """Получение информации о файлах экспорта"""
    try:
        export_dir = get_export_path()
        
        if not os.path.exists(export_dir):
            return {'files': [], 'total_size': 0}
        
        files = []
        total_size = 0
        
        for filename in os.listdir(export_dir):
            filepath = os.path.join(export_dir, filename)
            
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                files.append({
                    'name': filename,
                    'size': file_size,
                    'created': file_time.strftime('%d.%m.%Y %H:%M'),
                    'path': filepath
                })
                
                total_size += file_size
        
        # Сортируем по времени создания (новые первыми)
        files.sort(key=lambda x: x['created'], reverse=True)
        
        return {
            'files': files,
            'total_size': total_size,
            'count': len(files)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации об экспортах: {e}")
        return {'files': [], 'total_size': 0, 'count': 0}