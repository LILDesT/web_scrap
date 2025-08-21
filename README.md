# 🕷️ **Web Scraper Service**

Асинхронный веб-скрапер для парсинга новостей с защитой от ботов и ограничением доменов.

**Запуск скрапера**
```bash
docker-compose up -d --build
```

**Готово!** Сервис доступен на http://localhost:8000

## 🧪 **Тест**
```bash
# Создать задачу
curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"url":"https://24.kz/kz"}'

# Проверить результат (замените TASK_ID)
curl http://localhost:8000/tasks/TASK_ID

# Статистика доменов
curl http://localhost:8000/stats/domain-limiter

### PowerShell
```powershell
# Создать задачу
$response = Invoke-RestMethod -Uri "http://localhost:8000/tasks" -Method Post -Body '{"url":"https://24.kz/kz"}' -Headers @{"Content-Type"="application/json"}

# Проверить результат
Start-Sleep 5
Invoke-RestMethod -Uri "http://localhost:8000/tasks/$($response.task_id)"
```

## 📊 **Мониторинг**
- **API Docs**: http://localhost:8000/docs
- **Flower**: http://localhost:5555  
- **Logs**: `docker-compose logs -f`

## ⚙️ **Настройки** (docker-compose.yml)
- `MAX_CONCURRENT_REQUESTS_PER_DOMAIN=3` - Лимит запросов к домену
- `REQUEST_DELAY=2.0` - Задержка между запросами  
- `MAX_RETRIES=3` - Количество повторов

## 🧪 **Автотестирование**
```bash
python test_service.py
```
Тестирует все функции и сохраняет результаты в JSON файл.

## 🛑 **Остановка**
```bash
docker-compose down
```

---
**✅ Готов к продакшену: Celery + Redis + Docker + защита от ботов**