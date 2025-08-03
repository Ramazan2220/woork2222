# 📤 ИНСТРУКЦИЯ ПО ЗАГРУЗКЕ НА MEGA.NZ И РАЗВЕРТЫВАНИЮ

## 🎯 У ВАС ЕСТЬ ДВА АРХИВА:

1. **`instagram_bot_vds.tar.gz`** (380KB) - для Linux VDS (Ubuntu/CentOS)
2. **`instagram_bot_windows_vds.zip`** (400KB) - для Windows VDS

## 📤 ШАГИ ДЛЯ MEGA.NZ:

### 1. Загрузка на MEGA:
1. Перейдите на https://mega.nz
2. Создайте аккаунт (если нет)
3. Загрузите нужный архив:
   - Для Linux: `instagram_bot_vds.tar.gz`
   - Для Windows: `instagram_bot_windows_vds.zip`
4. Получите ссылку для скачивания

### 2. Поделиться ссылкой:
- Правый клик на файл → "Получить ссылку"
- Копируйте ссылку
- Ссылка будет вида: `https://mega.nz/file/XXXXXXX#YYYYYYY`

## 🚀 РАЗВЕРТЫВАНИЕ НА VDS:

### ДЛЯ LINUX VDS (Ubuntu/CentOS):

```bash
# 1. Подключение к VDS
ssh root@your_server_ip

# 2. Скачивание с MEGA
wget "https://mega.nz/file/XXXXXXX#YYYYYYY" -O instagram_bot_vds.tar.gz

# 3. Распаковка
tar -xzf instagram_bot_vds.tar.gz
cd vds_deployment

# 4. Автоматическая установка
chmod +x quick_deploy.sh
./quick_deploy.sh

# 5. Настройка .env
nano .env
# Измените TELEGRAM_BOT_TOKEN и ENCRYPTION_KEY

# 6. Запуск
./start_bot.sh
```

### ДЛЯ WINDOWS VDS:

```cmd
REM 1. Подключение через RDP к Windows VDS
REM 2. Откройте браузер и скачайте архив с MEGA
REM 3. Распакуйте instagram_bot_windows_vds.zip
REM 4. Откройте папку instagram_bot
REM 5. Дважды щелкните quick_deploy.bat
REM 6. Отредактируйте .env файл (notepad .env)
REM 7. Запустите start_bot.bat
```

## ⚡ БЫСТРЫЙ СТАРТ (1 МИНУТА):

### Linux:
```bash
wget "ВАША_MEGA_ССЫЛКА" -O bot.tar.gz && tar -xzf bot.tar.gz && cd vds_deployment && chmod +x quick_deploy.sh && ./quick_deploy.sh
```

### Windows:
1. Скачать → Распаковать → `quick_deploy.bat` → Настроить `.env` → `start_bot.bat`

## 🔧 ВАЖНЫЕ НАСТРОЙКИ В .ENV:

```env
# ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ:
TELEGRAM_BOT_TOKEN=ваш_реальный_токен_бота
ENCRYPTION_KEY=ваш_32_символьный_ключ_шифрования

# Остальное можно оставить как есть:
DATABASE_URL=sqlite:///data/database.db
DEBUG=False
LOG_LEVEL=INFO
```

## 📋 ПОСЛЕ УСТАНОВКИ:

### Управление ботом:

**Linux:**
- Запуск: `./start_bot.sh`
- Остановка: `./stop_bot.sh`
- Статус: `./status_bot.sh`
- Логи: `./logs_bot.sh`

**Windows:**
- Запуск: двойной клик `start_bot.bat`
- Остановка: двойной клик `stop_bot.bat`
- Статус: двойной клик `status_bot.bat`
- Логи: двойной клик `view_logs.bat`

### Проверка работы:
1. Найдите своего бота в Telegram
2. Отправьте команду `/start`
3. Добавьте первый аккаунт Instagram
4. Попробуйте любую функцию

## 💡 ПРЕИМУЩЕСТВА MEGA.NZ:

✅ **Быстро:** Просто загрузить и поделиться ссылкой
✅ **Удобно:** Не нужны дополнительные инструменты
✅ **Безопасно:** Файлы зашифрованы
✅ **Бесплатно:** 20GB места бесплатно
✅ **Надежно:** Высокая скорость скачивания

## 🔍 АЛЬТЕРНАТИВЫ MEGA.NZ:

- **Google Drive** - хорошая альтернатива
- **Dropbox** - простое использование
- **Яндекс.Диск** - для российских пользователей
- **GitHub Releases** - для технических пользователей

## 🚨 РЕШЕНИЕ ПРОБЛЕМ:

### MEGA не скачивается:
```bash
# Установите megacmd (Linux)
sudo apt install megatools
megadl "ВАША_ССЫЛКА"

# Или используйте curl
curl -L "ВАША_ССЫЛКА" -o bot_archive.zip
```

### Windows блокирует файлы:
1. Правый клик на архив → Свойства
2. Поставьте галочку "Разблокировать"
3. Примените и распакуйте заново

### Python не найден (Windows):
1. Скачайте с python.org
2. При установке поставьте галочку "Add to PATH"
3. Перезагрузите компьютер

## 🎉 ГОТОВО!

Теперь ваш Instagram Telegram Bot работает на VDS 24/7!

**Файлы для загрузки на MEGA:**
- `instagram_bot_vds.tar.gz` (Linux)
- `instagram_bot_windows_vds.zip` (Windows)

**Не забудьте:**
- Настроить Telegram токен
- Добавить аккаунты Instagram
- Проверить логи после запуска 