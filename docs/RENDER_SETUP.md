# 🚀 Настройка Render.com

Инструкция по деплою проекта на Render.com с базой данных на Supabase.

## 1. Настройка Render.com

### Шаг 1: Регистрация на Render.com
1. Откройте [Render.com](https://render.com)
2. Нажмите "Get Started"
3. Зарегистрируйтесь через GitHub
4. Подтвердите почту

### Шаг 2: Создание Web Service
1. Нажмите "New" → "Web Service"
2. Выберите "Build and deploy from a Git repository"
3. Выберите репозиторий с проектом
4. Настройте параметры:
   - **Name:** salary-scraper-api (или другое имя)
   - **Region:** Oregon (US West)
   - **Branch:** main
   - **Runtime:** Docker
   - **Instance Type:** Free ($0/month, 512 MB RAM)
   - **Остальные настройки оставьте по умолчанию**

### Шаг 3: Настройка переменных окружения
В разделе "Environment Variables" добавьте следующие переменные:

```
DATABASE_HOST=aws-0-eu-central-1.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres.cehitgienxwzplcxbfdk
DATABASE_PASSWORD=!!!!QQQQ2222

API_HOST=0.0.0.0
API_PORT=8000
API_URL=https://career.habr.com/api/frontend_v1/salary_calculator/general_graph
API_DELAY_MIN=1.5
API_DELAY_MAX=2.5
API_RETRY_ATTEMPTS=3
```

**📝 Важно:** Используется **Session pooler** Supabase (IPv4 совместимый)

### Шаг 4: Развертывание
1. Нажмите "Create Web Service"
2. Дождитесь завершения развертывания (~5-10 минут)
3. Проверьте работу API по предоставленному URL

## 2. Использование API

После деплоя API будет доступен по URL вида `https://salary-scraper-api.onrender.com`

### Доступные эндпоинты:
- **GET /health** - Проверка состояния API и БД
- **GET /api/status** - Проверка статуса скрапинга
- **POST /api/scrape** - Запуск полного скрапинга
- **POST /api/scrape/upload** - Запуск скрапинга с загрузкой CSV файла
- **GET /docs** - Swagger UI документация API

### Примеры запросов:

```bash
# Проверка статуса
curl https://salary-scraper-api.onrender.com/api/status

# Запуск полного скрапинга (все справочники)
curl -X POST https://salary-scraper-api.onrender.com/api/scrape

# Загрузка CSV конфигурации
curl -X POST https://salary-scraper-api.onrender.com/api/scrape/upload \
  -F "config=@config.csv"
```

## 3. База данных готова

✅ **Таблицы созданы:** specializations, skills, regions, companies, reports, report_log  
✅ **Справочники заполнены:** 39 записей  
✅ **Подключение работает:** через Session pooler (IPv4)  

## 4. Решение проблем

### Проблема: Ошибка подключения к базе данных
**Решение:** Проверьте правильность переменных окружения DATABASE_*.

### Проблема: Приложение "спит"
**Решение:** Free tier на Render.com "усыпляет" приложение через 15 минут неактивности. Первый запрос после "сна" может занять ~30 секунд для "пробуждения".

### Проблема: 503 Service Unavailable в /health
**Решение:** Проверьте логи в Render.com Dashboard. Возможна ошибка подключения к БД или неправильные переменные окружения.

### Проблема: База данных пустая
**Решение:** База уже настроена! Но если что-то пошло не так, можно пересоздать таблицы запустив локально `python scripts/migrate_to_supabase.py` 