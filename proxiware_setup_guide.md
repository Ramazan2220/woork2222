# 🎯 РУКОВОДСТВО ПО АКТИВАЦИИ PROXIWARE ПРОКСИ

## ✅ **ХОРОШИЕ НОВОСТИ:**

Ваш прокси **ПОЛНОСТЬЮ СОВМЕСТИМ** с системой! 🎉

```
✅ Формат правильный: proxy.proxiware.com:1337:user-default-network-mbl-pool-1-country-uk:L9p2WjtFRipG
✅ Тип: Мобильный ротационный (mbl)
✅ Страна: UK
✅ Система поддерживает: ДА!
```

## ❌ **ТЕКУЩАЯ ПРОБЛЕМА:**

Прокси **неактивен** - ошибка `503 Service Unavailable`

## 🔧 **ПОШАГОВОЕ РЕШЕНИЕ:**

### **ШАГ 1: Войдите в панель Proxiware**
1. Откройте: https://dashboard.proxiware.com
2. Войдите с вашими учетными данными
3. Перейдите в раздел "Proxies" или "Dashboard"

### **ШАГ 2: Проверьте статус подписки**
- ✅ Убедитесь, что подписка активна
- 💳 Проверьте баланс/лимиты трафика
- 📅 Проверьте дату окончания

### **ШАГ 3: Добавьте ваш IP в Whitelist**
**Ваш текущий IP: `45.128.38.170`**

1. Найдите раздел "IP Whitelist" или "Authorized IPs"
2. Добавьте IP: `45.128.38.170`
3. Сохраните изменения
4. **Подождите 5-10 минут для активации**

### **ШАГ 4: Активируйте прокси**
1. Найдите ваш мобильный план/пакет
2. Убедитесь, что статус: "Active" или "Running"
3. Если статус "Stopped" - запустите прокси

### **ШАГ 5: Проверка**
После активации проверьте командой:
```bash
curl --proxy http://user-default-network-mbl-pool-1-country-uk:L9p2WjtFRipG@proxy.proxiware.com:1337 ipinfo.io/ip
```

## 💡 **АЛЬТЕРНАТИВНЫЕ ВАРИАНТЫ:**

Если основной прокси не работает, попробуйте:

### **Пул 2:**
```
proxy.proxiware.com:1337:user-default-network-mbl-pool-2-country-uk:L9p2WjtFRipG
```

### **США вместо UK:**
```
proxy.proxiware.com:1337:user-default-network-mbl-pool-1-country-us:L9p2WjtFRipG
```

### **Residential вместо Mobile:**
```
proxy.proxiware.com:1337:user-default-network-residential-pool-1-country-uk:L9p2WjtFRipG
```

## 🤖 **ИНТЕГРАЦИЯ С INSTAGRAM БОТОМ:**

После активации используйте этот код:

```python
# Настройки для вашего Proxiware прокси
PROXIWARE_CONFIG = {
    'host': 'proxy.proxiware.com',
    'port': 1337,
    'username': 'user-default-network-mbl-pool-1-country-uk',
    'password': 'L9p2WjtFRipG',
    'url': 'http://user-default-network-mbl-pool-1-country-uk:L9p2WjtFRipG@proxy.proxiware.com:1337'
}

# Использование с instagrapi
from instagrapi import Client

client = Client()
client.set_proxy(PROXIWARE_CONFIG['url'])
```

## 📞 **ПОДДЕРЖКА PROXIWARE:**

Если проблемы остаются:
- 📧 **Email**: support@proxiware.com
- 💬 **Telegram**: @proxiware_support  
- 🌐 **Документация**: docs.proxiware.com
- 💬 **Live Chat**: на сайте proxiware.com

## 🎯 **ОПТИМАЛЬНЫЕ НАСТРОЙКИ ДЛЯ INSTAGRAM:**

```python
INSTAGRAM_SETTINGS = {
    'sticky_session_duration': 1800,  # 30 минут
    'rotation_check_interval': 300,   # 5 минут
    'pause_between_requests': 5,      # 5 секунд
    'max_requests_per_session': 500,
    'user_agent': 'Instagram Mobile App'
}
```

## ✅ **ПОСЛЕ АКТИВАЦИИ:**

1. **Протестируйте прокси** нашим скриптом
2. **Обновите базу данных** с правильными настройками  
3. **Настройте ротацию** для оптимальной работы
4. **Мониторьте использование** трафика

---

**🎉 Главное: Ваш прокси ОТЛИЧНЫЙ выбор для Instagram! Мобильный UK IP с ротацией - это именно то, что нужно для безопасной автоматизации!** 