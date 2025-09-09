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

# Ждем завершения скрапинга
log("Ожидание завершения скрапинга...")
while True:
    status = check_status()
    if status and status.get("status") == "idle":
        log("Скрапинг завершен!")
        break
    elif status and status.get("status") == "running":
        log(f"В процессе: {status.get('job_id', 'unknown')}")
    time.sleep(30)

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

# Проверка общего количества
cur.execute("SELECT COUNT(*) FROM reports WHERE fetched_at >= NOW() - INTERVAL '1 hour'")
total = cur.fetchone()[0]
log(f"Записей за час: {total}")

# Проверка по регионам
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '1 hour' AND r.region_id IS NOT NULL")
regions = cur.fetchone()[0]
log(f"Записей по регионам: {regions}")

# Проверка Москвы
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '1 hour' AND rg.title = 'Москва'")
moscow = cur.fetchone()[0]
log(f"Записей по Москве: {moscow}")

# Проверка качества данных (не generic)
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '1 hour' AND NOT (r.data->'groups'->0->>'title' LIKE 'По всем%')")
specific = cur.fetchone()[0]
log(f"Специфичных записей: {specific}")

cur.close()
conn.close()

log("=== ГОТОВО! Данные проверены ===")
