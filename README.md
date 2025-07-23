# Salary Scraper

Скрапер данных о зарплатах с Habr Career API.

## Структура проекта

```
salary_scrapping/
├── src/                    # Основные модули
│   ├── __init__.py
│   ├── core.py            # Базовые интерфейсы и классы
│   ├── database.py        # Работа с PostgreSQL (паттерн Repository)
│   ├── scraper.py         # API клиент и логика скрапинга
│   └── config_parser.py   # Парсеры конфигурации
├── tests/                 # Тесты
│   ├── __init__.py
│   ├── unit/             # Модульные тесты
│   │   ├── __init__.py
│   │   ├── test_core.py
│   │   ├── test_config_parser.py
│   │   ├── test_database.py
│   │   ├── test_scraper.py
│   │   └── test_error_coverage.py
│   └── integration/      # Интеграционные тесты
│       ├── __init__.py
│       └── test_integration.py
├── scripts/               # Вспомогательные скрипты
│   ├── update_references.py  # Обновление справочников
│   └── clean_db.py           # Очистка БД
├── examples/              # Примеры
│   └── example_config.csv    # Пример CSV конфигурации
├── sql queries/           # SQL запросы для отчетов
├── main.py               # Точка входа
├── run_tests.py          # Запуск тестов
├── pytest.ini            # Конфигурация pytest
├── config.json           # Конфигурация приложения
├── requirements.txt      # Зависимости Python
├── .gitignore           # Игнорируемые файлы
└── README.md            # Документация
```

## Архитектура

Проект построен по принципам SOLID

## Установка

```bash
pip install -r requirements.txt
```

## Использование

### 1. Без параметров - выгрузка по всем справочникам индивидуально:

```bash
python main.py
```

Выгрузит данные по каждому типу справочника отдельно:
- specializations (специализации)
- skills (навыки)
- regions (регионы)
- companies (компании)

### 2. С CSV конфигурацией:

```bash
python main.py config.csv
```

CSV файл должен содержать заголовки из списка: `specializations`, `skills`, `regions`, `companies`

Пример CSV:
```csv
skills,regions
```

Это создаст выгрузки для комбинаций навыков и регионов.

## База данных

Структура таблиц:
- `specializations`, `skills`, `regions`, `companies` - справочники
- `reports` - результаты выгрузок
- `report_log` - логи операций

## Конфигурация

Файл `config.json` содержит:
- Параметры подключения к БД
- URL API и параметры запросов
- Таймауты и количество попыток

## Обновление справочников

Для обновления справочников из Excel файлов используйте:

```bash
python scripts/update_references.py skills skills.xlsx
```

Excel файл должен содержать колонки `title` и `alias`.

## Тестирование

### Запуск тестов

```bash
# Все тесты
python run_tests.py

# Только unit тесты
python run_tests.py --type unit

# Только интеграционные тесты  
python run_tests.py --type integration

# С помощью pytest
pytest

# С покрытием кода
pytest --cov=src --cov-report=html
```

### Структура тестов

- `tests/unit/` - модульные тесты для каждого компонента
- `tests/integration/` - интеграционные тесты всего workflow

### Покрытие кода

Минимальное требуемое покрытие: 80%

## Принципы работы

1. Данные сохраняются в транзакции
2. Коммит происходит только при успехе >60% запросов
3. При ошибках - автоматический откат
4. Вывод только в терминал, без файловых логов 