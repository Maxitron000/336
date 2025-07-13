#!/bin/bash

# Скрипт для запуска бота на PythonAnywhere
# Автоматический перезапуск и мониторинг

# Настройки
BOT_DIR="/home/$(whoami)/personnel-bot"
LOG_FILE="$BOT_DIR/bot.log"
PID_FILE="$BOT_DIR/bot.pid"
MAX_RESTARTS=10
RESTART_DELAY=30

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Проверка существования директории
if [ ! -d "$BOT_DIR" ]; then
    error "Директория бота не найдена: $BOT_DIR"
    exit 1
fi

# Переход в директорию бота
cd "$BOT_DIR" || {
    error "Не удалось перейти в директорию бота"
    exit 1
}

# Проверка виртуального окружения
if [ ! -d "$VIRTUAL_ENV" ]; then
    warning "Виртуальное окружение не активировано"
    # Попытка активации
    source ~/.virtualenvs/personnel-bot/bin/activate 2>/dev/null || {
        error "Не удалось активировать виртуальное окружение"
        exit 1
    }
fi

# Проверка файла конфигурации
if [ ! -f ".env" ]; then
    error "Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

# Проверка зависимостей
if ! python -c "import aiogram, aiosqlite, aioschedule" 2>/dev/null; then
    warning "Зависимости не установлены. Устанавливаем..."
    pip install -r requirements.txt || {
        error "Не удалось установить зависимости"
        exit 1
    }
fi

# Функция остановки бота
stop_bot() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Останавливаем бота (PID: $pid)..."
            kill "$pid"
            sleep 5
            if kill -0 "$pid" 2>/dev/null; then
                warning "Бот не остановился, принудительно завершаем..."
                kill -9 "$pid"
            fi
        fi
        rm -f "$PID_FILE"
    fi
}

# Обработчик сигналов
cleanup() {
    log "Получен сигнал завершения..."
    stop_bot
    exit 0
}

trap cleanup SIGINT SIGTERM

# Основной цикл
restart_count=0

while [ $restart_count -lt $MAX_RESTARTS ]; do
    # Остановка предыдущего процесса
    stop_bot
    
    # Проверка рабочего времени (5:00-24:00)
    current_hour=$(date +%H)
    if [ "$current_hour" -lt 5 ] || [ "$current_hour" -gt 23 ]; then
        info "Вне рабочих часов (5:00-24:00). Ожидаем..."
        sleep 3600
        continue
    fi
    
    log "Запуск бота (попытка $((restart_count + 1))/$MAX_RESTARTS)..."
    
    # Запуск бота в фоне
    nohup python run_bot.py > "$LOG_FILE" 2>&1 &
    local bot_pid=$!
    
    # Сохранение PID
    echo $bot_pid > "$PID_FILE"
    
    log "Бот запущен с PID: $bot_pid"
    
    # Ожидание и проверка работы
    sleep 10
    
    if kill -0 "$bot_pid" 2>/dev/null; then
        log "Бот успешно запущен и работает"
        
        # Мониторинг работы
        while kill -0 "$bot_pid" 2>/dev/null; do
            sleep 60
            
            # Проверка размера лога
            if [ -f "$LOG_FILE" ]; then
                log_size=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
                if [ "$log_size" -gt 10485760 ]; then  # 10MB
                    warning "Лог файл слишком большой, архивируем..."
                    mv "$LOG_FILE" "${LOG_FILE}.$(date +%Y%m%d_%H%M%S)"
                    touch "$LOG_FILE"
                fi
            fi
        done
        
        warning "Бот завершил работу"
    else
        error "Бот не запустился"
    fi
    
    restart_count=$((restart_count + 1))
    
    if [ $restart_count -lt $MAX_RESTARTS ]; then
        warning "Перезапуск через $RESTART_DELAY секунд..."
        sleep $RESTART_DELAY
    fi
done

error "Превышено максимальное количество перезапусков ($MAX_RESTARTS)"
exit 1