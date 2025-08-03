from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from datetime import datetime, timedelta
import math

from ..config.admin_list import is_admin, has_permission, Permission
from ..services.user_service import UserService
from ..models.user import SubscriptionPlan, UserStatus, PLAN_INFO
from ..middleware.admin_auth import admin_required, permission_required

# Глобальный сервис пользователей
user_service = UserService()

@admin_required
def users_menu(update: Update, context: CallbackContext):
    """Главное меню управления пользователями"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.VIEW_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    # Получаем статистику
    stats = user_service.get_statistics()
    
    text = f"""👥 **УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ**

📊 **Статистика:**
• Всего пользователей: {stats['total_users']}
• Активных: {stats['active_users']}
• На триале: {stats['trial_users']}
• Заблокированных: {stats['blocked_users']}
• Истекших: {stats['expired_users']}

💰 **Оценочный доход:** ${stats['estimated_revenue']:.2f}
"""
    
    keyboard = [
        [InlineKeyboardButton("👁️ Просмотр пользователей", callback_data="users_list")],
        [InlineKeyboardButton("➕ Добавить пользователя", callback_data="users_add")],
        [InlineKeyboardButton("🔍 Поиск пользователя", callback_data="users_search")],
        [InlineKeyboardButton("📊 Статистика по планам", callback_data="users_plans_stats")],
        [InlineKeyboardButton("⏰ Истекающие подписки", callback_data="users_expiring")],
        [InlineKeyboardButton("🔧 Массовые операции", callback_data="users_bulk_operations")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

@admin_required
def users_list(update: Update, context: CallbackContext):
    """Список пользователей с пагинацией"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.VIEW_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    # Параметры пагинации
    page = int(context.user_data.get('users_page', 1))
    per_page = 10
    
    users = user_service.get_all_users()
    total_pages = math.ceil(len(users) / per_page)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_users = users[start_idx:end_idx]
    
    text = f"👥 **СПИСОК ПОЛЬЗОВАТЕЛЕЙ** (стр. {page}/{total_pages})\n\n"
    
    # Кнопки пользователей и их краткая информация
    keyboard = []
    user_buttons = []
    
    for i, user in enumerate(page_users, start_idx + 1):
        status_emoji = "✅" if user.is_active else "❌" if user.status == UserStatus.BLOCKED else "⏰"
        plan_name = PLAN_INFO[user.subscription_plan]['name'] if user.subscription_plan else "Без плана"
        
        # Краткая информация в тексте (экранируем для Markdown)
        username_display = user.username or 'Нет username'
        # Экранируем специальные символы для Markdown
        username_display = username_display.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
        
        text += f"{i}. {status_emoji} @{username_display}\n"
        text += f"   ID: `{user.telegram_id}` | {plan_name}\n\n"
        
        # Кнопка для перехода к деталям пользователя
        button_text = f"{status_emoji} @{user.username or str(user.telegram_id)}"
        user_buttons.append(InlineKeyboardButton(button_text, callback_data=f"user_detail_{user.telegram_id}"))
        
        # Добавляем по 2 кнопки в ряд
        if len(user_buttons) == 2:
            keyboard.append(user_buttons)
            user_buttons = []
    
    # Добавляем оставшуюся кнопку если есть
    if user_buttons:
        keyboard.append(user_buttons)
    
    # Управление страницами
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Пред", callback_data=f"users_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ След", callback_data=f"users_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопки действий
    keyboard.extend([
        [InlineKeyboardButton("🔍 Поиск", callback_data="users_search")],
        [InlineKeyboardButton("🆕 Добавить пользователя", callback_data="users_add")] if has_permission(user_id, Permission.MANAGE_USERS) else [],
        [InlineKeyboardButton("🔙 Назад", callback_data="users_menu")]
    ])
    
    # Удаляем пустые списки
    keyboard = [row for row in keyboard if row]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

@admin_required
def users_plans_stats(update: Update, context: CallbackContext):
    """Статистика по тарифным планам"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.VIEW_ANALYTICS):
        query.answer("❌ Недостаточно прав")
        return
    
    stats = user_service.get_statistics()
    
    text = "📊 **СТАТИСТИКА ПО ТАРИФНЫМ ПЛАНАМ**\n\n"
    
    total_revenue = 0
    for plan in SubscriptionPlan:
        count = stats['plans_distribution'].get(plan.value, 0)
        if count > 0:
            plan_info = PLAN_INFO[plan]
            revenue = count * plan_info['price']
            total_revenue += revenue
            
            text += f"**{plan_info['name']}**\n"
            text += f"• Пользователей: {count}\n"
            text += f"• Цена: ${plan_info['price']}\n"
            text += f"• Доход: ${revenue:.2f}\n\n"
    
    text += f"💰 **Общий доход:** ${total_revenue:.2f}\n"
    text += f"📈 **Средний чек:** ${total_revenue / max(stats['total_users'], 1):.2f}"
    
    keyboard = [
        [InlineKeyboardButton("📊 Экспорт данных", callback_data="users_export_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="users_menu")]
    ]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

@admin_required
def users_add(update: Update, context: CallbackContext):
    """Добавление нового пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    text = """➕ **ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ**

📝 Введите данные пользователя в формате:
`telegram_id username plan`

**Доступные планы:**
• `trial_1` - Триал 1 день
• `trial_3` - Триал 3 дня  
• `trial_7` - Триал 7 дней
• `month` - 30 дней ($200)
• `3month` - 3 месяца ($400)
• `lifetime` - Навсегда ($500)

**Пример:**
`123456789 testuser month`

Или нажмите "Отмена" для возврата в меню."""

    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="users_menu")]
    ]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # Устанавливаем состояние ожидания данных пользователя
    context.user_data['waiting_for'] = 'user_add_data'

@admin_required
def users_search(update: Update, context: CallbackContext):
    """Поиск пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.VIEW_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    text = """🔍 **ПОИСК ПОЛЬЗОВАТЕЛЯ**

📝 Введите для поиска:
• Telegram ID (например: 123456789)
• Username (например: @username или username)

Или нажмите "Отмена" для возврата в меню."""

    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="users_menu")]
    ]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # Устанавливаем состояние ожидания поискового запроса
    context.user_data['waiting_for'] = 'user_search_query'

@admin_required
def users_expiring(update: Update, context: CallbackContext):
    """Пользователи с истекающими подписками"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.VIEW_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    # Получаем пользователей с истекающими подписками в течение 7 дней
    expiring_users = user_service.get_expiring_users(days=7)
    
    text = f"⏰ **ИСТЕКАЮЩИЕ ПОДПИСКИ** ({len(expiring_users)} чел.)\n\n"
    
    if not expiring_users:
        text += "✅ Нет пользователей с истекающими подписками в ближайшие 7 дней"
    else:
        for user in expiring_users[:10]:  # Показываем только первых 10
            days_left = user.days_remaining
            urgency = "🔴" if days_left <= 1 else "🟡" if days_left <= 3 else "🟢"
            
            text += f"{urgency} @{user.username or 'Нет username'}\n"
            text += f"   ID: `{user.telegram_id}`\n"
            text += f"   План: {PLAN_INFO[user.subscription_plan]['name']}\n"
            text += f"   Истекает через: {days_left} дн.\n\n"
        
        if len(expiring_users) > 10:
            text += f"... и еще {len(expiring_users) - 10} пользователей"
    
    keyboard = [
        [InlineKeyboardButton("📬 Отправить уведомления", callback_data="users_notify_expiring")] if expiring_users and has_permission(user_id, Permission.SEND_NOTIFICATIONS) else [],
        [InlineKeyboardButton("📊 Полный список", callback_data="users_expiring_full")],
        [InlineKeyboardButton("🔙 Назад", callback_data="users_menu")]
    ]
    
    # Удаляем пустые списки
    keyboard = [row for row in keyboard if row]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

@admin_required 
def user_detail(update: Update, context: CallbackContext):
    """Показывает детальную информацию о пользователе"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.VIEW_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    # Извлекаем ID пользователя из callback_data
    target_user_id = int(query.data.split('_')[-1])
    user = user_service.get_user(target_user_id)
    
    if not user:
        query.answer("❌ Пользователь не найден")
        return
    
    plan_info = PLAN_INFO.get(user.subscription_plan, {})
    
    # Получаем статистику пользователя из основной системы
    from utils.subscription_service import subscription_service
    user_stats = subscription_service.get_user_stats(target_user_id)
    
    text = f"""👤 **ПОЛЬЗОВАТЕЛЬ {user.username or 'Без username'}**

🆔 **ID:** `{user.telegram_id}`
👤 **Username:** @{user.username or 'не указан'}
📅 **Регистрация:** {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else 'Неизвестно'}
🕐 **Последняя активность:** {user.last_activity.strftime('%d.%m.%Y %H:%M') if user.last_activity else 'Неизвестно'}

💎 **Подписка:**
• План: {plan_info.get('name', 'Неизвестный план')}
• Цена: ${plan_info.get('price', 0)}
• Статус: {user.status.value}
• Начало: {user.subscription_start.strftime('%d.%m.%Y') if user.subscription_start else 'Неизвестно'}
• Окончание: {user.subscription_end.strftime('%d.%m.%Y') if user.subscription_end else '♾️ Навсегда'}
• Дней осталось: {user.days_remaining if user.days_remaining != float('inf') else '♾️'}

📱 **Статистика:**
• Аккаунтов добавлено: {user.accounts_count}
• Доступ к системе: {'✅ Есть' if user_stats.get('has_access') else '❌ Нет'}
• Триальный: {'✅ Да' if user.is_trial else '❌ Нет'}"""

    keyboard = []
    
    # Кнопки управления (только для пользователей с правами)
    if has_permission(user_id, Permission.MANAGE_USERS):
        keyboard.append([
            InlineKeyboardButton("✏️ Изменить план", callback_data=f"user_edit_plan_{target_user_id}"),
            InlineKeyboardButton("⏰ Продлить", callback_data=f"user_extend_{target_user_id}")
        ])
        
        if user.status == UserStatus.BLOCKED:
            keyboard.append([InlineKeyboardButton("🔓 Разблокировать", callback_data=f"user_unblock_{target_user_id}")])
        else:
            keyboard.append([InlineKeyboardButton("🚫 Заблокировать", callback_data=f"user_block_{target_user_id}")])
        
        # Кнопка удаления пользователя
        keyboard.append([InlineKeyboardButton("🗑️ Удалить пользователя", callback_data=f"user_delete_{target_user_id}")])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Обновить", callback_data=f"user_detail_{target_user_id}"),
        InlineKeyboardButton("◀️ К списку", callback_data="users_list")
    ])
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

@admin_required
def users_bulk_operations(update: Update, context: CallbackContext):
    """Массовые операции с пользователями"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    stats = user_service.get_statistics()
    
    text = f"""🔧 **МАССОВЫЕ ОПЕРАЦИИ**

📊 **Текущая статистика:**
• Всего пользователей: {stats['total_users']}
• Истекших подписок: {stats['expired_users']}
• Заблокированных: {stats['blocked_users']}

⚠️ **Доступные операции:**"""

    keyboard = [
        [InlineKeyboardButton("🧹 Очистить истекших", callback_data="bulk_clean_expired")],
        [InlineKeyboardButton("📧 Уведомить об истечении", callback_data="bulk_notify_expiring")],
        [InlineKeyboardButton("📊 Экспорт пользователей", callback_data="bulk_export_users")],
        [InlineKeyboardButton("◀️ Назад", callback_data="users_menu")]
    ]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def handle_user_input(update: Update, context: CallbackContext):
    """Обрабатывает текстовый ввод для управления пользователями"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    waiting_for = context.user_data.get('waiting_for')
    text = update.message.text.strip()
    
    if waiting_for == 'user_add_data':
        handle_add_user_data(update, context, text)
    elif waiting_for == 'user_search_query':
        handle_search_user(update, context, text)
    elif waiting_for == 'user_extend_days':
        handle_extend_user(update, context, text)

def handle_add_user_data(update: Update, context: CallbackContext, text: str):
    """Обрабатывает добавление нового пользователя"""
    try:
        parts = text.split()
        if len(parts) != 3:
            update.message.reply_text("❌ Неверный формат. Используйте: `telegram_id username plan`", parse_mode='Markdown')
            return
        
        telegram_id, username, plan_code = parts
        telegram_id = int(telegram_id)
        
        # Маппинг кодов планов
        plan_mapping = {
            'trial_1': SubscriptionPlan.FREE_TRIAL_1_DAY,
            'trial_3': SubscriptionPlan.FREE_TRIAL_3_DAYS,
            'trial_7': SubscriptionPlan.FREE_TRIAL_7_DAYS,
            'month': SubscriptionPlan.SUBSCRIPTION_30_DAYS,
            '3month': SubscriptionPlan.SUBSCRIPTION_90_DAYS,
            'lifetime': SubscriptionPlan.SUBSCRIPTION_LIFETIME
        }
        
        if plan_code not in plan_mapping:
            update.message.reply_text("❌ Неверный код плана. Используйте: trial_1, trial_3, trial_7, month, 3month, lifetime")
            return
        
        plan = plan_mapping[plan_code]
        
        # Проверяем, существует ли пользователь
        existing_user = user_service.get_user(telegram_id)
        if existing_user:
            update.message.reply_text(f"❌ Пользователь с ID {telegram_id} уже существует!")
            return
        
        # Создаем пользователя
        user = user_service.create_user(telegram_id, username)
        user.set_subscription(plan)
        user_service.update_user(user)
        
        # КРИТИЧЕСКИ ВАЖНО: Сохраняем данные в файл!
        user_service.save_users()
        
        plan_info = PLAN_INFO[plan]
        
        update.message.reply_text(
            f"✅ **Пользователь добавлен успешно!**\n\n"
            f"👤 Username: @{username}\n"
            f"🆔 ID: {telegram_id}\n"
            f"💎 План: {plan_info['name']}\n"
            f"💰 Цена: ${plan_info['price']}\n"
            f"⏰ Дней: {plan_info['duration'] if plan_info['duration'] else '♾️'}",
            parse_mode='Markdown'
        )
        
        # Очищаем состояние
        context.user_data.pop('waiting_for', None)
        
    except ValueError:
        update.message.reply_text("❌ Неверный формат Telegram ID. Используйте числовой ID.")
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при добавлении пользователя: {str(e)}")

def handle_search_user(update: Update, context: CallbackContext, query_text: str):
    """Обрабатывает поиск пользователя"""
    try:
        users = user_service.get_all_users()
        found_users = []
        
        # Убираем @ если есть
        search_query = query_text.replace('@', '').lower()
        
        for user in users:
            # Поиск по ID
            if search_query.isdigit() and str(user.telegram_id) == search_query:
                found_users.append(user)
                continue
            
            # Поиск по username
            if user.username and search_query in user.username.lower():
                found_users.append(user)
        
        if not found_users:
            update.message.reply_text("❌ Пользователи не найдены")
            context.user_data.pop('waiting_for', None)
            return
        
        if len(found_users) == 1:
            # Если найден один пользователь, показываем детали
            user = found_users[0]
            show_user_detail_text(update, user)
        else:
            # Если найдено несколько, показываем список
            text = f"🔍 **Найдено пользователей: {len(found_users)}**\n\n"
            
            for i, user in enumerate(found_users[:10], 1):  # Показываем первых 10
                status_emoji = "✅" if user.is_active else "❌" if user.status == UserStatus.BLOCKED else "⏰"
                plan_name = PLAN_INFO[user.subscription_plan]['name'] if user.subscription_plan else "Без плана"
                text += f"{i}. {status_emoji} @{user.username or 'Нет username'} | ID: {user.telegram_id}\n"
                text += f"   {plan_name}\n\n"
            
            if len(found_users) > 10:
                text += f"... и еще {len(found_users) - 10} пользователей"
            
            update.message.reply_text(text, parse_mode='Markdown')
        
        # Очищаем состояние
        context.user_data.pop('waiting_for', None)
        
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка поиска: {str(e)}")

def show_user_detail_text(update: Update, user):
    """Показывает детали пользователя в текстовом формате"""
    plan_info = PLAN_INFO.get(user.subscription_plan, {})
    
    text = f"""👤 **НАЙДЕН ПОЛЬЗОВАТЕЛЬ**

🆔 **ID:** `{user.telegram_id}`
👤 **Username:** @{user.username or 'не указан'}
💎 **План:** {plan_info.get('name', 'Неизвестный план')}
💰 **Цена:** ${plan_info.get('price', 0)}
📅 **Статус:** {user.status.value}
⏰ **Дней осталось:** {user.days_remaining if user.days_remaining != float('inf') else '♾️'}
📱 **Аккаунтов:** {user.accounts_count}"""

    update.message.reply_text(text, parse_mode='Markdown')

# Обработчики навигации
def handle_users_callbacks(update: Update, context: CallbackContext):
    """Обрабатывает callback-и для управления пользователями"""
    query = update.callback_query
    data = query.data
    
    if data == "users_menu":
        users_menu(update, context)
    elif data == "users_list":
        users_list(update, context)
    elif data == "users_add":
        users_add(update, context)
    elif data == "users_search":
        users_search(update, context)
    elif data == "users_plans_stats":
        users_plans_stats(update, context)
    elif data == "users_expiring":
        users_expiring(update, context)
    elif data == "users_bulk_operations":
        users_bulk_operations(update, context)
    elif data.startswith("users_page_"):
        page = int(data.split('_')[-1])
        context.user_data['users_page'] = page
        users_list(update, context)
    elif data.startswith("user_detail_"):
        user_detail(update, context)
    elif data.startswith("user_block_"):
        handle_block_user(update, context)
    elif data.startswith("user_unblock_"):
        handle_unblock_user(update, context)
    elif data.startswith("user_edit_plan_"):
        handle_edit_user_plan(update, context)
    elif data.startswith("user_extend_"):
        handle_extend_user_menu(update, context)
    elif data.startswith("user_delete_"):
        handle_delete_user_confirm(update, context)
    elif data.startswith("confirm_delete_"):
        handle_delete_user_execute(update, context)
    elif data.startswith("cancel_delete_"):
        handle_cancel_delete_user(update, context)
    else:
        query.answer("🚧 Функция в разработке")

def handle_block_user(update: Update, context: CallbackContext):
    """Блокирует пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    target_user_id = int(query.data.split('_')[-1])
    
    success = user_service.block_user(target_user_id)
    if success:
        user_service.save_users()  # Сохраняем изменения
        query.answer("✅ Пользователь заблокирован")
        # Обновляем детали пользователя
        context.user_data['callback_data'] = f"user_detail_{target_user_id}"
        user_detail(update, context)
    else:
        query.answer("❌ Ошибка блокировки")

def handle_unblock_user(update: Update, context: CallbackContext):
    """Разблокирует пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    target_user_id = int(query.data.split('_')[-1])
    
    success = user_service.unblock_user(target_user_id)
    if success:
        user_service.save_users()  # Сохраняем изменения
        query.answer("✅ Пользователь разблокирован")
        # Обновляем детали пользователя
        context.user_data['callback_data'] = f"user_detail_{target_user_id}"
        user_detail(update, context)
    else:
        query.answer("❌ Ошибка разблокировки")

def handle_edit_user_plan(update: Update, context: CallbackContext):
    """Показывает меню изменения плана пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    target_user_id = int(query.data.split('_')[-1])
    user = user_service.get_user(target_user_id)
    
    if not user:
        query.answer("❌ Пользователь не найден")
        return
    
    text = f"""✏️ **ИЗМЕНЕНИЕ ПЛАНА**

👤 Пользователь: @{user.username or 'Без username'}
💎 Текущий план: {PLAN_INFO[user.subscription_plan]['name'] if user.subscription_plan else 'Без плана'}

🛒 **Выберите новый план:**"""

    keyboard = []
    for plan, info in PLAN_INFO.items():
        keyboard.append([InlineKeyboardButton(
            f"{info['name']} - ${info['price']}", 
            callback_data=f"set_plan_{target_user_id}_{plan.value}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=f"user_detail_{target_user_id}")])
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def handle_extend_user_menu(update: Update, context: CallbackContext):
    """Показывает меню продления подписки"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    target_user_id = int(query.data.split('_')[-1])
    
    text = f"""⏰ **ПРОДЛЕНИЕ ПОДПИСКИ**

📝 Введите количество дней для продления:
(например: 30, 90, 365)

Или нажмите "Отмена" для возврата."""

    keyboard = [
        [
            InlineKeyboardButton("30 дней", callback_data=f"extend_days_{target_user_id}_30"),
            InlineKeyboardButton("90 дней", callback_data=f"extend_days_{target_user_id}_90")
        ],
        [InlineKeyboardButton("365 дней", callback_data=f"extend_days_{target_user_id}_365")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"user_detail_{target_user_id}")]
    ]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def handle_delete_user_confirm(update: Update, context: CallbackContext):
    """Показывает подтверждение удаления пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    target_user_id = int(query.data.split('_')[-1])
    
    # Получаем данные пользователя
    user = user_service.get_user(target_user_id)
    if not user:
        query.answer("❌ Пользователь не найден")
        return
    
    text = f"""⚠️ **ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ**

👤 **Пользователь:** @{user.username} (ID: `{user.telegram_id}`)
📅 **Создан:** {user.created_at.strftime('%d.%m.%Y %H:%M')}
📊 **План:** {PLAN_INFO[user.subscription_plan]['name'] if user.subscription_plan else 'Без плана'}
💳 **Статус:** {user.status.value}

🗑️ **ВЫ УВЕРЕНЫ ЧТО ХОТИТЕ УДАЛИТЬ ЭТОГО ПОЛЬЗОВАТЕЛЯ?**

⚠️ Это действие **НЕОБРАТИМО**:
• Пользователь будет полностью удален из системы
• Все данные о подписке будут потеряны
• Доступ к основному боту будет заблокирован
• Восстановить пользователя можно будет только заново"""

    keyboard = [
        [
            InlineKeyboardButton("✅ ДА, УДАЛИТЬ", callback_data=f"confirm_delete_{target_user_id}"),
            InlineKeyboardButton("❌ ОТМЕНА", callback_data=f"cancel_delete_{target_user_id}")
        ]
    ]
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def handle_delete_user_execute(update: Update, context: CallbackContext):
    """Выполняет удаление пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not has_permission(user_id, Permission.MANAGE_USERS):
        query.answer("❌ Недостаточно прав")
        return
    
    target_user_id = int(query.data.split('_')[-1])
    
    # Получаем данные пользователя для логирования
    user = user_service.get_user(target_user_id)
    if not user:
        query.answer("❌ Пользователь не найден")
        return
    
    username = user.username
    
    # Удаляем пользователя
    success = user_service.delete_user(target_user_id)
    
    if success:
        user_service.save_users()  # Сохраняем изменения
        query.answer("✅ Пользователь удален")
        
        # Логируем действие
        admin_username = update.effective_user.username or update.effective_user.first_name
        logger.warning(f"🗑️ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ: Админ @{admin_username} (ID: {user_id}) удалил пользователя @{username} (ID: {target_user_id})")
        
        # Показываем результат
        text = f"""✅ **ПОЛЬЗОВАТЕЛЬ УДАЛЕН**

👤 **Удален:** @{username} (ID: `{target_user_id}`)
👨‍💼 **Администратор:** @{admin_username} (ID: `{user_id}`)
🕐 **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

✅ Пользователь полностью удален из системы.
🔒 Доступ к основному боту заблокирован."""

        keyboard = [
            [InlineKeyboardButton("📋 К списку пользователей", callback_data="users_list")]
        ]
        
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        query.answer("❌ Ошибка при удалении")
        # Возвращаемся к деталям пользователя
        context.user_data['callback_data'] = f"user_detail_{target_user_id}"
        user_detail(update, context)

def handle_cancel_delete_user(update: Update, context: CallbackContext):
    """Отменяет удаление пользователя"""
    query = update.callback_query
    target_user_id = int(query.data.split('_')[-1])
    
    query.answer("❌ Удаление отменено")
    
    # Возвращаемся к деталям пользователя
    context.user_data['callback_data'] = f"user_detail_{target_user_id}"
    user_detail(update, context)

# Вспомогательные функции
def format_user_for_list(user, index):
    """Форматирует пользователя для списка"""
    status_emoji = "✅" if user.is_active else "❌" if user.status == UserStatus.BLOCKED else "⏰"
    plan_name = PLAN_INFO[user.subscription_plan]['name'] if user.subscription_plan else "Без плана"
    
    return f"{index}. {status_emoji} @{user.username or 'Нет username'} | {plan_name}" 