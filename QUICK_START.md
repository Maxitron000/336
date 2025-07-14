# ⚡ БЫСТРЫЙ ЗАПУСК БОТА

## 🚀 1 команда - полная настройка!

```bash
python setup.py
```

Этот скрипт:
- ✅ Создаст конфигурацию
- ✅ Установит зависимости  
- ✅ Настроит базу данных
- ✅ Проверит работоспособность

## 📱 Что нужно подготовить

### Токен бота:
1. [@BotFather](https://t.me/BotFather) → `/newbot`
2. Скопируйте токен

### Ваш ID:
1. [@userinfobot](https://t.me/userinfobot) → `/start`  
2. Скопируйте ID

## 🎯 Запуск

После настройки:

```bash
python start.py
```

## 🎉 Готово!

Ваш бот работает с:
- 🔄 Автоперезапуском каждый час
- 📊 Отчётами админу каждые 6 часов  
- 🚨 Уведомлениями об ошибках
- 🛡️ Самовосстановлением

---

## 🌐 Для PythonAnywhere

```bash
git clone YOUR_REPO telegram_bot
cd telegram_bot
python setup.py
python pythonanywhere_deploy.py
```

Настройте Scheduled Task и всё готово! 🚀