import os
import json
import logging
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AutoRestartSystem:
    """Простая система учёта и управления перезапусками бота.

    Задачи:
      1. Хранить историю перезапусков в JSON-файле.
      2. Предоставлять статистику (кол-во, тренд, успешность).
      3. Выполнять принудительный и экстренный «перезапуск» (по факту –
         завершение процесса, чтобы оркестратор / runner запустил его
         заново).

    Реального рестарта процесса библиотека aiogram не предоставляет.
    Самый надёжный способ – корректно завершить процесс с нулевым кодом,
    дав внешней среде (Docker, systemd, Replit Runner и т. д.) возможность
    поднять его снова. В большинстве окружений достаточно вызвать
    ``os._exit(0)`` либо ``sys.exit(0)``.  Здесь мы используем ``os._exit``
    после небольшой задержки, чтобы успеть зафиксировать статистику.
    """

    _DEFAULT_LOG_PATH = os.path.join("data", "restart_log.json")
    _MAX_RESTARTS_PER_DAY = 10  # Порог, после которого считаем частые рестарты

    def __init__(self, log_path: str | None = None, max_restarts_per_day: int | None = None) -> None:
        self.log_path = log_path or self._DEFAULT_LOG_PATH
        self.max_restarts_per_day = max_restarts_per_day or self._MAX_RESTARTS_PER_DAY

        # Убеждаемся, что директория для лога существует.
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        # Инициализируем файл, если его нет.
        if not os.path.exists(self.log_path):
            self._save_log([])

    # ---------------------------------------------------------------------
    # Публичные coroutine-методы, вызываемые из AdminPanel
    # ---------------------------------------------------------------------

    async def get_restart_stats(self) -> Dict[str, Any]:
        """Возвращает агрегированную статистику по перезапускам."""
        try:
            records = self._load_log()
            total_restarts = len(records)
            now = datetime.utcnow()
            last_24h_threshold = now - timedelta(hours=24)
            restarts_last_24h = [r for r in records if self._parse_ts(r["timestamp"]) >= last_24h_threshold]

            successful_restarts = sum(1 for r in records if r.get("success", False))
            failed_restarts = total_restarts - successful_restarts
            last_restart_time: Optional[datetime] = None
            if records:
                last_restart_time = self._parse_ts(records[-1]["timestamp"])

            # Кол-во рестартов, которое ещё можно сделать, исходя из лимита.
            restarts_remaining = max(0, self.max_restarts_per_day - len(restarts_last_24h))

            trend = self._calculate_trend(len(restarts_last_24h))

            return {
                "total_restarts": total_restarts,
                "max_restarts": self.max_restarts_per_day,
                "restarts_remaining": restarts_remaining,
                "restarts_last_24h": len(restarts_last_24h),
                "successful_restarts": successful_restarts,
                "failed_restarts": failed_restarts,
                "last_restart_time": last_restart_time,
                "trend": trend,
            }
        except Exception as e:
            logger.exception("Ошибка получения статистики перезапусков")
            return {"error": str(e)}

    async def force_restart(self) -> bool:
        """Плановый (ручной) перезапуск."""
        return await self._restart(label="force", emergency=False)

    async def emergency_restart(self) -> bool:
        """Экстренный перезапуск – выполняется независимо от лимитов."""
        return await self._restart(label="emergency", emergency=True)

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    async def _restart(self, label: str, emergency: bool) -> bool:
        """Фиксирует рестарт и завершает процесс.

        Returns:
            bool: True – если удалось инициировать рестарт
        """
        try:
            # Проверяем лимиты, если это не emergency-рестарт.
            if not emergency:
                stats = await self.get_restart_stats()
                if stats.get("restarts_remaining", 0) <= 0:
                    logger.warning("Превышен лимит перезапусков за сутки – рестарт отклонён")
                    return False

            # Записываем событие рестарта.
            await self._record_restart(success=True, label=label)
            logger.info("Инициирован %s рестарт...", label)

            # Планируем завершение процесса через 0.5 с, чтобы успели отправиться логи.
            loop = asyncio.get_running_loop()
            loop.call_later(0.5, os._exit, 0)
            return True
        except Exception:
            logger.exception("Ошибка при попытке перезапуска")
            await self._record_restart(success=False, label=label)
            return False

    async def _record_restart(self, *, success: bool, label: str) -> None:
        """Добавляет запись о перезапуске в лог."""
        records = self._load_log()
        records.append({
            "timestamp": datetime.utcnow().isoformat(),
            "success": bool(success),
            "label": label,
        })
        self._save_log(records)

    def _load_log(self) -> List[Dict[str, Any]]:
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_log(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("Не удалось сохранить лог перезапусков")

    @staticmethod
    def _parse_ts(ts_str: str) -> datetime:
        # Используем fromisoformat, поддерживаемый с Python 3.7+
        return datetime.fromisoformat(ts_str)

    def _calculate_trend(self, restarts_24h: int) -> str:
        """Очень простая эвристика тренда по количеству рестартов за 24 ч."""
        if restarts_24h == 0:
            return "stable"
        if restarts_24h <= 3:
            return "moderate_restart_rate"
        if restarts_24h > 3:
            return "high_restart_rate"
        return "no_data"