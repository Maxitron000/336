#!/usr/bin/env python3
"""
Healthcheck сервер для Telegram бота
Предоставляет REST API для мониторинга состояния
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from aiohttp import web, ClientSession
from aiohttp.web import Response, Application
import aiohttp_cors

# Импорт компонентов бота
from database import Database
from config import Config
from monitoring import BotHealthMonitor

logger = logging.getLogger(__name__)

class HealthCheckServer:
    """HTTP сервер для healthcheck"""
    
    def __init__(self, bot, db: Database, monitor: BotHealthMonitor):
        self.bot = bot
        self.db = db
        self.monitor = monitor
        self.config = Config()
        self.start_time = time.time()
        self.app = self._create_app()
        
    def _create_app(self) -> Application:
        """Создание aiohttp приложения"""
        app = web.Application()
        
        # CORS настройки
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Маршруты
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/health/detailed', self.detailed_health_check)
        app.router.add_get('/metrics', self.metrics)
        app.router.add_get('/status', self.status)
        app.router.add_get('/version', self.version)
        app.router.add_get('/ready', self.readiness_check)
        app.router.add_get('/live', self.liveness_check)
        
        # Добавление CORS для всех маршрутов
        for route in list(app.router.routes()):
            cors.add(route)
            
        return app
    
    async def health_check(self, request) -> Response:
        """Базовая проверка здоровья"""
        try:
            # Простая проверка базы данных
            await self.db.execute_query("SELECT 1")
            
            # Проверка Telegram API
            await self.bot.get_me()
            
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.start_time,
                "version": "1.0.0"
            }
            
            return Response(
                text=json.dumps(health_data, indent=2),
                content_type="application/json",
                status=200
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
            error_data = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.start_time
            }
            
            return Response(
                text=json.dumps(error_data, indent=2),
                content_type="application/json",
                status=503
            )
    
    async def detailed_health_check(self, request) -> Response:
        """Детальная проверка здоровья"""
        try:
            health_data = await self.monitor.perform_health_check()
            
            # Конвертация datetime в строку для JSON
            for key, value in health_data.items():
                if isinstance(value, datetime):
                    health_data[key] = value.isoformat()
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, datetime):
                            value[sub_key] = sub_value.isoformat()
            
            status_code = 200 if health_data.get('overall_status') == 'healthy' else 503
            
            return Response(
                text=json.dumps(health_data, indent=2, default=str),
                content_type="application/json",
                status=status_code
            )
            
        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            
            error_data = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return Response(
                text=json.dumps(error_data, indent=2),
                content_type="application/json",
                status=500
            )
    
    async def metrics(self, request) -> Response:
        """Метрики в формате Prometheus"""
        try:
            # Получаем статистику из базы данных
            stats = await self._get_bot_stats()
            
            uptime = time.time() - self.start_time
            
            metrics = f"""# HELP bot_uptime_seconds Bot uptime in seconds
# TYPE bot_uptime_seconds gauge
bot_uptime_seconds {uptime}

# HELP bot_users_total Total number of users
# TYPE bot_users_total gauge
bot_users_total {stats.get('total_users', 0)}

# HELP bot_messages_total Total number of messages
# TYPE bot_messages_total counter
bot_messages_total {stats.get('total_messages', 0)}

# HELP bot_errors_total Total number of errors
# TYPE bot_errors_total counter
bot_errors_total {stats.get('total_errors', 0)}

# HELP bot_active_users_today Active users today
# TYPE bot_active_users_today gauge
bot_active_users_today {stats.get('active_users_today', 0)}
"""
            
            return Response(
                text=metrics,
                content_type="text/plain",
                status=200
            )
            
        except Exception as e:
            logger.error(f"Metrics generation failed: {e}")
            return Response(
                text=f"# Error generating metrics: {e}",
                content_type="text/plain",
                status=500
            )
    
    async def status(self, request) -> Response:
        """Краткий статус системы"""
        try:
            stats = await self._get_bot_stats()
            
            status_data = {
                "service": "telegram-bot",
                "status": "running",
                "uptime": time.time() - self.start_time,
                "users": stats.get('total_users', 0),
                "active_today": stats.get('active_users_today', 0),
                "timestamp": datetime.now().isoformat()
            }
            
            return Response(
                text=json.dumps(status_data, indent=2),
                content_type="application/json",
                status=200
            )
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def version(self, request) -> Response:
        """Информация о версии"""
        version_data = {
            "version": "1.0.0",
            "python_version": "3.13",
            "aiogram_version": "3.x",
            "build_date": "2024-01-01",
            "commit": "main"
        }
        
        return Response(
            text=json.dumps(version_data, indent=2),
            content_type="application/json",
            status=200
        )
    
    async def readiness_check(self, request) -> Response:
        """Проверка готовности к работе"""
        try:
            # Проверка подключения к базе данных
            await self.db.execute_query("SELECT 1")
            
            # Проверка Telegram API
            await self.bot.get_me()
            
            return Response(
                text="Ready",
                content_type="text/plain",
                status=200
            )
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return Response(
                text=f"Not ready: {e}",
                content_type="text/plain",
                status=503
            )
    
    async def liveness_check(self, request) -> Response:
        """Проверка жизнеспособности"""
        # Простая проверка что сервер отвечает
        return Response(
            text="Alive",
            content_type="text/plain",
            status=200
        )
    
    async def _get_bot_stats(self) -> Dict[str, Any]:
        """Получение статистики бота"""
        try:
            # Получаем статистику из базы данных
            total_users = await self.db.execute_query(
                "SELECT COUNT(*) FROM users"
            )
            
            # Активные пользователи за сегодня
            active_today = await self.db.execute_query(
                "SELECT COUNT(*) FROM user_activity WHERE date(timestamp) = date('now')"
            )
            
            return {
                'total_users': total_users[0][0] if total_users else 0,
                'active_users_today': active_today[0][0] if active_today else 0,
                'total_messages': 0,  # Можно добавить подсчет сообщений
                'total_errors': 0     # Можно добавить подсчет ошибок
            }
            
        except Exception as e:
            logger.error(f"Failed to get bot stats: {e}")
            return {}
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Запуск сервера"""
        logger.info(f"Starting healthcheck server on {host}:{port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"✅ Healthcheck server started on http://{host}:{port}")
        logger.info(f"   Health check: http://{host}:{port}/health")
        logger.info(f"   Detailed health: http://{host}:{port}/health/detailed")
        logger.info(f"   Metrics: http://{host}:{port}/metrics")
        logger.info(f"   Status: http://{host}:{port}/status")
        
        return runner