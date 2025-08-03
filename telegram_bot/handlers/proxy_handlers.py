from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import ConversationHandler, CallbackContext, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from database.db_manager import add_proxy, get_proxies, update_proxy, delete_proxy, assign_proxy_to_account
from utils.proxy_manager import check_proxy, distribute_proxies, check_all_proxies
import re
import logging

# Состояния для ConversationHandler
PROXY_INPUT = 1

logger = logging.getLogger(__name__)

def proxy_menu(update: Update, context: CallbackContext):
    """Показывает меню управления прокси"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить прокси", callback_data='add_proxy'),
            InlineKeyboardButton("📋 Список прокси", callback_data='list_proxies')
        ],
        [
            InlineKeyboardButton("🔄 Проверить прокси", callback_data='check_proxies'),
            InlineKeyboardButton("📊 Распределить прокси", callback_data='distribute_proxies')
        ],
        [
            InlineKeyboardButton("📤 Импорт прокси", callback_data='import_proxies'),
            InlineKeyboardButton("🔙 Назад", callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text(
            "🔄 *Меню управления прокси*\n\n"
            "Выберите действие из списка ниже:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.callback_query.edit_message_text(
            "🔄 *Меню управления прокси*\n\n"
            "Выберите действие из списка ниже:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    # Явно завершаем состояние разговора
    return ConversationHandler.END

def start_add_proxy(update: Update, context: CallbackContext):
    """Начинает процесс добавления прокси"""
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "📝 *Добавление прокси*\n\n"
        "Отправьте прокси в формате:\n"
        "`host:port:username:password`\n\n"
        "Например: `154.13.71.245:6641:khbttott:sazhjvj8p21o`\n\n"
        "Вы также можете отправить несколько прокси, каждый с новой строки.",
        parse_mode=ParseMode.MARKDOWN
    )

    return PROXY_INPUT

def add_proxy_handler(update: Update, context: CallbackContext):
    """Обрабатывает ввод прокси"""
    text = update.message.text.strip()
    lines = text.split('\n')

    success_count = 0
    error_count = 0
    error_messages = []

    for line in lines:
        parts = line.strip().split(':')
        if len(parts) < 2 or len(parts) > 4:
            error_count += 1
            error_messages.append(f"Неверный формат: {line}")
            continue

        try:
            host = parts[0]
            port = int(parts[1])
            username = parts[2] if len(parts) > 2 else None
            password = parts[3] if len(parts) > 3 else None
            protocol = 'http'  # По умолчанию используем HTTP

            # Добавляем прокси в базу данных
            success, result = add_proxy(protocol, host, port, username, password)

            if success:
                success_count += 1
                logger.info(f"Добавлен прокси {host}:{port}")
            else:
                error_count += 1
                error_messages.append(f"Ошибка при добавлении {line}: {result}")
                logger.error(f"Ошибка при добавлении прокси: {result}")

        except Exception as e:
            error_count += 1
            error_messages.append(f"Ошибка при добавлении {line}: {str(e)}")
            logger.error(f"Ошибка при добавлении прокси: {e}")

    # Формируем ответное сообщение
    response = f"✅ Успешно добавлено прокси: {success_count}\n"
    if error_count > 0:
        response += f"❌ Ошибок: {error_count}\n\n"
        if len(error_messages) > 5:
            response += "Первые 5 ошибок:\n"
            for i, msg in enumerate(error_messages[:5]):
                response += f"{i+1}. {msg}\n"
        else:
            response += "Ошибки:\n"
            for i, msg in enumerate(error_messages):
                response += f"{i+1}. {msg}\n"

    keyboard = [
        [InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(response, reply_markup=reply_markup)
    return ConversationHandler.END

def list_proxies_handler(update: Update, context: CallbackContext):
    """Показывает список прокси с пагинацией"""
    query = update.callback_query
    query.answer()

    # Извлекаем номер страницы из callback_data
    page = 1
    if query.data.startswith("list_proxies_page_"):
        try:
            page = int(query.data.split("_")[-1])
        except (ValueError, IndexError):
            page = 1

    proxies = get_proxies()

    if not proxies:
        keyboard = [
            [InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            "📋 *Список прокси*\n\n"
            "Прокси не найдены.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END

    # Пагинация: показываем по 5 прокси на страницу (с кнопками)
    proxies_per_page = 5
    total_pages = (len(proxies) + proxies_per_page - 1) // proxies_per_page
    start_idx = (page - 1) * proxies_per_page
    end_idx = start_idx + proxies_per_page
    page_proxies = proxies[start_idx:end_idx]

    # Создаем список прокси с кнопками для каждого
    message = f"📋 *Список прокси* (страница {page}/{total_pages})\n\n"
    keyboard = []

    for proxy in page_proxies:
        status = "✅ Активен" if proxy.is_active else "❌ Неактивен"
        auth_info = " 🔐" if proxy.username else ""

        message += f"*ID {proxy.id}*: {proxy.host}:{proxy.port} - {proxy.protocol.upper()}{auth_info} - {status}\n"

        # Добавляем кнопки для каждого прокси
        keyboard.append([
            InlineKeyboardButton(f"🔄 Проверить #{proxy.id}", callback_data=f'check_proxy_{proxy.id}'),
            InlineKeyboardButton(f"❌ Удалить #{proxy.id}", callback_data=f'delete_proxy_{proxy.id}')
        ])

    # Кнопки навигации по страницам
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Пред", callback_data=f"list_proxies_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("След ➡️", callback_data=f"list_proxies_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка удаления всех прокси (только если есть прокси)
    if len(proxies) > 0:
        keyboard.append([InlineKeyboardButton("🗑️ Удалить все прокси", callback_data='delete_all_proxies')])

    keyboard.append([InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

    return ConversationHandler.END

def check_proxy_handler(update: Update, context: CallbackContext):
    """Проверяет работоспособность прокси"""
    query = update.callback_query
    query.answer()

    proxy_id = int(query.data.split('_')[-1])

    # Получаем прокси из базы данных
    proxy = next((p for p in get_proxies() if p.id == proxy_id), None)

    if not proxy:
        query.edit_message_text(
            "❌ Прокси не найден."
        )
        return ConversationHandler.END

    query.edit_message_text(
        f"🔄 Проверка прокси {proxy.host}:{proxy.port}... Пожалуйста, подождите."
    )

    # Проверяем прокси (передаем объект proxy напрямую)
    _, is_working, error = check_proxy(proxy)

    # Обновляем статус прокси в базе данных
    update_proxy(proxy_id, is_active=is_working)

    keyboard = [
        [InlineKeyboardButton("🔙 К списку прокси", callback_data='list_proxies')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_working:
        query.edit_message_text(
            f"✅ Прокси {proxy.host}:{proxy.port} работает!",
            reply_markup=reply_markup
        )
    else:
        query.edit_message_text(
            f"❌ Прокси {proxy.host}:{proxy.port} не работает!\nОшибка: {error}",
            reply_markup=reply_markup
        )

    # Очищаем данные пользователя и завершаем состояние
    context.user_data.clear()
    return ConversationHandler.END

def delete_proxy_handler(update: Update, context: CallbackContext):
    """Удаляет прокси"""
    query = update.callback_query
    query.answer()

    proxy_id = int(query.data.split('_')[-1])

    # Получаем прокси из базы данных
    proxy = next((p for p in get_proxies() if p.id == proxy_id), None)

    if not proxy:
        query.edit_message_text(
            "❌ Прокси не найден."
        )
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f'confirm_delete_proxy_{proxy_id}'),
            InlineKeyboardButton("❌ Отмена", callback_data='list_proxies')
        ],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        f"❓ Вы уверены, что хотите удалить прокси {proxy.host}:{proxy.port}?",
        reply_markup=reply_markup
    )

    return ConversationHandler.END

def confirm_delete_proxy_handler(update: Update, context: CallbackContext):
    """Подтверждает удаление прокси"""
    query = update.callback_query
    query.answer()

    proxy_id = int(query.data.split('_')[-1])

    # Удаляем прокси из базы данных
    success, result = delete_proxy(proxy_id)

    keyboard = [
        [InlineKeyboardButton("🔙 К списку прокси", callback_data='list_proxies')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if success:
        query.edit_message_text(
            f"✅ Прокси успешно удален!",
            reply_markup=reply_markup
        )
    else:
        query.edit_message_text(
            f"❌ Ошибка при удалении прокси: {result}",
            reply_markup=reply_markup
        )

    return ConversationHandler.END

def check_all_proxies_handler(update: Update, context: CallbackContext):
    """Проверяет все прокси"""
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "🔄 Проверка всех прокси... Пожалуйста, подождите."
    )

    # Проверяем все прокси
    results = check_all_proxies()

    # Подсчитываем статистику
    total = len(results)
    working = sum(1 for result in results.values() if result['working'])

    keyboard = [
        [InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        f"✅ Проверка завершена!\n\n"
        f"Всего прокси: {total}\n"
        f"Работающих: {working}\n"
        f"Неработающих: {total - working}",
        reply_markup=reply_markup
    )

    # Очищаем данные пользователя и завершаем состояние
    context.user_data.clear()
    return ConversationHandler.END

def distribute_proxies_handler(update: Update, context: CallbackContext):
    """Распределяет прокси между аккаунтами"""
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "🔄 Распределение прокси между аккаунтами... Пожалуйста, подождите."
    )

    # Распределяем прокси
    success, result = distribute_proxies()

    keyboard = [
        [InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if success:
        query.edit_message_text(
            f"✅ Прокси успешно распределены!\n\n{result}",
            reply_markup=reply_markup
        )
    else:
        query.edit_message_text(
            f"❌ Ошибка при распределении прокси: {result}",
            reply_markup=reply_markup
        )

    # Очищаем данные пользователя и завершаем состояние
    context.user_data.clear()
    return ConversationHandler.END

def import_proxies_handler(update: Update, context: CallbackContext):
    """Начинает процесс импорта прокси из файла"""
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        "📤 *Импорт прокси из файла*\n\n"
        "Отправьте текстовый файл со списком прокси в формате:\n"
        "`host:port:username:password`\n\n"
        "Каждый прокси должен быть на новой строке.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

    # Устанавливаем состояние для ожидания файла
    context.user_data['waiting_for_proxy_file'] = True

    return ConversationHandler.END

def process_proxy_file(update: Update, context: CallbackContext):
    """Обрабатывает файл с прокси"""
    if not context.user_data.get('waiting_for_proxy_file', False):
        return

    # Сбрасываем флаг ожидания файла
    context.user_data['waiting_for_proxy_file'] = False

    # Проверяем, что получен файл
    if not update.message.document:
        update.message.reply_text(
            "❌ Пожалуйста, отправьте текстовый файл."
        )
        return

    # Проверяем, что файл текстовый
    file = update.message.document
    if not file.mime_type.startswith('text/'):
        update.message.reply_text(
            "❌ Пожалуйста, отправьте текстовый файл."
        )
        return

    # Скачиваем файл
    file_id = file.file_id
    new_file = context.bot.get_file(file_id)
    file_content = new_file.download_as_bytearray().decode('utf-8')

    # Парсим прокси из файла
    lines = file_content.strip().split('\n')
    success_count = 0
    error_count = 0
    error_messages = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(':')
        if len(parts) < 2 or len(parts) > 4:
            error_count += 1
            error_messages.append(f"Неверный формат: {line}")
            continue

        try:
            host = parts[0]
            port = int(parts[1])
            username = parts[2] if len(parts) > 2 else None
            password = parts[3] if len(parts) > 3 else None
            protocol = 'http'  # По умолчанию используем HTTP

            # Добавляем прокси в базу данных
            success, result = add_proxy(protocol, host, port, username, password)

            if success:
                success_count += 1
            else:
                error_count += 1
                error_messages.append(f"Ошибка при добавлении {line}: {result}")
        except Exception as e:
            error_count += 1
            error_messages.append(f"Ошибка при парсинге: {line} - {str(e)}")

    # Формируем отчет
    message = f"📤 *Результаты импорта прокси*\n\n"
    message += f"Всего строк: {len(lines)}\n"
    message += f"Успешно добавлено: {success_count}\n"
    message += f"Ошибок: {error_count}\n\n"

    if error_messages:
        message += "*Ошибки:*\n"
        for i, error in enumerate(error_messages[:10]):  # Показываем только первые 10 ошибок
            message += f"{i+1}. {error}\n"

        if len(error_messages) > 10:
            message += f"... и еще {len(error_messages) - 10} ошибок."

    keyboard = [
        [InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

    # Очищаем данные пользователя
    context.user_data.clear()

def delete_all_proxies_handler(update: Update, context: CallbackContext):
    """Показывает подтверждение удаления всех прокси"""
    query = update.callback_query
    query.answer()

    proxies = get_proxies()
    proxies_count = len(proxies)

    keyboard = [
        [InlineKeyboardButton("⚠️ Да, удалить все", callback_data='confirm_delete_all_proxies')],
        [InlineKeyboardButton("❌ Отмена", callback_data='list_proxies')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы действительно хотите удалить все {proxies_count} прокси?\n\n"
        f"❗ *Это действие нельзя отменить!*",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

    return ConversationHandler.END

def confirm_delete_all_proxies_handler(update: Update, context: CallbackContext):
    """Удаляет все прокси после подтверждения"""
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "🗑️ Удаление всех прокси... Пожалуйста, подождите."
    )

    try:
        # Получаем все прокси
        proxies = get_proxies()
        deleted_count = 0

        # Удаляем каждый прокси
        for proxy in proxies:
            success = delete_proxy(proxy.id)
            if success:
                deleted_count += 1

        keyboard = [
            [InlineKeyboardButton("🔙 К меню прокси", callback_data='menu_proxy')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if deleted_count > 0:
            query.edit_message_text(
                f"✅ *Успешно удалено {deleted_count} прокси*\n\n"
                f"Все прокси были удалены из системы.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            query.edit_message_text(
                f"⚠️ *Не удалось удалить прокси*\n\n"
                f"Возможно, прокси уже были удалены или произошла ошибка.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        logger.error(f"Ошибка при удалении всех прокси: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🔙 К списку прокси", callback_data='list_proxies')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            f"❌ *Ошибка при удалении прокси*\n\n"
            f"Произошла ошибка: {str(e)}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    # Очищаем данные пользователя и завершаем состояние
    context.user_data.clear()
    return ConversationHandler.END

def main_menu_handler(update: Update, context: CallbackContext):
    """Возвращает пользователя в главное меню"""
    query = update.callback_query
    query.answer()

    # Очищаем все данные пользователя
    context.user_data.clear()

    # Показываем главное меню
    from telegram_bot.keyboards import get_main_menu_keyboard
    query.edit_message_text(
        "🏠 Главное меню\nВыберите действие:",
        reply_markup=get_main_menu_keyboard()
    )

    return ConversationHandler.END

def get_proxy_handlers():
    """Возвращает обработчики для управления прокси"""
    # Обработчик для добавления прокси
    add_proxy_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_proxy, pattern='^add_proxy$')],
        states={
            PROXY_INPUT: [MessageHandler(Filters.text & ~Filters.command, add_proxy_handler)]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    return [
        CommandHandler("proxy", proxy_menu),
        CallbackQueryHandler(proxy_menu, pattern='^menu_proxy$'),
        add_proxy_conv_handler,
        CallbackQueryHandler(list_proxies_handler, pattern='^list_proxies$'),
        CallbackQueryHandler(list_proxies_handler, pattern=r'^list_proxies_page_\d+$'),
        CallbackQueryHandler(check_proxy_handler, pattern=r'^check_proxy_\d+$'),
        CallbackQueryHandler(delete_proxy_handler, pattern=r'^delete_proxy_\d+$'),
        CallbackQueryHandler(confirm_delete_proxy_handler, pattern=r'^confirm_delete_proxy_\d+$'),
        CallbackQueryHandler(delete_all_proxies_handler, pattern='^delete_all_proxies$'),
        CallbackQueryHandler(confirm_delete_all_proxies_handler, pattern='^confirm_delete_all_proxies$'),
        CallbackQueryHandler(check_all_proxies_handler, pattern='^check_proxies$'),
        CallbackQueryHandler(distribute_proxies_handler, pattern='^distribute_proxies$'),
        CallbackQueryHandler(import_proxies_handler, pattern='^import_proxies$'),
        CallbackQueryHandler(main_menu_handler, pattern='^main_menu$'),
        MessageHandler(Filters.document, process_proxy_file)
    ]