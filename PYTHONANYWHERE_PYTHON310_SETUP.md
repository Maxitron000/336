# 🚀 Пошаговая настройка бота на PythonAnywhere с Python 3.10

## ✅ **Исправленные проблемы:**
- Конфликты версий aiogram с Python 3.13
- Проблемы с базой данных
- Отсутствующие зависимости

---

## 📋 **Подготовка**

### 1. Получите данные для бота:
- **Токен бота:** [@BotFather](https://t.me/BotFather) → `/newbot`
- **Ваш Telegram ID:** [@userinfobot](https://t.me/userinfobot) → `/start`

### 2. Зарегистрируйтесь на PythonAnywhere:
- Перейдите на https://www.pythonanywhere.com
- Создайте бесплатный аккаунт

---

## 🔧 **Установка на PythonAnywhere**

### **Шаг 1: Загрузка проекта**

1. Откройте **"Bash console"** на PythonAnywhere
2. Клонируйте проект:

```bash
cd ~
git clone YOUR_REPOSITORY_URL telegram_bot
cd telegram_bot
ls -la  # Проверяем файлы
```

### **Шаг 2: Настройка Python 3.10**

```bash
# Проверяем доступные версии Python
ls /usr/bin/python*

# Используем Python 3.10 (рекомендуется)
python3.10 --version

# Создаем виртуальное окружение
python3.10 -m venv venv_bot

# Активируем окружение
source venv_bot/bin/activate

# Проверяем активацию
which python
python --version  # Должно быть 3.10.x
```

### **Шаг 3: Настройка конфигурации**

```bash
# Копируем и редактируем конфигурацию
cp .env .env.example  # Создаем пример
nano .env

# В файле .env замените:
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id

# Сохраните: Ctrl+X, затем Y, затем Enter
```

### **Шаг 4: Установка зависимостей**

```bash
# Убедитесь что виртуальное окружение активно
source venv_bot/bin/activate

# Обновляем pip
pip install --upgrade pip

# Устанавливаем совместимые зависимости
pip install -r requirements_python310.txt

# Если возникают ошибки, используйте автоматическое исправление:
python fix_dependencies.py
```

### **Шаг 5: Диагностика проблем**

```bash
# Запускаем диагностику
python diagnose_issues.py

# Все проверки должны пройти успешно
# Если есть проблемы - они будут показаны с инструкциями по исправлению
```

### **Шаг 6: Тестирование бота**

```bash
# Проверяем импорт aiogram
python test_aiogram.py

# Инициализируем базу данных
python create_database.py

# Тестовый запуск (остановите через Ctrl+C через несколько секунд)
python main.py
```

---

## 📅 **Настройка автозапуска (Scheduled Task)**

### **Создание задачи:**

1. Перейдите в **"Tasks"** → **"Scheduled"**
2. Нажмите **"Create a scheduled task"**
3. Заполните:
   - **Command:** `/home/yourusername/telegram_bot/venv_bot/bin/python /home/yourusername/telegram_bot/run_bot.py`
   - **Hour:** `12` (раз в сутки в 12:00)
   - **Minute:** `0`
   - **Description:** `Telegram Bot Auto-restart`

### **Скрипт запуска для PythonAnywhere:**

```bash
# Создаем скрипт запуска
nano start_bot_pa.sh

# Содержимое скрипта:
#!/bin/bash
cd /home/yourusername/telegram_bot
source venv_bot/bin/activate
python run_bot.py

# Делаем исполняемым
chmod +x start_bot_pa.sh
```

---

## 🔍 **Мониторинг и отладка**

### **Проверка логов:**

```bash
# Просмотр логов
tail -f logs/bot.log

# Проверка последних ошибок
grep -i error logs/bot.log | tail -20

# Проверка статуса процессов
ps aux | grep python
```

### **Перезапуск бота:**

```bash
cd ~/telegram_bot
source venv_bot/bin/activate

# Остановка (если запущен)
pkill -f "python.*main.py"

# Запуск
python run_bot.py
```

---

## ⚠️ **Ограничения бесплатного аккаунта**

### **Лимиты:**
- ❌ Нет "Always-On Tasks"
- ⏰ 3000 CPU секунд в месяц
- 🔄 Scheduled Tasks только раз в сутки
- 🌐 Ограниченный интернет доступ

### **Оптимизация для бесплатного аккаунта:**

1. **Рабочие часы:** Бот работает только 5:00-24:00 (настроено в `run_bot.py`)
2. **Автоперезапуск:** Раз в сутки через Scheduled Task
3. **Легкий мониторинг:** Минимальные ресурсы

---

## 🚨 **Решение проблем**

### **Проблема: ModuleNotFoundError**
```bash
# Проверьте активацию виртуального окружения
source venv_bot/bin/activate
python diagnose_issues.py
```

### **Проблема: aiogram import error**
```bash
# Исправьте зависимости
python fix_dependencies.py
```

### **Проблема: База данных не создается**
```bash
# Создайте вручную
python create_database.py
python check_database.py
```

### **Проблема: Бот не отвечает**
```bash
# Проверьте токен в .env
cat .env | grep BOT_TOKEN

# Проверьте логи
tail -50 logs/bot.log
```

---

## ✅ **Финальная проверка**

### **Контрольный список:**

- [ ] Python 3.10 установлен и используется
- [ ] Виртуальное окружение создано и активировано  
- [ ] Файл .env настроен с реальными токенами
- [ ] Все зависимости установлены (diagnose_issues.py показывает ✅)
- [ ] База данных создана
- [ ] Тестовый запуск прошел успешно
- [ ] Scheduled Task настроена
- [ ] Логи создаются в logs/bot.log

### **Команды для финальной проверки:**

```bash
cd ~/telegram_bot
source venv_bot/bin/activate
python diagnose_issues.py
python test_aiogram.py
```

---

## 🎉 **Готово!**

Ваш бот должен работать стабильно на Python 3.10 с исправленными зависимостями.

**Для мониторинга используйте:**
```bash
tail -f logs/bot.log  # Просмотр логов в реальном времени
```

**Для перезапуска:**
```bash
cd ~/telegram_bot && source venv_bot/bin/activate && python run_bot.py
```