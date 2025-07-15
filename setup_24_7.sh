#!/bin/bash

# 🚀 Быстрая настройка Telegram бота для работы 24/7
# Этот скрипт автоматически настраивает все необходимые компоненты

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Переменные
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BOT_USER="${BOT_USER:-$USER}"
BOT_DIR="${BOT_DIR:-$SCRIPT_DIR}"
SERVICE_NAME="telegram-bot"

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}🚀 НАСТРОЙКА TELEGRAM БОТА ДЛЯ РАБОТЫ 24/7${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
}

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

check_requirements() {
    log "Проверка системных требований..."
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 не найден. Установите Python 3.11+"
        exit 1
    fi
    
    # Проверка виртуального окружения
    if [[ ! -d "$BOT_DIR/venv" ]]; then
        error "Виртуальное окружение не найдено. Сначала запустите основную установку"
        exit 1
    fi
    
    # Проверка .env файла
    if [[ ! -f "$BOT_DIR/.env" ]]; then
        error ".env файл не найден. Настройте конфигурацию"
        exit 1
    fi
    
    log "✅ Системные требования выполнены"
}

setup_systemd_service() {
    log "Настройка systemd сервиса..."
    
    # Создание systemd сервиса
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot Service - Attendance Tracker
After=network.target network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_USER}
WorkingDirectory=${BOT_DIR}
Environment=PYTHONPATH=${BOT_DIR}
ExecStart=${BOT_DIR}/venv/bin/python main.py
ExecReload=/bin/kill -HUP \$MAINPID

# Restart policy
Restart=always
RestartSec=10
StartLimitBurst=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${BOT_DIR}/data ${BOT_DIR}/logs ${BOT_DIR}/exports ${BOT_DIR}/backups

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

# Resource limits
LimitNOFILE=4096
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагрузка systemd
    sudo systemctl daemon-reload
    
    # Включение автозапуска
    sudo systemctl enable ${SERVICE_NAME}
    
    log "✅ Systemd сервис настроен"
}

setup_backup_cron() {
    log "Настройка автоматических бэкапов..."
    
    # Создание директории для бэкапов
    mkdir -p "${BOT_DIR}/backups"
    
    # Делаем скрипт исполняемым
    chmod +x "${BOT_DIR}/scripts/backup_daily.sh"
    
    # Обновляем пути в скрипте
    sed -i "s|BOT_DIR=\".*\"|BOT_DIR=\"${BOT_DIR}\"|g" "${BOT_DIR}/scripts/backup_daily.sh"
    sed -i "s|BACKUP_DIR=\".*\"|BACKUP_DIR=\"${BOT_DIR}/backups\"|g" "${BOT_DIR}/scripts/backup_daily.sh"
    sed -i "s|LOG_FILE=\".*\"|LOG_FILE=\"${BOT_DIR}/logs/backup.log\"|g" "${BOT_DIR}/scripts/backup_daily.sh"
    
    # Добавление в crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * ${BOT_DIR}/scripts/backup_daily.sh") | crontab -
    
    log "✅ Автоматические бэкапы настроены (ежедневно в 2:00)"
}

setup_log_rotation() {
    log "Настройка ротации логов..."
    
    # Создание конфигурации logrotate
    sudo tee /etc/logrotate.d/${SERVICE_NAME} > /dev/null <<EOF
${BOT_DIR}/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ${BOT_USER} ${BOT_USER}
    postrotate
        systemctl reload ${SERVICE_NAME} > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log "✅ Ротация логов настроена"
}

setup_firewall() {
    log "Настройка файрвола..."
    
    # Проверка наличия ufw
    if command -v ufw &> /dev/null; then
        # Открываем порт для healthcheck
        sudo ufw allow 8000/tcp comment "Telegram Bot Healthcheck"
        log "✅ Файрвол настроен (порт 8000 открыт)"
    else
        warn "ufw не найден, пропускаем настройку файрвола"
    fi
}

install_monitoring_tools() {
    log "Установка инструментов мониторинга..."
    
    # Установка необходимых пакетов
    sudo apt update
    sudo apt install -y curl htop iotop
    
    # Установка дополнительных зависимостей для healthcheck
    source "${BOT_DIR}/venv/bin/activate"
    pip install aiohttp-cors
    
    log "✅ Инструменты мониторинга установлены"
}

test_configuration() {
    log "Тестирование конфигурации..."
    
    # Проверка синтаксиса Python
    cd "$BOT_DIR"
    source venv/bin/activate
    
    if python -m py_compile main.py; then
        log "✅ Синтаксис Python корректен"
    else
        error "Ошибка в синтаксисе Python"
        exit 1
    fi
    
    # Проверка конфигурации
    if python check_config.py; then
        log "✅ Конфигурация корректна"
    else
        error "Ошибка в конфигурации"
        exit 1
    fi
    
    # Проверка systemd сервиса
    if sudo systemctl is-enabled ${SERVICE_NAME} &> /dev/null; then
        log "✅ Systemd сервис готов"
    else
        error "Проблема с systemd сервисом"
        exit 1
    fi
}

start_services() {
    log "Запуск сервисов..."
    
    # Остановка если работает
    sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true
    
    # Запуск сервиса
    sudo systemctl start ${SERVICE_NAME}
    
    # Проверка статуса
    sleep 5
    if sudo systemctl is-active ${SERVICE_NAME} &> /dev/null; then
        log "✅ Сервис успешно запущен"
    else
        error "Сервис не запустился"
        sudo systemctl status ${SERVICE_NAME}
        exit 1
    fi
}

show_status() {
    echo
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
    echo -e "${GREEN}✅ Статус сервиса:${NC}"
    sudo systemctl status ${SERVICE_NAME} --no-pager -l
    echo
    echo -e "${GREEN}📊 Полезные команды:${NC}"
    echo -e "${YELLOW}  sudo systemctl start ${SERVICE_NAME}${NC}      - Запустить бота"
    echo -e "${YELLOW}  sudo systemctl stop ${SERVICE_NAME}${NC}       - Остановить бота"
    echo -e "${YELLOW}  sudo systemctl restart ${SERVICE_NAME}${NC}    - Перезапустить бота"
    echo -e "${YELLOW}  sudo systemctl status ${SERVICE_NAME}${NC}     - Статус бота"
    echo -e "${YELLOW}  sudo journalctl -u ${SERVICE_NAME} -f${NC}     - Просмотр логов"
    echo
    echo -e "${GREEN}🔗 Эндпоинты мониторинга:${NC}"
    echo -e "${YELLOW}  http://localhost:8000/health${NC}              - Проверка здоровья"
    echo -e "${YELLOW}  http://localhost:8000/status${NC}              - Статус системы"
    echo -e "${YELLOW}  http://localhost:8000/metrics${NC}             - Метрики"
    echo
    echo -e "${GREEN}📋 Автоматические процессы:${NC}"
    echo -e "${YELLOW}  • Автозапуск при перезагрузке сервера${NC}"
    echo -e "${YELLOW}  • Автоматический перезапуск при сбоях${NC}"
    echo -e "${YELLOW}  • Ежедневные бэкапы в 2:00${NC}"
    echo -e "${YELLOW}  • Автоматическая ротация логов${NC}"
    echo
    echo -e "${GREEN}🔄 Для проверки через 30 секунд:${NC}"
    echo -e "${YELLOW}  curl http://localhost:8000/health${NC}"
    echo
}

# Основная функция
main() {
    print_header
    
    # Проверка прав sudo
    if ! sudo -n true 2>/dev/null; then
        error "Требуются sudo права для настройки системных сервисов"
        exit 1
    fi
    
    check_requirements
    setup_systemd_service
    setup_backup_cron
    setup_log_rotation
    setup_firewall
    install_monitoring_tools
    test_configuration
    start_services
    show_status
    
    log "🎉 Ваш Telegram бот готов к работе 24/7!"
}

# Обработка сигналов
trap 'error "Установка прервана"; exit 1' INT TERM

# Проверка аргументов
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Использование: $0 [OPTIONS]"
    echo
    echo "Опции:"
    echo "  --help, -h     Показать справку"
    echo "  --user USER    Пользователь для сервиса (по умолчанию: $USER)"
    echo "  --dir DIR      Директория бота (по умолчанию: текущая)"
    echo
    exit 0
fi

# Обработка аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            BOT_USER="$2"
            shift 2
            ;;
        --dir)
            BOT_DIR="$2"
            shift 2
            ;;
        *)
            error "Неизвестный аргумент: $1"
            exit 1
            ;;
    esac
done

# Запуск основной функции
main