# ⚡ БЫСТРЫЙ ЗАПУСК НА PYTHONANYWHERE FREE (5 МИНУТ)

## 🎯 **КРАТКО: 4 простых шага**

### **1️⃣ Загрузите код на PythonAnywhere**

1. Зайдите на https://www.pythonanywhere.com (создайте аккаунт)
2. Откройте **"Bash console"**
3. Выполните команды:

```bash
# Клонируем репозиторий или загружаем код
cd ~
git clone YOUR_REPOSITORY_URL telegram_bot
cd telegram_bot

# ИЛИ создаем папку и загружаем файлы вручную
mkdir ~/telegram_bot
# Загрузите все .py файлы через Files tab
```

### **2️⃣ Автоматическая установка (1 команда!)**

```bash
# Запускаем автоматический скрипт установки
cd ~/telegram_bot
bash setup_pythonanywhere.sh
```

**Скрипт автоматически:**
- ✅ Создаст Python 3.10 виртуальное окружение
- ✅ Установит все зависимости
- ✅ Создаст необходимые папки и файлы
- ✅ Настроит скрипты запуска

### **3️⃣ Настройте токен бота**

```bash
# Отредактируйте конфигурацию
nano .env

# Замените эти строки:
BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
ADMIN_IDS=YOUR_TELEGRAM_ID_HERE
```

**🔧 Где взять:**
- **Токен**: отправьте `/newbot` в [@BotFather](https://t.me/BotFather)
- **ID**: отправьте сообщение в [@userinfobot](https://t.me/userinfobot)

### **4️⃣ Настройте автозапуск**

1. Откройте вкладку **"Tasks"** в дашборде PythonAnywhere
2. Нажмите **"Create a task"**
3. Заполните форму:

```
Command: /home/yourusername/telegram_bot/hourly_runner.sh
Hour: * (каждый час)
Minute: 5
```

**⚠️ Замените `yourusername` на ваше имя пользователя PythonAnywhere!**

---

## ✅ **ГОТОВО! Проверка работы**

```bash
# Проверяем статус
cd ~/telegram_bot
./check_status.py

# Тестовый запуск (остановите через Ctrl+C через 10-15 сек)
python run_bot_pythonanywhere.py
```

**Отправьте `/start` вашему боту в Telegram!**

---

## 🔧 **Основные команды**

```bash
# Проверка статуса
cd ~/telegram_bot && ./check_status.py

# Просмотр логов
tail -f logs/bot_output.log

# Остановка бота
pkill -f "run_bot_pythonanywhere.py"

# Ручной запуск
./hourly_runner.sh
```

---

## 💡 **Особенности Free аккаунта**

- ⏰ **CPU лимит**: 3000 секунд в месяц
- 🔄 **Перезапуск каждый час** для стабильности
- 📊 **Следите за CPU usage** в дашборде

**Если превышен лимит CPU:**
1. Измените hourly task на каждые 2-3 часа
2. Установите `LOG_LEVEL=ERROR` в `.env`

---

## 🆘 **Если что-то не работает**

### **Бот не отвечает:**
```bash
cd ~/telegram_bot
./check_status.py
# Смотрите на ошибки в выводе
```

### **Ошибка токена:**
```bash
nano .env
# Проверьте правильность токена
```

### **Task не запускается:**
1. Проверьте путь: `/home/YOURUSERNAME/telegram_bot/hourly_runner.sh`
2. Замените `YOURUSERNAME` на ваше имя
3. Убедитесь что файл исполняемый: `chmod +x hourly_runner.sh`

---

## 🚀 **Результат**

После выполнения всех шагов ваш бот будет:
- ✅ Работать 24/7 на PythonAnywhere Free
- ✅ Автоматически перезапускаться каждый час
- ✅ Иметь все возможности проекта:
  - Система прав доступа
  - Фильтры журнала
  - Excel экспорт с цветами
  - ТГ ссылки в админке
  - Защита опасных операций

**Команды бота:**
- `/start` - главное меню
- `/admin` - админ-панель
- `/status` - статус системы

🎉 **Бот готов к работе!**