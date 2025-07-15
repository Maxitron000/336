FROM python:3.13-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt первым для кеширования слоев
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p data logs exports && \
    chown -R botuser:botuser /app

# Переключение на пользователя botuser
USER botuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port for healthcheck
EXPOSE 8000

# Запуск приложения
CMD ["python", "main.py"]