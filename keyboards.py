from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils import load_locations
from database import get_all_users

def main_menu_keyboard(show_admin_button=False):
    buttons = [
        [
            InlineKeyboardButton("Прибыл", callback_data='arrived'),
            InlineKeyboardButton("Убыл", callback_data='depart')
        ],
        [InlineKeyboardButton("📜 История действий", callback_data='history')]
    ]
    if show_admin_button:
        buttons.append([InlineKeyboardButton("👑 Админ-панель", callback_data='admin_panel')])
    return InlineKeyboardMarkup(buttons)

def locations_keyboard():
    locations = load_locations()
    buttons = []

    for i in range(0, len(locations), 2):
        row = []
        if i < len(locations):
            loc1 = locations[i]
            row.append(InlineKeyboardButton(
                f"{loc1['emoji']} {loc1['name']}",
                callback_data=f"loc_{loc1['id']}"
            ))
        if i+1 < len(locations):
            loc2 = locations[i+1]
            row.append(InlineKeyboardButton(
                f"{loc2['emoji']} {loc2['name']}",
                callback_data=f"loc_{loc2['id']}"
            ))
        if row:
            buttons.append(row)

    buttons.append([InlineKeyboardButton("« Назад", callback_data='back')])
    return InlineKeyboardMarkup(buttons)

def comment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Добавить комментарий", callback_data='add_comment')],
        [InlineKeyboardButton("❌ Без комментария", callback_data='no_comment')],
        [InlineKeyboardButton("« Назад", callback_data='back')]
    ])

def history_keyboard(expanded=False):
    if expanded:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Свернуть", callback_data='history_collapse')]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Показать 10 последних", callback_data='history_expand')]
    ])

def admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👥 Управление ЛС", callback_data='admin_manage')],
        [InlineKeyboardButton("📜 Журнал действий", callback_data='admin_logs')],
        [InlineKeyboardButton("💾 Экспорт данных", callback_data='admin_export')],
        [InlineKeyboardButton("📊 Сводка", callback_data='admin_summary')],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='admin_settings')],
        [InlineKeyboardButton("⚠️ Опасная зона", callback_data='admin_danger')],
        [InlineKeyboardButton("« Главное меню", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« Назад", callback_data='admin_back')]
    ])

def admin_export_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("CSV", callback_data='export_csv')],
        [InlineKeyboardButton("Excel", callback_data='export_excel')],
        [InlineKeyboardButton("PDF", callback_data='export_pdf')],
        [InlineKeyboardButton("Все форматы", callback_data='export_all')],
        [InlineKeyboardButton("« Назад", callback_data='admin_export')]
    ])

def admin_danger_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ Очистить журнал", callback_data='danger_clear_logs')],
        [InlineKeyboardButton("♻️ Сбросить статусы", callback_data='danger_reset_statuses')],
        [InlineKeyboardButton("🏠 Отметить всех прибывшими", callback_data='danger_mark_all_arrived')],
        [InlineKeyboardButton("« Назад", callback_data='admin_back')]
    ])

def confirm_danger_keyboard(action):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, выполнить", callback_data=f'confirm_{action}')],
        [InlineKeyboardButton("❌ Отмена", callback_data='admin_danger')]
    ])

def admin_manage_users_keyboard():
    users = get_all_users()
    keyboard = []
    for user in users:
        keyboard.append([
            InlineKeyboardButton(
                f"{user['full_name']} ({user['status']})",
                callback_data=f"user_{user['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("➕ Добавить бойца", callback_data='admin_add_user')])
    keyboard.append([InlineKeyboardButton("« Назад", callback_data='admin_manage')])
    return InlineKeyboardMarkup(keyboard)

def admin_back_to_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« В админ-меню", callback_data='admin_back')]
    ])