# 🚀 Быстрый старт

Простое руководство для запуска проекта локально и понимания как он работает.

## 🎯 Что делает этот проект

Этот проект автоматически собирает данные о зарплатах с сайта **Habr Career** и сохраняет их в базу данных PostgreSQL для дальнейшего анализа.

### 📊 Какие данные собираются

- **Специализации** (Backend, Frontend, DevOps, и т.д.)
- **Навыки** (Python, JavaScript, Docker, и т.д.)
- **Регионы** (Москва, СПб, Екатеринбург, и т.д.)
- **Компании** (Яндекс, VK, Сбер, и т.д.)
- **Зарплатные вилки** для каждой комбинации

## 🛠️ Быстрая установка

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/your-username/salary_scrapping.git
cd salary_scrapping
```

### 2. Установите зависимости
```bash
pip install -r requirements.txt
```

### 3. Настройте базу данных
Создайте PostgreSQL базу и обновите `config.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  database: scraping_db
  user: scraper
  password: your_password

api:
  url: "https://career.habr.com/api/frontend_v1/salary_calculator/general_graph"
  delay_min: 1.5
  delay_max: 2.5
  retry_attempts: 3

max_references: 2000
```

### 4. Создайте таблицы
Выполните SQL скрипты из папки `sql queries/` в вашей базе данных.

### 5. Запустите скрапер
```bash
# Собрать данные по всем справочникам
python main.py

# Собрать данные по конкретной конфигурации
python main.py examples/example_config.csv
```

## 📁 Структура проекта (упрощенно)

```
salary_scrapping/
├── main.py              # 👈 Запускаете отсюда
├── config.yaml          # 👈 Настройки БД и API
├── src/                 # Код приложения
│   ├── scraper.py       # Сбор данных с API
│   ├── database.py      # Работа с PostgreSQL
│   └── config_parser.py # Чтение конфигураций
├── tests/               # Автотесты (71 штука)
├── docs/                # Документация
└── sql queries/         # SQL скрипты для отчетов
```

## 🚀 Основные команды

### Запуск скрапинга
```bash
# Все справочники (специализации, навыки, регионы, компании)
python main.py

# Только определенные комбинации (из CSV файла)
python main.py examples/example_config.csv
```

### Тестирование
```bash
# Запустить все тесты
python -m pytest tests/

# Тесты с покрытием кода
python -m pytest tests/ --cov=src --cov-report=html

# Посмотреть отчет покрытия
# Откройте htmlcov/index.html в браузере
```

### Проверка качества кода
```bash
# Линтер (проверка ошибок)
python -m ruff check src tests

# Форматирование кода
python -m black .

# Проверка типов
python -m mypy src --ignore-missing-imports
```

## 📝 Как создать свою конфигурацию

Создайте CSV файл с заголовками из списка: `specializations`, `skills`, `regions`, `companies`

**Пример `my_config.csv`:**
```csv
skills,regions
Python,Moscow
JavaScript,SPB
Go,Ekaterinburg
```

Это создаст выгрузки для каждой комбинации навык+регион.

**Запуск:**
```bash
python main.py my_config.csv
```

## 🗄️ Работа с базой данных

### Основные таблицы
- `specializations` - справочник специализаций
- `skills` - справочник навыков  
- `regions` - справочник регионов
- `companies` - справочник компаний
- `reports` - результаты скрапинга (зарплатные данные)
- `report_log` - логи операций

### Примеры SQL запросов
```sql
-- Последние зарплаты по Python в Москве
SELECT * FROM reports 
WHERE skills_1 IS NOT NULL 
AND region_id IS NOT NULL
ORDER BY fetched_at DESC 
LIMIT 10;

-- Статистика по скрапингу
SELECT COUNT(*), DATE(created_at) 
FROM report_log 
GROUP BY DATE(created_at);
```

## 🔧 Обновление справочников

Если нужно обновить справочные данные (навыки, регионы и т.д.) из Excel файлов:

```bash
python scripts/update_references.py skills skills.xlsx
python scripts/update_references.py regions regions.xlsx
```

Excel файл должен содержать колонки `title` и `alias`.

## 🐛 Что делать если что-то не работает

### 1. Ошибка подключения к БД
```
psycopg2.OperationalError: connection failed
```
**Решение:** Проверьте настройки в `config.yaml` и убедитесь что PostgreSQL запущен.

### 2. Ошибка API
```
requests.exceptions.HTTPError: 429 Too Many Requests
```
**Решение:** Увеличьте `delay_min` и `delay_max` в `config.yaml`.

### 3. Тесты падают
```
FAILED tests/unit/test_database.py
```
**Решение:** Установите все зависимости: `pip install -r requirements.txt`

### 4. Нет данных в БД
**Решение:** Проверьте что создали все таблицы из `sql queries/`.

## 📚 Дополнительная документация

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Подробный гайд по развертыванию в продакшне
- **[README.md](../README.md)** - Полное описание архитектуры и CI/CD
- **SQL запросы** - готовые отчеты в папке `sql queries/`

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/my-feature`
3. Внесите изменения и добавьте тесты
4. Запустите проверки: `pytest`, `ruff check`, `black --check`
5. Создайте Pull Request

---

**🎉 Готово!** Теперь у вас есть работающий скрапер зарплатных данных с автоматическими тестами и CI/CD! 