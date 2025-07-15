#!/bin/bash

# Telegram Bot - Daily Backup Script
# Добавьте в crontab: 0 2 * * * /path/to/backup_daily.sh

set -euo pipefail

# Конфигурация
BOT_DIR="/home/ubuntu/telegram-bot"
BACKUP_DIR="/home/ubuntu/telegram-bot/backups"
LOG_FILE="/home/ubuntu/telegram-bot/logs/backup.log"
RETENTION_DAYS=7

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Функция для отправки уведомлений
send_notification() {
    local message="$1"
    local severity="${2:-info}"
    
    # Отправка в Telegram (если настроен webhook)
    if [[ -n "${WEBHOOK_URL:-}" ]]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🔄 Backup: $message\",\"severity\":\"$severity\"}" \
            --silent --show-error || true
    fi
}

# Проверка что скрипт запущен не от root
if [[ $EUID -eq 0 ]]; then
    log "ERROR: Не запускайте скрипт от root"
    exit 1
fi

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Переход в директорию бота
cd "$BOT_DIR"

log "Начинаю создание backup..."

# Создание timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_daily_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Создание директории для текущего бэкапа
mkdir -p "$BACKUP_PATH"

# Активация виртуального окружения
source venv/bin/activate

# Создание бэкапа базы данных
log "Создание бэкапа базы данных..."
if [[ -f "data/bot_database.db" ]]; then
    cp "data/bot_database.db" "$BACKUP_PATH/bot_database.db"
    log "✅ База данных скопирована"
else
    log "⚠️  База данных не найдена"
fi

# Создание бэкапа конфигурации
log "Создание бэкапа конфигурации..."
cp .env "$BACKUP_PATH/.env" 2>/dev/null || log "⚠️  .env файл не найден"
cp requirements.txt "$BACKUP_PATH/" 2>/dev/null || true

# Создание бэкапа логов (последние 1000 строк)
log "Создание бэкапа логов..."
if [[ -f "logs/bot.log" ]]; then
    tail -n 1000 "logs/bot.log" > "$BACKUP_PATH/bot.log"
    log "✅ Логи скопированы"
fi

# Создание архива
log "Создание архива..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME/"

# Проверка размера архива
ARCHIVE_SIZE=$(du -h "$BACKUP_NAME.tar.gz" | cut -f1)
log "📦 Размер архива: $ARCHIVE_SIZE"

# Удаление временной директории
rm -rf "$BACKUP_NAME"

# Проверка целостности архива
log "Проверка целостности архива..."
if tar -tzf "$BACKUP_NAME.tar.gz" >/dev/null 2>&1; then
    log "✅ Архив создан успешно"
    send_notification "Backup создан успешно ($ARCHIVE_SIZE)" "success"
else
    log "❌ Ошибка создания архива"
    send_notification "Ошибка создания backup" "error"
    exit 1
fi

# Очистка старых бэкапов
log "Очистка старых бэкапов (старше $RETENTION_DAYS дней)..."
find "$BACKUP_DIR" -name "backup_daily_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
OLD_BACKUPS_COUNT=$(find "$BACKUP_DIR" -name "backup_daily_*.tar.gz" -type f | wc -l)
log "📊 Осталось бэкапов: $OLD_BACKUPS_COUNT"

# Опционально: загрузка в облако
if [[ -n "${CLOUD_BACKUP_ENABLED:-}" && "$CLOUD_BACKUP_ENABLED" == "true" ]]; then
    log "Загрузка в облачное хранилище..."
    
    # AWS S3
    if [[ -n "${AWS_S3_BUCKET:-}" ]]; then
        aws s3 cp "$BACKUP_NAME.tar.gz" "s3://$AWS_S3_BUCKET/backups/" && \
        log "✅ Загружено в S3" || \
        log "❌ Ошибка загрузки в S3"
    fi
    
    # Google Cloud Storage
    if [[ -n "${GCS_BUCKET:-}" ]]; then
        gsutil cp "$BACKUP_NAME.tar.gz" "gs://$GCS_BUCKET/backups/" && \
        log "✅ Загружено в GCS" || \
        log "❌ Ошибка загрузки в GCS"
    fi
fi

# Статистика использования диска
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}')
log "💾 Использование диска: $DISK_USAGE"

# Проверка работы бота
log "Проверка статуса бота..."
if python -c "
import asyncio
import sys
sys.path.append('.')
from monitoring import BotHealthMonitor
from database import Database

async def check():
    db = Database()
    await db.init()
    monitor = BotHealthMonitor(db)
    health = await monitor.perform_health_check()
    print(f'Bot status: {health[\"overall_status\"]}')
    return health['overall_status'] == 'healthy'

result = asyncio.run(check())
sys.exit(0 if result else 1)
" 2>/dev/null; then
    log "✅ Бот работает нормально"
else
    log "⚠️  Бот может иметь проблемы"
    send_notification "Бот может иметь проблемы после backup" "warning"
fi

log "🎉 Backup завершен успешно!"

# Отправка итогового отчета
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "backup_daily_*.tar.gz" -type f | wc -l)
send_notification "Backup завершен. Размер: $ARCHIVE_SIZE, Всего бэкапов: $TOTAL_BACKUPS" "success"