 **Web Scraper Service**

Асинхронный веб-скрапер для парсинга новостей с защитой от ботов и ограничением доменов.

**Запуск скрапера**
```bash
docker-compose up -d --build
```

Сервис будет доступен на http://localhost:8000

 **Тест**
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

**Мониторинг**
- **API Docs**: http://localhost:8000/docs
- **Flower**: http://localhost:5555  
- **Logs**: `docker-compose logs -f`

**Настройки** (docker-compose.yml)
- `MAX_CONCURRENT_REQUESTS_PER_DOMAIN=3` - Лимит запросов к домену
- `REQUEST_DELAY=2.0` - Задержка между запросами  
- `MAX_RETRIES=3` - Количество повторов

**Автотестирование**
```bash
python test_service.py
```
Тестирует все функции и сохраняет результаты в JSON файл.

**Остановка**
```bash
docker-compose down
```
## **Пример запроса**
```bash
$ curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"url":"https://24.kz/kz"}'
Ответ:
{"task_id":"b29b2ac7-9c86-4786-b9a8-95d2a2512269"}
```
```bash
curl http://localhost:8000/tasks/b29b2ac7-9c86-4786-b9a8-95d2a2512269
Ответ:
{"status":"SUCCESS","data":[{"entity_title":"Қасым-Жомарт Тоқаев Қырғыз Республикасына ресми сапармен барды","entry_meta_date":"Дата 
не найдена","url":"https://24.kz/kz/zha-aly-tar/basty-zha-aly-tar/725704-kasym-zomart-tokaev-kyrgyz-respublikasyna-resmi-saparmen-bardy"},{"entity_title":"Елордаға жеткізілген балалардың жағдайы ауыр","entry_meta_date":"Бүгін 11:11","url":"https://24.kz/kz/zha-aly-tar/o-i-a/725641-elordaga-zhetkizilgen-balalardyn-zhagdajy-auyr"},{"entity_title":"Қазақстанда жұмыссыздар саны қысқарды","entry_meta_date":"Бүгін 09:37","url":"https://24.kz/kz/zha-aly-tar/ekonomika/725625-kazakstanda-zhumyssyzdar-sany-kyskardy"},{"entity_title":"Чемпиондар лигасы: «Қайрат» пен «Селтик» тең түсті","entry_meta_date":"Бүгін 09:25","url":"https://24.kz/kz/zha-aly-tar/sport/725621-cempiondar-ligasy-kajrat-pen-seltik-ten-tusti"}........
```
```bash
curl http://localhost:8000/stats/domain-limiter
Ответ:
{"domain_stats":{},"config":{"max_concurrent_per_domain":3}}
```
