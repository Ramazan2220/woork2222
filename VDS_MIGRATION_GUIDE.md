# 🚀 ПОЛНАЯ ИНСТРУКЦИЯ ПО ПЕРЕНОСУ БОТА НА VDS

## 📦 ЧТО У ВАС ЕСТЬ:

- `instagram_bot_vds.tar.gz` - архив с ботом для VDS
- Все необходимые файлы и инструкции

## 🎯 ПОШАГОВАЯ ИНСТРУКЦИЯ:

### 1. 🖥️ ВЫБОР И НАСТРОЙКА VDS

#### Рекомендуемые характеристики:
- **CPU:** 2-4 ядра
- **RAM:** 2-4 GB
- **Диск:** 20-40 GB SSD
- **ОС:** Ubuntu 20.04 LTS

#### Лучшие провайдеры:
- **Для России:** Selectel, Timeweb, REG.RU
- **Международные:** DigitalOcean, Vultr, Linode

### 2. 📤 ЗАГРУЗКА НА VDS

```bash
# Подключение по SSH
ssh root@your_server_ip

# Загрузка архива (через scp с локальной машины)
scp instagram_bot_vds.tar.gz root@your_server_ip:/root/

# Или скачивание с файлообменника
wget https://your-file-sharing-link/instagram_bot_vds.tar.gz
```

### 3. 🚀 БЫСТРОЕ РАЗВЕРТЫВАНИЕ

```bash
# Распаковка
tar -xzf instagram_bot_vds.tar.gz
cd vds_deployment

# Запуск автоматической установки
./quick_deploy.sh
```

**Скрипт сделает всё автоматически:**
- Установит зависимости
- Создаст виртуальное окружение
- Настроит systemd сервис
- Создаст скрипты управления

### 4. ⚙️ НАСТРОЙКА

```bash
# Редактирование конфигурации
nano .env
```

**Обязательно измените:**
```env
TELEGRAM_BOT_TOKEN=ваш_реальный_токен_бота
ENCRYPTION_KEY=ваш_32_символьный_ключ_шифрования
```

### 5. 🚀 ЗАПУСК

```bash
# Запуск бота
./start_bot.sh

# Проверка статуса
./status_bot.sh

# Просмотр логов
./logs_bot.sh
```

### 6. 🔧 УПРАВЛЕНИЕ БОТОМ

```bash
# Запуск
./start_bot.sh

# Остановка
./stop_bot.sh

# Статус и логи
./status_bot.sh

# Логи в реальном времени
./logs_bot.sh
```

### 7. 📊 МОНИТОРИНГ

```bash
# Системные ресурсы
htop

# Использование диска
df -h

# Оперативная память
free -h

# Логи системы
journalctl -u instagram_bot -f
```

## 🔒 БЕЗОПАСНОСТЬ

### Базовые настройки:
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Настройка firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Создание отдельного пользователя (рекомендуется)
sudo adduser botuser
sudo usermod -aG sudo botuser
```

### Смена портов SSH (рекомендуется):
```bash
sudo nano /etc/ssh/sshd_config
# Измените Port 22 на другой порт
sudo systemctl restart ssh
sudo ufw allow новый_порт/tcp
```

## 💾 БЭКАП

### Автоматический бэкап:
```bash
# Создание скрипта бэкапа
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_$DATE.tar.gz data/ .env
echo "Бэкап создан: backup_$DATE.tar.gz"
EOF

chmod +x backup.sh

# Добавление в crontab (ежедневно в 2:00)
echo "0 2 * * * /path/to/bot/backup.sh" | crontab -
```

## 🚨 РЕШЕНИЕ ПРОБЛЕМ

### Бот не запускается:
```bash
# Проверка логов
sudo journalctl -u instagram_bot -n 50

# Проверка конфигурации
cat .env

# Ручная проверка зависимостей
source bot_env/bin/activate
python -c "import telegram_bot, instagram, database"
```

### Проблемы с памятью:
```bash
# Добавление swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Проблемы с правами:
```bash
sudo chown -R $USER:$USER /path/to/bot
chmod +x *.sh
```

## 🔄 ОБНОВЛЕНИЕ

```bash
# Остановка бота
./stop_bot.sh

# Бэкап текущей версии
./backup.sh

# Загрузка новой версии
wget https://new-version-link/instagram_bot_vds.tar.gz

# Распаковка (с заменой файлов)
tar -xzf instagram_bot_vds.tar.gz --overwrite

# Обновление зависимостей
source bot_env/bin/activate
pip install -r requirements.txt

# Запуск
./start_bot.sh
```

## 📋 ЧЕКЛИСТ ПОСЛЕ УСТАНОВКИ

- [ ] Бот запущен и работает
- [ ] Telegram токен настроен
- [ ] Ключ шифрования установлен
- [ ] Добавлен первый аккаунт Instagram
- [ ] Настроен автозапуск
- [ ] Настроен firewall
- [ ] Настроен бэкап
- [ ] Проверены логи

## 📞 ПОЛЕЗНЫЕ КОМАНДЫ

```bash
# Быстрая проверка
ps aux | grep python                    # Процессы Python
netstat -tlnp | grep :80               # Открытые порты
systemctl status instagram_bot         # Статус сервиса
df -h                                   # Место на диске
free -m                                 # Память
top                                     # Системная нагрузка

# Очистка логов
sudo journalctl --vacuum-time=7d        # Логи старше 7 дней
find data/logs/ -name "*.log" -mtime +7 -delete  # Логи бота

# Перезапуск полный
sudo systemctl restart instagram_bot
```

## 🎉 ГОТОВО!

Ваш бот теперь работает на VDS 24/7. Используйте скрипты управления для контроля работы.

**Не забудьте:**
- Регулярно проверять логи
- Делать бэкапы
- Обновлять систему
- Мониторить ресурсы 