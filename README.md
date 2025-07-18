# 🚀 Telegram Bot - Быстрый запуск

## Мгновенная установка и запуск

### Вариант 1: Bash скрипт (рекомендуется)
```bash
# Скачайте проект и запустите
./quick_start.sh
```

### Вариант 2: Python скрипт
```bash
python3 setup.py
```

## Что нужно для запуска

1. **Токен бота** - получите от [@BotFather](https://t.me/BotFather)
2. **Ваш Telegram ID** - получите от [@userinfobot](https://t.me/userinfobot)

## 🆕 Новые функции мониторинга

✅ **Автоперезапуск каждые 55 минут** (идеально для PythonAnywhere Free)  
✅ **Мониторинг здоровья каждые 6 часов** с отчетами в Telegram  
✅ **Уведомления об ошибках** в реальном времени  
✅ **Единая задача** для PythonAnywhere Daily Task  
✅ **Автоматическое восстановление** при сбоях  

## Что делает автоматически

✅ **Проверяет зависимости** и устанавливает недостающие  
✅ **Создает виртуальное окружение**  
✅ **Устанавливает все пакеты** (aiogram, aiosqlite, schedule и др.)  
✅ **Тестирует подключение** к боту  
✅ **Создает конфигурацию** (.env файл)  
✅ **Настраивает автозапуск** (systemd сервис)  
✅ **Создает скрипты мониторинга** для PythonAnywhere  
✅ **Запускает бота** в режиме 24/7  

## 🛠️ Для PythonAnywhere Free

После установки создайте Daily Task:
1. **Dashboard** → **Tasks** → **Create a new task**
2. **Command**: `python3 /home/yourusername/yourproject/monitoring/daily_task.py`
3. **Frequency**: Daily
4. **Time**: 00:00

⚠️ **Важно**: Замените `/home/yourusername/yourproject` на полный путь к вашему проекту!

**Готово!** Бот будет автоматически перезапускаться каждые 55 минут и отправлять отчеты о здоровье.

## 📱 Уведомления в Telegram

Вы будете получать:
- 🔄 Уведомления о перезапуске
- 🏥 Подробные отчеты о здоровье системы
- 🚨 Уведомления об ошибках
- 📊 Системные метрики (CPU, память, диск)

## Ограничения

⏰ **Запуск только раз в сутки** - защита от случайного повторного запуска

## Управление ботом

### Запуск/остановка
```bash
# Статус
sudo systemctl status telegram-bot

# Запуск
sudo systemctl start telegram-bot

# Остановка
sudo systemctl stop telegram-bot

# Перезапуск
sudo systemctl restart telegram-bot
```

### Мониторинг
```bash
# Просмотр логов
tail -f logs/bot.log
tail -f logs/monitoring.log
tail -f logs/health.log

# Ручная проверка здоровья
python3 monitoring/health_check.py

# Ручной перезапуск
python3 monitoring/auto_restart.py

# Полная инструкция по PythonAnywhere
cat monitoring/PYTHONANYWHERE_SETUP.md
```

## 🎯 Преимущества

✅ **Полностью автоматическая установка** - просто введите токен и ID  
✅ **Мониторинг 24/7** - постоянный контроль состояния  
✅ **Уведомления в реальном времени** - мгновенные сообщения об ошибках  
✅ **Идеально для PythonAnywhere Free** - обход всех лимитов  
✅ **Автоматическое восстановление** - перезапуск при сбоях  

## 📋 Быстрая настройка

1. `./quick_start.sh` - запуск установки
2. Введите токен бота и ваш ID
3. Дождитесь окончания установки
4. Для PythonAnywhere: настройте Daily Task
5. Готово! Бот работает с полным мониторингом

**Теперь ваш бот будет работать стабильно и надежно!**

---

## 🚀 Запуск на Replit (24/7)

1. **Создайте новый Repl на https://replit.com/**
2. Загрузите все файлы проекта (или клонируйте репозиторий)
3. В разделе Secrets (Environment Variables) добавьте:
   - `BOT_TOKEN` — токен вашего Telegram-бота
   - `ADMIN_ID` — ваш Telegram user id
4. Убедитесь, что в requirements.txt есть `flask`
5. В файле main.py импортируйте и вызовите `keep_alive()` перед запуском бота
6. Нажмите Run — бот запустится и будет работать 24/7, если настроить внешний мониторинг
7. Для anti-sleep используйте UptimeRobot:
   - Зарегистрируйтесь на https://uptimerobot.com/
   - Создайте HTTP(s) монитор с URL вашего Replit (например, https://your-repl-username.your-repl-name.repl.co/)
   - Монитор будет “будить” ваш бот каждые 5 минут

---