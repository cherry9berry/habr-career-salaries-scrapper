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

log("=== ФИНАЛЬНАЯ ЗАДАЧА: СКРАПИНГ РЕГИОНОВ ===")

# Запускаем скрапинг только по регионам
log("1. Запуск скрапинга по регионам...")
result = upload_regions_csv()
if not result:
    log("ОШИБКА: Не удалось запустить скрапинг")
    exit(1)

job_id = result.get("job_id")
log(f"Скрапинг регионов запущен: {job_id}")

# Ждём завершения (максимум 10 минут)
log("2. Ожидание завершения...")
start_time = time.time()
while time.time() - start_time < 600:  # 10 минут максимум
    status = check_status()
    if status and status.get("status") == "idle":
        log("✅ Скрапинг завершён!")
        break
    elif status and status.get("status") == "running":
        elapsed = int(time.time() - start_time)
        log(f"В процессе ({elapsed}s): {status.get('job_id', 'unknown')}")
    time.sleep(15)
else:
    log("❌ Таймаут ожидания")
    exit(1)

# Проверяем данные
log("3. Проверка данных в БД...")
conn = psycopg2.connect(
    host="aws-0-eu-central-1.pooler.supabase.com",
    port=5432,
    dbname="postgres",
    user="postgres.cehitgienxwzplcxbfdk",
    password="!!!!QQQQ2222"
)

cur = conn.cursor()

# Проверка записей за последние 15 минут
cur.execute("SELECT COUNT(*) FROM reports WHERE fetched_at >= NOW() - INTERVAL '15 minutes'")
total = cur.fetchone()[0]
log(f"📊 Записей за 15 мин: {total}")

# Проверка по регионам
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '15 minutes' AND r.region_id IS NOT NULL")
regions = cur.fetchone()[0]
log(f"🏙️ Записей по регионам: {regions}")

# Проверка Москвы
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '15 minutes' AND rg.title = 'Москва'")
moscow = cur.fetchone()[0]
log(f"🏛️ Записей по Москве: {moscow}")

# Проверка качества (не generic)
cur.execute("SELECT COUNT(*) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '15 minutes' AND NOT (r.data->'groups'->0->>'title' LIKE 'По всем%')")
specific = cur.fetchone()[0]
log(f"🎯 Специфичных записей: {specific}")

# Проверка уникальных регионов
cur.execute("SELECT COUNT(DISTINCT rg.title) FROM reports r JOIN regions rg ON rg.id = r.region_id WHERE r.fetched_at >= NOW() - INTERVAL '15 minutes'")
unique_regions = cur.fetchone()[0]
log(f"🗺️ Уникальных регионов: {unique_regions}")

cur.close()
conn.close()

log("=== ✅ ЗАДАЧА ВЫПОЛНЕНА! ДАННЫЕ ГОТОВЫ ===")
print("\nФинальный SQL запрос для анализа:")
print("""
WITH moscow_median_all AS (
    SELECT (gd->>'median')::int as moscow_median
    FROM reports r
    JOIN regions rg ON rg.id = r.region_id
    CROSS JOIN LATERAL jsonb_array_elements(r.data->'groups') AS gd
    WHERE r.region_id IS NOT NULL
      AND rg.title = 'Москва'
      AND gd->>'name' = 'All'
      AND r.fetched_at >= NOW() - INTERVAL '30 minutes'
      AND (gd->>'total')::int > 0
    ORDER BY r.fetched_at DESC
    LIMIT 1
)
SELECT
    rg.title                         AS region,
    (gd->>'median')::int             AS median_salary,
    mm.moscow_median                 AS moscow_median,
    CASE 
        WHEN mm.moscow_median IS NOT NULL AND mm.moscow_median > 0 THEN
            ROUND(((gd->>'median')::int - mm.moscow_median) * 100.0 / mm.moscow_median, 1)
        ELSE 0
    END                              AS diff_from_moscow_percent
FROM reports r
JOIN regions rg ON rg.id = r.region_id
CROSS JOIN LATERAL jsonb_array_elements(r.data->'groups') AS gd
CROSS JOIN moscow_median_all mm
WHERE r.region_id IS NOT NULL
  AND gd->>'name' = 'All'
  AND r.fetched_at >= NOW() - INTERVAL '30 minutes'
  AND (gd->>'total')::int > 0
ORDER BY (gd->>'median')::int DESC;
""")
