# 🤖 Быстрая настройка Telegram бота

## ⚡ Супер-быстрый запуск (1 команда)

```bash
python setup.py
```

**Всё! Больше ничего не нужно!**

## 📋 Что вам понадобится

1. **Токен бота** - получите у [@BotFather](https://t.me/BotFather)
2. **Ваш Telegram ID** - получите у [@userinfobot](https://t.me/userinfobot)

## 🚀 Пошаговая инструкция

### Шаг 1: Получение токена бота
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям (придумайте имя и username)
4. Скопируйте токен (например: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Получение вашего ID
1. Откройте [@userinfobot](https://t.me/userinfobot) в Telegram  
2. Отправьте `/start`
3. Скопируйте ваш ID (например: `123456789`)

### Шаг 3: Автоматическая настройка
```bash
python setup.py
```

Скрипт сам:
- ✅ Создаст конфигурацию
- ✅ Установит зависимости  
- ✅ Настроит базу данных
- ✅ Проверит работоспособность
- ✅ Создаст скрипты запуска

### Шаг 4: Запуск
```bash
python start.py
```

## 🎯 Что получаете

- 🔄 **Автоперезапуск раз в сутки**
- 📊 **Отчёты админу каждые 12 часов**
- 🚨 **Уведомления об ошибках**
- 📱 **Мониторинг системы**
- 🛡️ **Самопроверка и восстановление**

## 🌐 Для PythonAnywhere

### Загрузка на сервер:
```bash
git clone YOUR_REPOSITORY_URL telegram_bot
cd telegram_bot
python setup.py
```

### Настройка Scheduled Task:
1. Откройте "Tasks" → "Scheduled"
2. Command: `/home/yourusername/telegram_bot/start.py`
3. Hour: `12` (раз в сутки в 12:00)
4. Minute: `0`

## 🚨 Решение проблем

### Ошибка модулей:
```bash
python setup.py  # Переустановит всё
```

### Проблемы с базой данных:
```bash
python create_database.py
python check_database.py
```

### Проверка состояния:
```bash
python diagnose_issues.py
```

## 📁 Структура после настройки

```
telegram_bot/
├── .env              # Ваша конфигурация
├── start.py          # Простой запуск
├── setup.py          # Автоматическая настройка
├── data/
│   └── bot_database.db
├── logs/
│   └── bot.log
└── exports/
```

## 🎉 Готово!

После `python setup.py` и `python start.py` ваш бот:

- ✅ Работает 24/7 с автоперезапуском
- ✅ Присылает отчёты каждые 12 часов
- ✅ Уведомляет об ошибках
- ✅ Автоматически восстанавливается

**Просто запустите и забудьте! 🚀**