# keyboards.py

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import LOCATIONS, ADMIN_RIGHTS

def main_menu_keyboard(is_admin=False):
    buttons = [
        [InlineKeyboardButton("🟢 Прибыл", callback_data="arrive"),
         InlineKeyboardButton("🔴 Убыл", callback_data="depart")],
        [InlineKeyboardButton("📋 Журнал", callback_data="journal"),
         InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_menu")])
    return InlineKeyboardMarkup(buttons)

def locations_inline_keyboard():
    loc_buttons = []
    row = []
    for i, (icon, name) in enumerate(LOCATIONS):
        row.append(InlineKeyboardButton(f"{icon} {name}", callback_data=f"loc_{name}"))
        if (i+1) % 2 == 0:
            loc_buttons.append(row)
            row = []
    if row:
        loc_buttons.append(row)
    loc_buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(loc_buttons)

def comment_confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить комментарий", callback_data="add_comment")],
        [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_comment")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_menu")]
    ])

def journal_keyboard(short=True):
    if short:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔽 Показать больше", callback_data="more_journal")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_menu")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔼 Свернуть", callback_data="less_journal")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_menu")]
        ])

def profile_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Сменить ФИО", callback_data="change_fio")],
        [InlineKeyboardButton("❌ Удалить профиль", callback_data="delete_user")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_menu")]
    ])

def admin_main_keyboard(rights=None):
    buttons = [
        [InlineKeyboardButton("📊 Быстрая сводка", callback_data="admin_summary")],
        [InlineKeyboardButton("👥 Личный состав", callback_data="admin_users")],
        [InlineKeyboardButton("📖 Журнал событий", callback_data="admin_journal")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_users_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Сменить ФИО", callback_data="admin_change_fio"),
         InlineKeyboardButton("➕ Добавить бойца", callback_data="admin_add_user")],
        [InlineKeyboardButton("❌ Удалить бойца", callback_data="admin_delete_user")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
    ])

def admin_journal_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Экспорт журнала", callback_data="admin_export_journal")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
    ])

def admin_settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Уведомления", callback_data="admin_notifications")],
        [InlineKeyboardButton("👑 Управление админами", callback_data="admin_admins")],
        [InlineKeyboardButton("⚠️ Опасная зона", callback_data="admin_danger_zone")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
    ])

def admin_admins_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить админа", callback_data="admin_add_admin")],
        [InlineKeyboardButton("❌ Удалить админа", callback_data="admin_delete_admin")],
        [InlineKeyboardButton("⚙️ Редактировать права", callback_data="admin_edit_rights")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_settings")]
    ])

def admin_notifications_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔕 Включить/выключить уведомления", callback_data="admin_toggle_notify")],
        [InlineKeyboardButton("⏰ Настроить расписание", callback_data="admin_set_schedule")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_settings")]
    ])

def admin_danger_zone_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚨 Отметить всех прибывшими", callback_data="admin_mark_all_arrived")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_settings")]
    ])

def rights_checkbox_keyboard(current_rights):
    buttons = []
    for code, name, icon in ADMIN_RIGHTS:
        state = "✅" if code in current_rights else "❌"
        buttons.append([
            InlineKeyboardButton(f"{icon} {name} {state}", callback_data=f"toggle_right_{code}")
        ])
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_admins")])
    return InlineKeyboardMarkup(buttons)
