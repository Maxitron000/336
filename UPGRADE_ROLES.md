# 🔄 Обновление системы ролей

## 📋 Описание изменений

Система ролей упрощена до 3 основных ролей:

1. **👤 Боец/солдат** (`soldier`) - обычные пользователи
2. **👑 Админ** (`admin`) - администраторы 
3. **👑 Главный админ** (`main_admin`) - суперадминистратор

### Что изменилось:

- ❌ Удалены колонки `is_admin` и `is_commander`
- ✅ Добавлена колонка `role` с ограничениями
- 🔄 Автоматическая миграция существующих данных
- 🛡️ Улучшенная система прав доступа

## 🚀 Процесс обновления

### 1. Подготовка

```bash
# Создайте резервную копию
cp data/bot_database.db data/bot_database.db.backup

# Остановите бота
pkill -f "python.*main.py"
```

### 2. Запуск миграции

```bash
# Запустите миграционный скрипт
python3 migrate_roles.py
```

### 3. Проверка результатов

Скрипт автоматически:
- ✅ Создаст резервную копию
- 🔄 Мигрирует существующие роли
- 📊 Покажет статистику
- 🔍 Проверит корректность данных

### 4. Запуск обновленного бота

```bash
# Запустите бота
python3 main.py
```

## 📊 Правила миграции

### Старые роли → Новые роли:

| Старая роль | Новая роль | Описание |
|-------------|------------|----------|
| `is_admin = True` | `main_admin` | Первый админ становится главным |
| `is_commander = True` | `admin` | Командиры становятся админами |
| Остальные | `soldier` | Все остальные становятся бойцами |

## 🔐 Система прав доступа

### 👤 Боец (soldier)
- ✅ Отметка прибытия/убытия
- ✅ Просмотр своего статуса
- ✅ Получение уведомлений
- ❌ Доступ к админ-панели

### 👑 Админ (admin)
- ✅ Все права бойца
- ✅ Управление личным составом
- ✅ Просмотр журналов
- ✅ Экспорт данных
- ✅ Настройки уведомлений
- ❌ Управление другими админами
- ❌ Опасные операции

### 👑 Главный админ (main_admin)
- ✅ Все права админа
- ✅ Управление админами
- ✅ Опасные операции
- ✅ Системные настройки
- ✅ Мониторинг бота
- ✅ Техобслуживание

## 🛠️ Новые методы в API

### Database класс:

```python
# Получение роли пользователя
role = await db.get_user_role(telegram_id)

# Установка роли
success = await db.set_user_role(telegram_id, 'admin')

# Проверка ролей
is_admin = await db.is_admin(telegram_id)
is_main_admin = await db.is_main_admin(telegram_id)

# Получение списка админов
admins = await db.get_admins()

# Получение главного админа
main_admin = await db.get_main_admin()
```

### AdminPanel класс:

```python
# Проверка ролей
is_admin = await admin_panel.is_admin(user_id)
is_main_admin = await admin_panel.is_main_admin(user_id)
role = await admin_panel.get_user_role(user_id)

# Управление админами
success = await admin_panel.add_admin(telegram_id, 'admin')
success = await admin_panel.add_admin(telegram_id, 'main_admin')
success = await admin_panel.remove_admin(telegram_id)
```

### Utils функции:

```python
# Проверка ролей
is_admin = is_admin(telegram_id)
is_main_admin = is_main_admin(telegram_id)
role = get_user_role(telegram_id)

# Отображение ролей
role_name = get_role_display_name(role)
role_emoji = get_role_emoji(role)
```

## 📝 Обновленные клавиатуры

### Управление админами:
- ➕ Добавить админа
- ➕ Главный админ  
- ❌ Удалить админа
- 📋 Список админов
- 🔐 Права доступа
- 📊 Активность

## 🔍 Проверка после обновления

### 1. Проверьте структуру базы данных:

```sql
PRAGMA table_info(users);
```

Должна быть колонка `role` типа `TEXT`.

### 2. Проверьте данные:

```sql
SELECT role, COUNT(*) FROM users GROUP BY role;
```

### 3. Проверьте ограничения:

```sql
SELECT COUNT(*) FROM users WHERE role NOT IN ('soldier', 'admin', 'main_admin');
```

Результат должен быть 0.

### 4. Проверьте индексы:

```sql
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users';
```

Должен быть индекс `idx_users_role`.

## ⚠️ Важные замечания

1. **Резервная копия**: Всегда создавайте резервную копию перед миграцией
2. **Права доступа**: После миграции проверьте права всех пользователей
3. **Главный админ**: Убедитесь, что у вас есть хотя бы один главный админ
4. **Тестирование**: Протестируйте все функции после обновления

## 🆘 Устранение проблем

### Ошибка "Колонка role не найдена":
```bash
# Проверьте, что миграция прошла успешно
python3 migrate_roles.py
```

### Ошибка "Некорректная роль":
```sql
-- Исправьте некорректные роли
UPDATE users SET role = 'soldier' WHERE role NOT IN ('soldier', 'admin', 'main_admin');
```

### Ошибка "Нет главного админа":
```sql
-- Назначьте главного админа
UPDATE users SET role = 'main_admin' WHERE telegram_id = YOUR_ID LIMIT 1;
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте лог файл: `migration_roles.log`
2. Убедитесь, что резервная копия создана
3. Проверьте права доступа к файлам базы данных
4. Обратитесь к документации или создайте issue

---

**Версия**: 2.0  
**Дата**: $(date)  
**Автор**: Telegram Bot Team