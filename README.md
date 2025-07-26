# 🔥 Habr Career Salary Scraper

Парсер зарплатных данных с сайта Habr Career с автоматическим CI/CD пайплайном и REST API.

## 🏗️ Архитектура проекта

### 📁 Структура папок
```
salary_scrapping/
├── src/                    # Основной код приложения
│   ├── api/               # REST API (FastAPI)
│   │   ├── __init__.py
│   │   └── app.py         # API endpoints и логика
│   ├── core.py            # Интерфейсы и базовые классы (SOLID принципы)
│   ├── database.py        # Работа с PostgreSQL + временные таблицы
│   ├── scraper.py         # HTTP клиент для API Habr + логика скрапинга
│   ├── async_*.py         # Асинхронные версии для параллельного скрапинга
│   ├── config_parser.py   # Парсинг CSV конфигураций
│   └── settings.py        # Загрузка настроек из YAML
├── tests/                 # Тесты (71 штука, покрытие 68%)
│   ├── unit/             # Юнит-тесты каждого модуля
│   └── integration/      # Интеграционные тесты
├── .github/workflows/    # CI/CD пайплайны
├── docs/                 # Документация
├── scripts/              # Вспомогательные скрипты
├── sql queries/          # SQL запросы для отчетов
├── examples/             # Примеры конфигураций
├── main.py               # CLI версия (для локального использования)
├── run_api.py            # Запуск API сервера
└── config.yaml           # Конфигурация БД и API
```

### 🎯 Принципы архитектуры
- **SOLID принципы** - каждый класс имеет одну ответственность
- **Dependency Injection** - зависимости передаются через конструкторы
- **Repository Pattern** - слой абстракции для работы с БД
- **Interface Segregation** - интерфейсы для каждого компонента
- **Временные таблицы** - данные не в RAM, а в PostgreSQL temporary tables

## 💾 Новая система хранения данных

### **Раньше: Хранение в RAM**
❌ Данные терялись при краше  
❌ Ограничения по памяти  
❌ Сложно отслеживать прогресс  

### **Сейчас: PostgreSQL временные таблицы**
✅ **Надежность** - данные в БД, не теряются при краше  
✅ **Масштабируемость** - нет ограничений по RAM  
✅ **Атомарность** - либо все данные, либо ничего  
✅ **Отмена** - просто DROP TABLE  

```sql
-- Временная таблица создается для каждого скрапинга
CREATE TEMPORARY TABLE temp_scraping_uuid123 (
    id SERIAL PRIMARY KEY,
    specialization_id INTEGER,
    skills_1 INTEGER,
    region_id INTEGER,
    company_id INTEGER,  
    data JSONB NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- При успешном завершении данные переносятся в основную таблицу
INSERT INTO reports SELECT * FROM temp_scraping_uuid123;
DROP TABLE temp_scraping_uuid123;
```

## 🚀 REST API

### 📡 Доступные эндпоинты:

```bash
# Проверка здоровья API
GET /health
→ {"status": "healthy", "database": "connected"}

# Статус скрапинга
GET /api/status  
→ {"status": "idle|running", "job_id": "uuid"}

# Запуск полного скрапинга (все справочники)
POST /api/scrape
→ {"status": "started", "job_id": "uuid123"}

# Запуск с загрузкой CSV файла
POST /api/scrape/upload
Content-Type: multipart/form-data
Form: config=@config.csv
→ {"status": "started", "job_id": "uuid456"}

# Автогенерируемая документация
GET /docs - Swagger UI
GET /redoc - ReDoc документация
```

### 🔒 Защита от параллельного запуска

API автоматически блокирует повторные запуски:
```bash
# Если скрапинг уже идет
POST /api/scrape
→ HTTP 409: {"detail": "Scraping already in progress"}
```

### 🎮 Примеры использования:

```bash
# Запуск полного скрапинга
curl -X POST http://localhost:8000/api/scrape

# Загрузка конфигурации из файла
curl -X POST http://localhost:8000/api/scrape/upload \
  -F "config=@examples/example_config.csv"

# Проверка статуса
curl http://localhost:8000/api/status
```

## 🚀 CI/CD Пайплайн (GitHub Actions)

### 🔄 Что происходит при `git push`

```mermaid
graph TD
    A[git push] --> B[GitHub получает код]
    B --> C[Запускается CI workflow]
    C --> D[Устанавливает Python 3.9]
    C --> E[Устанавливает зависимости]
    C --> F[Запускает линтеры]
    C --> G[Запускает тесты]
    
    F --> F1[ruff check - проверка кода]
    F --> F2[black --check - форматирование]
    F --> F3[mypy - проверка типов]
    
    G --> G1[pytest - запуск 71 теста]
    G --> G2[coverage - проверка покрытия >68%]
    
    F1 --> H{Все проверки OK?}
    F2 --> H
    F3 --> H
    G1 --> H
    G2 --> H
    
    H -->|✅ Да| I[✅ CI успешен - готов к деплою]
    H -->|❌ Нет| J[❌ CI провален - исправь код]
```

### 📋 Файл `.github/workflows/ci.yml`
```yaml
# Автоматически запускается при push в main или PR
# Проверяет качество кода и запускает тесты
# Генерирует отчет покрытия кода
```

## 🌐 Деплой на Render.com + Supabase ✅

### 📊 Текущий статус данных:
**Все справочные данные уже перенесены в Supabase:**
- ✅ **specializations**: 165 записей
- ✅ **skills**: 1,572 уникальных записи  
- ✅ **regions**: 93 записи
- ✅ **companies**: 467 записей

**Временное хранение во время скрапинга:** SQLite файлы (по умолчанию)

### 🤔 Что такое "засыпание" и "холодный старт"?

**🛌 Засыпание через 15 минут:**
- Если к вашему приложению 15 минут никто не обращается - Render его "усыпляет"
- Это экономит ресурсы на бесплатном плане
- Приложение не работает, пока кто-то не сделает запрос

**🥶 Холодный старт ~30 секунд:**
- Когда приходит запрос к "спящему" приложению - оно "просыпается"
- Первый запрос будет ждать ~30 секунд пока приложение загрузится
- Последующие запросы работают быстро

**🎯 Как это влияет на наш проект:**
- ✅ **Не критично** - скрапинг запускается редко (раз в день/неделю)  
- ✅ **30 секунд ожидания** - нормально для фонового процесса
- ✅ **API остается доступным** - просто первый запрос медленный

### 🗄️ Бесплатные базы данных 24/7

**Render PostgreSQL** = 90 дней бесплатно → не подходит

**🆓 Supabase (выбранное решение):**
- ✅ **PostgreSQL** (совместимо с нашим кодом)
- ✅ **Бесплатно навсегда** - никаких подтверждений по почте
- ✅ 500MB хранилища
- ✅ 2 CPU hours в день (достаточно для скрапинга)
- ✅ Засыпает только при полном отсутствии активности >1 месяца
- ✅ REST API из коробки (для аналитики)
- ✅ Веб-интерфейс для управления данными

## 🛠️ Развертывание (теория)

### 🏃‍♂️ Пошаговый план:

1. **Регистрируемся на Supabase** - бесплатная PostgreSQL база
2. **Создаем проект на Render.com** - бесплатный хостинг API
3. **Настраиваем переменные окружения:**
   ```env
   DATABASE_URL=postgresql://user:pass@supabase.com:5432/postgres
   API_DELAY_MIN=1.5
   API_DELAY_MAX=2.5
   ```
4. **Render автоматически:**
   - Клонирует код из GitHub
   - Устанавливает зависимости: `pip install -r requirements.txt`
   - Запускает API: `python run_api.py`
5. **GitHub Actions при успешном CI:**
   - Автоматически триггерит новый деплой
   - Render подтягивает новый код
   - Перезапускает приложение

### 🌊 Workflow пользователя:

```
1. Разработчик → git push
2. GitHub Actions → проверяет код  
3. Render.com → деплоит новую версию API
4. Пользователь → POST /api/scrape/upload + CSV файл
5. API → создает временный SQLite файл для скрапинга  
6. Скрапер → собирает данные в SQLite
7. При успехе → переносит данные в основную таблицу
8. Пользователь → анализирует данные через pgAdmin/Grafana
```

## 🧪 Запуск локально

### CLI версия (как раньше):
```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить config.yaml
database:
  host: localhost
  database: scraping_db
  # ...

# 3. Запустить скрапинг
python main.py                    # Все справочники
python main.py config.csv         # Кастомная конфигурация
```

### API версия (новая):
```bash
# 1. Установить зависимости (включая FastAPI)
pip install -r requirements.txt

# 2. Запустить API сервер
python run_api.py
# или
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# 3. Открыть документацию
# http://localhost:8000/docs

# 4. Использовать API
curl -X POST http://localhost:8000/api/scrape
```

### Docker (полный стек):
```bash
# Запуск PostgreSQL + API
docker-compose up

# API доступен на http://localhost:8000
# PostgreSQL на localhost:5432
```

## 📊 Мониторинг и отладка

- **Логи на Render:** доступны в веб-интерфейсе
- **Тесты:** автоматически в CI, локально `pytest`
- **Покрытие кода:** `htmlcov/index.html` после `pytest --cov`
- **Линтеры:** `ruff check src`, `black --check .`, `mypy src`
- **API документация:** `/docs` и `/redoc` эндпоинты
- **Здоровье системы:** `/health` эндпоинт

---

**🎯 Итог:** Проект готов к автоматическому деплою с REST API управлением и надежным хранением данных!