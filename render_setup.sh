#!/bin/bash

# Скрипт для инициализации базы данных на Render.com
# Этот скрипт запустится автоматически после деплоя

set -e # Exit on error

# Проверка переменных окружения
echo "Checking environment variables..."
if [ -z "$DATABASE_HOST" ] || [ -z "$DATABASE_USER" ] || [ -z "$DATABASE_PASSWORD" ]; then
  echo "ERROR: Missing database environment variables"
  exit 1
fi

echo "Connecting to database..."
export PGPASSWORD=$DATABASE_PASSWORD

# Создаем таблицы
echo "Creating tables..."
psql -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER -d $DATABASE_NAME -f "sql queries/01_create_tables.sql"

# Вставляем начальные данные
echo "Inserting initial data..."
psql -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER -d $DATABASE_NAME -f "sql queries/03_initial_data.sql"

echo "Setup complete!" 