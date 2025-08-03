# Group handlers
import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from database.db_manager import (
    create_account_group, get_account_groups, get_account_group,
    update_account_group, delete_account_group, add_account_to_group,
    remove_account_from_group, get_accounts_in_group, get_accounts_without_group,
    get_instagram_accounts, get_instagram_account
)
from config import ADMIN_USER_IDS

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_GROUP_NAME = 1
WAITING_GROUP_DESCRIPTION = 2
WAITING_GROUP_ICON = 3
WAITING_ACCOUNT_SELECTION = 4

# Временное хранилище данных
user_data_store = {}

def groups_menu_handler(update: Update, context: CallbackContext):
    """Главное меню управления папками"""
    query = update.callback_query
    if query:
        query.answer()
    
    from telegram_bot.keyboards import get_folders_menu_keyboard
    
    text = "📁 *Управление папками аккаунтов*\n\n" \
           "Папки позволяют организовать аккаунты для удобного управления.\n\n" \
           "Выберите действие:"
    
    if query:
        query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_folders_menu_keyboard())
    else:
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_folders_menu_keyboard())

def create_group_handler(update: Update, context: CallbackContext):
    """Начало создания новой папки"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    user_data_store[user_id] = {}
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="folders_menu")]]
    
    query.edit_message_text(
        "📝 *Создание новой папки*\n\n"
        "Введите название папки:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return WAITING_GROUP_NAME

def process_group_name(update: Update, context: CallbackContext):
    """Обработка названия папки"""
    user_id = update.effective_user.id
    
    if user_id not in user_data_store:
        user_data_store[user_id] = {}
    
    user_data_store[user_id]['group_name'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_group_description")]]
    
    update.message.reply_text(
        "📝 Введите описание папки (необязательно):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return WAITING_GROUP_DESCRIPTION

def process_group_description(update: Update, context: CallbackContext):
    """Обработка описания группы"""
    user_id = update.effective_user.id
    
    if update.message:
        user_data_store[user_id]['group_description'] = update.message.text
    else:
        user_data_store[user_id]['group_description'] = None
    
    # Предлагаем выбрать иконку
    icon_keyboard = [
        [
            InlineKeyboardButton("📁", callback_data="icon_📁"),
            InlineKeyboardButton("📂", callback_data="icon_📂"),
            InlineKeyboardButton("🗂️", callback_data="icon_🗂️"),
            InlineKeyboardButton("📊", callback_data="icon_📊")
        ],
        [
            InlineKeyboardButton("🎯", callback_data="icon_🎯"),
            InlineKeyboardButton("💼", callback_data="icon_💼"),
            InlineKeyboardButton("🏷️", callback_data="icon_🏷️"),
            InlineKeyboardButton("⭐", callback_data="icon_⭐")
        ],
        [
            InlineKeyboardButton("🔥", callback_data="icon_🔥"),
            InlineKeyboardButton("💎", callback_data="icon_💎"),
            InlineKeyboardButton("🚀", callback_data="icon_🚀"),
            InlineKeyboardButton("🌟", callback_data="icon_🌟")
        ]
    ]
    
    text = "🎨 Выберите иконку для папки:"
    
    if update.message:
        update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(icon_keyboard))
    else:
        query = update.callback_query
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(icon_keyboard))
    
    return WAITING_GROUP_ICON

def process_group_icon(update: Update, context: CallbackContext):
    """Обработка выбора иконки и создание папки"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    icon = query.data.replace("icon_", "")
    
    # Создаем папку
    name = user_data_store[user_id]['group_name']
    description = user_data_store[user_id].get('group_description')
    
    success, result = create_account_group(name, description, icon)
    
    if success:
        keyboard = [
            [InlineKeyboardButton("➕ Добавить аккаунты", callback_data=f"add_accounts_to_group_{result}")],
            [InlineKeyboardButton("📂 К списку папок", callback_data="list_folders")]
        ]
        
        query.edit_message_text(
            f"✅ Папка *{name}* {icon} успешно создана!\n\n"
            f"ID папки: `{result}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="folders_menu")]]
        
        query.edit_message_text(
            f"❌ Ошибка при создании папки: {result}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # Очищаем временные данные
    if user_id in user_data_store:
        del user_data_store[user_id]
    
    return ConversationHandler.END

def list_groups_handler(update: Update, context: CallbackContext):
    """Показывает список всех папок с пагинацией"""
    query = update.callback_query
    if query:
        query.answer()
    
    # Получаем номер страницы из callback_data
    page = 1
    if query and query.data.startswith("list_folders_page_"):
        page = int(query.data.replace("list_folders_page_", ""))
    
    groups = get_account_groups()
    
    if not groups:
        keyboard = [[InlineKeyboardButton("📁 Создать папку", callback_data="create_folder")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="folders_menu")]]
        
        text = "📂 Список папок пуст.\n\nСоздайте первую папку для организации аккаунтов."
        
        if query:
            query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # Пагинация
    groups_per_page = 5
    total_pages = (len(groups) + groups_per_page - 1) // groups_per_page
    start_idx = (page - 1) * groups_per_page
    end_idx = min(start_idx + groups_per_page, len(groups))
    
    keyboard = []
    
    # Добавляем группы на текущей странице
    for group in groups[start_idx:end_idx]:
        accounts_count = len(get_accounts_in_group(group.id))
        button_text = f"{group.icon} {group.name} ({accounts_count} акк.)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_group_{group.id}")])
    
    # Навигация по страницам
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"list_folders_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"list_folders_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="folders_menu")])
    
    text = f"📂 *Список папок* (всего: {len(groups)})\n\n" \
           f"Нажмите на папку для просмотра деталей:"
    
    if query:
        query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

def view_group_handler(update: Update, context: CallbackContext):
    """Показывает детали папки"""
    query = update.callback_query
    query.answer()
    
    group_id = int(query.data.replace("view_group_", ""))
    group = get_account_group(group_id)
    
    if not group:
        query.edit_message_text("❌ Папка не найдена", 
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_folders")]]))
        return
    
    accounts = get_accounts_in_group(group_id)
    
    text = f"{group.icon} *{group.name}*\n\n"
    if group.description:
        text += f"📝 {group.description}\n\n"
    
    text += f"👥 Аккаунтов в папке: {len(accounts)}\n"
    text += f"📅 Создана: {group.created_at.strftime('%d.%m.%Y')}\n\n"
    
    if accounts:
        text += "*Аккаунты в папке:*\n"
        for i, acc in enumerate(accounts[:10]):  # Показываем первые 10
            status = "✅" if acc.is_active else "❌"
            # Экранируем специальные символы для Markdown
            username = acc.username.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')
            text += f"{i+1}. {status} @{username}\n"
        
        if len(accounts) > 10:
            text += f"\n_...и еще {len(accounts) - 10} аккаунтов_"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить аккаунты", callback_data=f"add_accounts_to_group_{group_id}")],
        [InlineKeyboardButton("👥 Показать все аккаунты", callback_data=f"show_group_accounts_{group_id}")],
        [InlineKeyboardButton("🗑️ Удалить папку", callback_data=f"delete_group_{group_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="list_folders")]
    ]
    
    query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

def get_group_conversation_handler():
    """Возвращает ConversationHandler для управления папками"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(create_group_handler, pattern="^create_folder$")
        ],
        states={
            WAITING_GROUP_NAME: [MessageHandler(Filters.text & ~Filters.command, process_group_name)],
            WAITING_GROUP_DESCRIPTION: [
                MessageHandler(Filters.text & ~Filters.command, process_group_description),
                CallbackQueryHandler(process_group_description, pattern="^skip_group_description$")
            ],
            WAITING_GROUP_ICON: [CallbackQueryHandler(process_group_icon, pattern="^icon_")]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^folders_menu$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^menu_accounts$")
        ]
    )

def add_accounts_to_group_handler(update: Update, context: CallbackContext):
    """Начало процесса добавления аккаунтов в папку"""
    query = update.callback_query
    query.answer()
    
    group_id = int(query.data.replace("add_accounts_to_group_", ""))
    group = get_account_group(group_id)
    
    if not group:
        query.edit_message_text("❌ Папка не найдена", 
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_folders")]]))
        return ConversationHandler.END
    
    # Сохраняем ID группы для дальнейшего использования
    user_id = query.from_user.id
    if user_id not in user_data_store:
        user_data_store[user_id] = {}
    user_data_store[user_id]['target_group_id'] = group_id
    
    # Получаем аккаунты, которые еще не в этой папке
    all_accounts = get_instagram_accounts()
    accounts_in_group = get_accounts_in_group(group_id)
    accounts_in_group_ids = [acc.id for acc in accounts_in_group]
    
    available_accounts = [acc for acc in all_accounts if acc.id not in accounts_in_group_ids]
    
    if not available_accounts:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"view_group_{group_id}")]]
        query.edit_message_text(
            f"ℹ️ Все аккаунты уже добавлены в папку *{group.name}*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    # Создаем клавиатуру с аккаунтами
    keyboard = []
    selected_accounts = user_data_store[user_id].get('selected_accounts', [])
    
    for account in available_accounts[:20]:  # Показываем первые 20
        status = "✅" if account.is_active else "❌"
        check = "☑️" if account.id in selected_accounts else "☐"
        button_text = f"{check} {status} @{account.username}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_account_{account.id}")])
    
    if len(available_accounts) > 20:
        keyboard.append([InlineKeyboardButton(f"📄 Показаны первые 20 из {len(available_accounts)}", callback_data="noop")])
    
    # Кнопки действий
    action_buttons = []
    if selected_accounts:
        action_buttons.append(InlineKeyboardButton(f"✅ Добавить ({len(selected_accounts)})", callback_data="confirm_add_to_group"))
    action_buttons.append(InlineKeyboardButton("❌ Отмена", callback_data=f"view_group_{group_id}"))
    keyboard.append(action_buttons)
    
    text = f"📁 Добавление аккаунтов в папку *{group.name}*\n\n"
    text += "Выберите аккаунты для добавления:"
    
    query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return WAITING_ACCOUNT_SELECTION

def toggle_account_selection(update: Update, context: CallbackContext):
    """Переключает выбор аккаунта"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    account_id = int(query.data.replace("toggle_account_", ""))
    
    if user_id not in user_data_store:
        user_data_store[user_id] = {}
    
    selected_accounts = user_data_store[user_id].get('selected_accounts', [])
    
    if account_id in selected_accounts:
        selected_accounts.remove(account_id)
    else:
        selected_accounts.append(account_id)
    
    user_data_store[user_id]['selected_accounts'] = selected_accounts
    
    # Получаем данные для обновления интерфейса
    group_id = user_data_store[user_id].get('target_group_id')
    if not group_id:
        return ConversationHandler.END
    
    group = get_account_group(group_id)
    if not group:
        return ConversationHandler.END
    
    # Получаем аккаунты, которые еще не в этой папке
    all_accounts = get_instagram_accounts()
    accounts_in_group = get_accounts_in_group(group_id)
    accounts_in_group_ids = [acc.id for acc in accounts_in_group]
    
    available_accounts = [acc for acc in all_accounts if acc.id not in accounts_in_group_ids]
    
    # Создаем клавиатуру с аккаунтами
    keyboard = []
    
    for account in available_accounts[:20]:  # Показываем первые 20
        status = "✅" if account.is_active else "❌"
        check = "☑️" if account.id in selected_accounts else "☐"
        button_text = f"{check} {status} @{account.username}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_account_{account.id}")])
    
    if len(available_accounts) > 20:
        keyboard.append([InlineKeyboardButton(f"📄 Показаны первые 20 из {len(available_accounts)}", callback_data="noop")])
    
    # Кнопки действий
    action_buttons = []
    if selected_accounts:
        action_buttons.append(InlineKeyboardButton(f"✅ Добавить ({len(selected_accounts)})", callback_data="confirm_add_to_group"))
    action_buttons.append(InlineKeyboardButton("❌ Отмена", callback_data=f"view_group_{group_id}"))
    keyboard.append(action_buttons)
    
    text = f"📁 Добавление аккаунтов в папку *{group.name}*\n\n"
    text += "Выберите аккаунты для добавления:"
    
    query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return WAITING_ACCOUNT_SELECTION

def confirm_add_accounts_to_group(update: Update, context: CallbackContext):
    """Подтверждает добавление выбранных аккаунтов в папку"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_data_store:
        query.edit_message_text("❌ Ошибка: данные сессии потеряны", 
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_folders")]]))
        return ConversationHandler.END
    
    group_id = user_data_store[user_id].get('target_group_id')
    selected_accounts = user_data_store[user_id].get('selected_accounts', [])
    
    if not group_id or not selected_accounts:
        query.edit_message_text("❌ Ошибка: не выбраны аккаунты", 
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_folders")]]))
        return ConversationHandler.END
    
    group = get_account_group(group_id)
    if not group:
        query.edit_message_text("❌ Папка не найдена", 
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_folders")]]))
        return ConversationHandler.END
    
    # Добавляем аккаунты в папку
    success_count = 0
    for account_id in selected_accounts:
        success, _ = add_account_to_group(account_id, group_id)
        if success:
            success_count += 1
    
    # Очищаем временные данные
    if user_id in user_data_store:
        user_data_store[user_id].pop('selected_accounts', None)
        user_data_store[user_id].pop('target_group_id', None)
    
    keyboard = [[InlineKeyboardButton("👁️ Просмотр папки", callback_data=f"view_group_{group_id}")],
                [InlineKeyboardButton("📂 К списку папок", callback_data="list_folders")]]
    
    query.edit_message_text(
        f"✅ Успешно добавлено {success_count} аккаунтов в папку *{group.name}*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END

def show_group_accounts_handler(update: Update, context: CallbackContext):
    """Показывает все аккаунты в папке с пагинацией"""
    query = update.callback_query
    query.answer()
    
    # Парсим group_id и страницу
    data_parts = query.data.split("_")
    if len(data_parts) >= 4 and data_parts[-2] == "page":
        group_id = int(data_parts[3])
        page = int(data_parts[-1])
    else:
        group_id = int(query.data.replace("show_group_accounts_", ""))
        page = 1
    
    group = get_account_group(group_id)
    if not group:
        query.edit_message_text("❌ Папка не найдена", 
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_folders")]]))
        return
    
    accounts = get_accounts_in_group(group_id)
    
    if not accounts:
        keyboard = [[InlineKeyboardButton("➕ Добавить аккаунты", callback_data=f"add_accounts_to_group_{group_id}")],
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"view_group_{group_id}")]]
        
        query.edit_message_text(
            f"📂 В папке *{group.name}* пока нет аккаунтов",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Пагинация
    accounts_per_page = 10
    total_pages = (len(accounts) + accounts_per_page - 1) // accounts_per_page
    start_idx = (page - 1) * accounts_per_page
    end_idx = min(start_idx + accounts_per_page, len(accounts))
    
    text = f"{group.icon} *{group.name}* - Аккаунты ({len(accounts)})\n\n"
    
    for i, acc in enumerate(accounts[start_idx:end_idx], start=start_idx+1):
        status = "✅" if acc.is_active else "❌"
        # Экранируем специальные символы
        username = acc.username.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')
        text += f"{i}. {status} @{username}\n"
    
    keyboard = []
    
    # Навигация по страницам
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"show_group_accounts_{group_id}_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"show_group_accounts_{group_id}_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("➕ Добавить еще", callback_data=f"add_accounts_to_group_{group_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"view_group_{group_id}")])
    
    query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

def get_add_accounts_conversation_handler():
    """ConversationHandler для добавления аккаунтов в папку"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_accounts_to_group_handler, pattern="^add_accounts_to_group_")
        ],
        states={
            WAITING_ACCOUNT_SELECTION: [
                CallbackQueryHandler(toggle_account_selection, pattern="^toggle_account_"),
                CallbackQueryHandler(confirm_add_accounts_to_group, pattern="^confirm_add_to_group$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^view_group_"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^list_folders$")
        ]
    )

def get_group_handlers():
    """Возвращает все обработчики для папок"""
    return [
        get_group_conversation_handler(),
        get_add_accounts_conversation_handler(),
        CallbackQueryHandler(groups_menu_handler, pattern="^folders_menu$"),
        CallbackQueryHandler(list_groups_handler, pattern="^list_folders"),
        CallbackQueryHandler(view_group_handler, pattern="^view_group_"),
        CallbackQueryHandler(show_group_accounts_handler, pattern="^show_group_accounts_"),
        CallbackQueryHandler(lambda u, c: None, pattern="^noop$")  # Для неактивных кнопок
    ]
 