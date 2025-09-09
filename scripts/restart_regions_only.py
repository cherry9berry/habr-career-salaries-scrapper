#!/usr/bin/env python3
import time
import requests
import psycopg2
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def check_status():
    try:
        response = requests.get("https://habr-career-salaries-scrapper.onrender.com/api/status", timeout=10)
        return response.json()
    except:
        return None

def upload_regions_csv():
    try:
        with open("examples/regions_from_db.csv", "rb") as f:
            files = {"config": f}
            response = requests.post(
                "https://habr-career-salaries-scrapper.onrender.com/api/scrape/upload",
                files=files,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        log(f"Ошибка загрузки CSV: {e}")
        return None

# Проверяем статус - если идёт скрапинг, ждём его завершения
log("Проверка текущего статуса...")
status = check_status()
if status and status.get("status") == "running":
    log(f"Ждём завершения текущего скрапинга: {status.get('job_id')}")
    while True:
        status = check_status()
        if status and status.get("status") == "idle":
            log("Предыдущий скрапинг завершён!")
            break
        time.sleep(15)

# Запускаем скрапинг только по регионам
log("Запуск скрапинга по регионам...")
result = upload_regions_csv()
if not result:
    log("ОШИБКА: Не удалось запустить скрапинг")
    exit(1)

job_id = result.get("job_id")
log(f"Скрапинг регионов запущен: {job_id}")

# Ждём завершения
log("Ожидание завершения...")
while True:
    status = check_status()
    if status and status.get("status") == "idle":
        log("Скрапинг завершён!")
        break
    elif status and status.get("status") == "running":
        log(f"В процессе: {status.get('job_id', 'unknown')}")
    time.sleep(20)

# Проверяем данные
log("Проверка данных в БД...")
conn = psycopg2.connect(
    host="aws-0-eu-central-1.pooler.supabase.com",
    port=5432,
    dbname="postgres",
    user="postgres.cehitgienxwzplcxbfdk",
    password="!!!!QQQQ2222"
)

cur = conn.cursor()

# Проверка записей за последние 30 минут
cur.execute("SELECT COUNT(*) FROM reports WHERE fetched_at >= NOW() - INTERVAL '30 minutes'")
total = cur.fetchone()[0]
log(f"Записей за 30 мин: {total}")

# Проверка по регионам
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '30 minutes' AND r.region_id IS NOT NULL")
regions = cur.fetchone()[0]
log(f"Записей по регионам: {regions}")

# Проверка Москвы
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '30 minutes' AND rg.title = 'Москва'")
moscow = cur.fetchone()[0]
log(f"Записей по Москве: {moscow}")

# Проверка специфичности (не generic)
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '30 minutes' AND NOT (r.data->'groups'->0->>'title' LIKE 'По всем%')")
specific = cur.fetchone()[0]
log(f"Специфичных записей: {specific}")

cur.close()
conn.close()

log("=== ГОТОВО! Данные проверены ===")
