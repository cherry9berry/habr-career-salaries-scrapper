# Salary-Scraper – полное руководство

Async-скрапер зарплат с Habr Career, построенный по SOLID-принципам, покрытый тестами >95 %, готовый к CI/CD и контейнеризации.

---

## 1. Структура проекта
```text
salary_scrapping/
├── src/                  # основной пакет
│   ├── __init__.py
│   ├── core.py           # DTO + интерфейсы IRepository / IApiClient / IScraper
│   ├── database.py       # PostgresRepository (pool + batch-insert)
│   ├── scraper.py        # синхронный скрапер
│   ├── async_api.py      # aiohttp-клиент
│   ├── async_scraper.py  # асинхронный скрапер (Semaphore)
│   ├── config_parser.py  # CSV-парсер конфигов
│   ├── settings.py       # Pydantic Settings + .env/YAML
│   └── cli.py            # Typer-CLI (scrape / update / clean)
├── scripts/              # вспомогательные утилиты
│   ├── update_references.py
│   └── clean_db.py
├── tests/                # 69 тестов: unit, async, integration, error-coverage
├── Dockerfile            # образ приложения
├── docker-compose.yml    # Postgres + app
├── config.yaml           # конфигурация (заменяет прежний JSON)
├── pyproject.toml        # Poetry + Black/Ruff/Mypy
├── requirements.txt      # fallback-зависимости для pip install -r
├── run_tests.py          # универсальный запуск тестов
├── README.md             # краткая дока
└── .github/workflows/ci.yml  # GitHub Actions (lint + tests + coverage)
```

## 2. Быстрый старт
### 2.1. Poetry (рекомендуется)
```bash
# установка poetry, если нужно
pip install --upgrade pip
pip install poetry

# установка зависимостей
poetry install

# запуск CLI (scrape sync)
poetry run salary-scraper scrape
# или асинхронно
poetry run salary-scraper scrape --async
```

### 2.2. pip
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.cli scrape
```

### 2.3. Docker / compose
```bash
docker-compose build          # собираем образ
docker-compose up             # старт Postgres + скрапера
# Postgres доступен на localhost:5432
```

## 3. Конфигурация: `config.yaml`
```yaml
database:
  host: localhost
  port: 5432
  database: scraping_db
  user: scraper
  password: "password"
api:
  url: https://career.habr.com/api/frontend_v1/salary_calculator/general_graph
  delay_min: 1.5
  delay_max: 2.5
  retry_attempts: 3
max_references: 2000
```
Переменные можно переопределить через `.env`. Файл валидируется Pydantic-моделью `Settings`.

## 4. CLI команды
| Команда | Действие |
|---------|----------|
| `salary-scraper scrape` | Сбор данных (синхронно) |
| `salary-scraper scrape --async` | Сбор данных асинхронно |
| `salary-scraper update TABLE FILE.xlsx` | Обновить справочник (`skills`, `regions`, …) |
| `salary-scraper clean` | Удалить `test_table` из БД |

## 5. Устройство кода
### 5.1. `core.py`
Value-объекты `Reference`, `SalaryData`, `ScrapingConfig` и интерфейсы.

### 5.2. `database.py`
Пул соединений `SimpleConnectionPool`, batch-insert через `execute_values`, транзакция коммитится при успехе >60 %.

### 5.3. Асинхронный режим
`async_api.py` (aiohttp) и `async_scraper.py` (Semaphore + gather).

### 5.4. `settings.py`
```python
settings = Settings.load("config.yaml")
repo = PostgresRepository(settings.database.model_dump())
```

## 6. Тестирование
```bash
python run_tests.py            # все тесты
python run_tests.py --type unit # только unit
pytest --cov=src               # pytest с покрытием
```
Покрытие: **96 %**.

## 7. Линтинг и типы
```bash
ruff src tests
black --check .
mypy src
```
Все проверки выполняются в CI.

## 8. CI/CD
GitHub Actions workflow: lint → tests + coverage → Codecov.

## 9. Dockerfile
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 10. Compose
```yaml
version: "3.9"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: scraping_db
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: password
    ports: ["5432:5432"]
  app:
    build: .
    depends_on: [db]
    environment:
      - DATABASE_HOST=db
    command: ["python", "main.py"]
```

## 11. Вклад
Форк → ветка → PR. Прогоняйте `poetry run ruff . && poetry run pytest` перед коммитом.

## 12. Лицензия
MIT (см. `LICENSE`).

## 13. Production-hardening checklist

Минимально рабочий контейнер уже собирается, но для продакшена обычно добавляют:

| Блок | Что сделать | Пример |
|------|-------------|--------|
| Secrets | Хранить пароль/URL БД в переменных окружения или секретах orchestrator | `POSTGRES_PASSWORD=${DB_PASS}` в compose + `env_file` |
| Logging | Выводить логи в stdout/stderr, настроить ротацию (Docker, Loki, ELK) | заменить `print` на `rich.logging` или `structlog` |
| Healthcheck | Добавить `HEALTHCHECK CMD curl -f http://localhost/health || exit 1` в Dockerfile/compose | эндпоинт `/health` (FastAPI) или psql-ping |
| Resources | Установить `mem_limit`, `cpus`, restart-policy | `deploy.resources.limits:` в Swarm / K8s requests/limits |
| DB migrations | Использовать Alembic; хранить версии миграций в `migrations/` и запускать `alembic upgrade head` при старте | отдельная Init-Job или Entrypoint |
| Observability | Экспорт Prometheus-метрик (время запроса, ошибки, скорость вставки) + Grafana дашборды | библиотека `prometheus-client` |
| Security | Скэн Docker-образа (Trivy), обновлять зависимости, non-root user | `USER scraper` в Dockerfile |

Примеры переменных окружения для compose:

```env
# .env
POSTGRES_DB=scraping_db
POSTGRES_USER=scraper
POSTGRES_PASSWORD=supersecret
API_URL=https://career.habr.com/api/frontend_v1/salary_calculator/general_graph
```

В `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:15
    env_file: .env
  app:
    build: .
    env_file: .env
    environment:
      - DATABASE_HOST=db
    healthcheck:
      test: ["CMD", "python", "-c", "import psycopg2,os,sys;\nimport time;\ntry:\n psycopg2.connect(host='db', dbname=os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD')).close();\n sys.exit(0)\nexcept Exception as e:\n sys.exit(1)"]
      interval: 30s
      retries: 3
```

Следуя чек-листу, контейнер можно без боли раскатить в Kubernetes / Swarm / ECS. 