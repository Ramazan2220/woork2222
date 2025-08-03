# 🚀 Instagram Automation Bot MVP

## 📋 Описание
MVP версия Instagram Automation Bot с интегрированными системами безопасности, прогрева и ML-мониторинга.

## ✨ Ключевые возможности MVP

### 1. **Безопасность**
- ✅ Шифрование паролей (AES-256)
- ✅ Автоматические бэкапы БД каждые 6 часов
- ✅ Изоляция чувствительных данных

### 2. **Умная автоматизация**
- ✅ Централизованный Rate Limiter
- ✅ ML прогнозирование рисков бана
- ✅ Мониторинг здоровья аккаунтов
- ✅ Адаптивный прогрев

### 3. **Основные функции**
- ✅ Публикация контента (посты, stories, reels)
- ✅ Автоподписки с фильтрами
- ✅ Управление через Telegram Bot
- ✅ Web API для интеграций

## 🛠️ Установка

### 1. Клонирование и настройка
```bash
git clone [repository_url]
cd instagram_telegram_bot
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
pip install cryptography  # Для шифрования
```

### 4. Настройка конфигурации
```bash
cp config.example.py config.py
# Отредактируйте config.py и добавьте ваши данные:
# - TELEGRAM_BOT_TOKEN
# - ADMIN_USER_IDS
```

### 5. Первый запуск

#### 5.1 Создание бэкапа БД (если есть существующая)
```bash
python backup_database.py
# Выберите опцию 1
```

#### 5.2 Шифрование паролей
```bash
python encrypt_existing_passwords.py
# Подтвердите операцию
```

#### 5.3 Очистка проекта (опционально)
```bash
# Удаление DEBUG логов
python clean_debug_logs.py

# Очистка временных файлов
python cleanup_project.py
```

## 🚀 Запуск

### Основной бот
```bash
python main.py
```

### Автоматические бэкапы (в отдельном терминале)
```bash
python backup_database.py
# Выберите опцию 3
```

### Web API (опционально)
```bash
python web_api.py
# API будет доступен на http://localhost:5000
```

## 📱 Использование

### 1. Добавление аккаунта
1. В Telegram боте: `/start`
2. Выберите "➕ Добавить аккаунт"
3. Следуйте инструкциям

### 2. Проверка статуса аккаунтов
```python
from services.account_automation import automation_service

# Получить статус всех аккаунтов
recommendations = automation_service.get_daily_recommendations()
for account_id, data in recommendations.items():
    print(f"Аккаунт: {data['username']}")
    print(f"Здоровье: {data['health_score']}/100")
    print(f"Риск бана: {data['ban_risk']}/100")
```

### 3. Умный прогрев
```python
# Запустить прогрев с учетом рисков
success, message = automation_service.smart_warm_account(
    account_id=1,
    duration_minutes=30
)
```

### 4. Безопасное выполнение действий
```python
from services.rate_limiter import ActionType

# Любое действие с проверками безопасности
success, result = automation_service.perform_safe_action(
    account_id=1,
    action_type=ActionType.POST,
    action_func=publish_post,
    content="Hello World!",
    media_path="photo.jpg"
)
```

## 🔒 Безопасность

### Шифрование
- Все пароли Instagram автоматически шифруются
- Ключ шифрования хранится в `.encryption_key`
- **ВАЖНО**: Сделайте резервную копию `.encryption_key`!

### Лимиты (автоматические)
- Новые аккаунты (< 7 дней): 20 подписок/день
- Прогретые (> 30 дней): 200 подписок/день
- Адаптивные задержки между действиями

### Мониторинг
- Health Score: 0-100 (здоровье аккаунта)
- Ban Risk: 0-100 (риск блокировки)
- Автоматическая остановка при риске > 70

## 📊 Архитектура MVP

```
instagram_telegram_bot/
├── services/              # Централизованные сервисы
│   ├── instagram_service.py    # Работа с Instagram
│   ├── rate_limiter.py        # Контроль лимитов
│   └── account_automation.py   # Умная автоматизация
├── instagram/             # Instagram модули
│   ├── health_monitor.py      # Мониторинг здоровья
│   ├── predictive_monitor.py  # ML прогнозирование
│   └── improved_warmer.py     # Система прогрева
├── database/              # База данных
├── telegram_bot/          # Telegram интерфейс
├── utils/                 # Утилиты
│   └── encryption.py          # Шифрование
└── web_api.py            # REST API
```

## ⚠️ Важные замечания

1. **Юридические риски**: Использование автоматизации нарушает ToS Instagram
2. **Прокси**: Рекомендуется использовать качественные residential прокси
3. **Масштабирование**: SQLite подходит для < 100 активных аккаунтов
4. **Мониторинг**: Регулярно проверяйте логи и статусы аккаунтов

## 🛟 Поддержка

При возникновении проблем:
1. Проверьте логи в `data/logs/`
2. Убедитесь, что все зависимости установлены
3. Проверьте правильность конфигурации
4. Восстановите БД из бэкапа при необходимости

## 📈 Дальнейшее развитие

### Неделя 2 (после MVP):
- [ ] Миграция на PostgreSQL
- [ ] Docker контейнеризация
- [ ] CI/CD pipeline
- [ ] Unit тесты (coverage > 60%)

### Месяц 2-3:
- [ ] Микросервисная архитектура
- [ ] Kubernetes deployment
- [ ] Система подписок (монетизация)
- [ ] Официальное API где возможно

---

**MVP Version 1.0** | Создано за 2 недели | Готово к тестированию 