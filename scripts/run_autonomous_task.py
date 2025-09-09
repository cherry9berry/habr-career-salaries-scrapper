#!/usr/bin/env python3
"""
Автономное выполнение задачи: запуск скрапинга по регионам и проверка данных
"""

import os
import sys
import time
import requests
import psycopg2
from datetime import datetime, timedelta


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def check_api_status():
    """Проверить статус API"""
    try:
        response = requests.get("https://habr-career-salaries-scrapper.onrender.com/api/status", timeout=10)
        return response.json()
    except Exception as e:
        log(f"Ошибка проверки статуса API: {e}")
        return None


def start_scraping():
    """Запустить скрапинг всех справочников"""
    try:
        response = requests.post("https://habr-career-salaries-scrapper.onrender.com/api/scrape", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"Ошибка запуска скрапинга: {e}")
        return None


def wait_for_completion():
    """Ждать завершения скрапинга"""
    log("Ожидание завершения скрапинга...")
    while True:
        status = check_api_status()
        if not status:
            time.sleep(10)
            continue
            
        if status.get("status") == "idle":
            log("Скрапинг завершён!")
            return True
        elif status.get("status") == "running":
            log(f"Скрапинг в процессе: {status.get('job_id', 'unknown')}")
            time.sleep(30)
        else:
            log(f"Неизвестный статус: {status}")
            time.sleep(10)


def check_data_quality():
    """Проверить качество данных в БД"""
    try:
        conn = psycopg2.connect(
            host="aws-0-eu-central-1.pooler.supabase.com",
            port=5432,
            dbname="postgres",
            user="postgres.cehitgienxwzplcxbfdk",
            password="!!!!QQQQ2222"
        )
        
        cur = conn.cursor()
        
        # Проверка: сколько записей за последний час
        cur.execute("""
            SELECT COUNT(*) as total_records
            FROM reports 
            WHERE fetched_at >= NOW() - INTERVAL '1 hour'
        """)
        total = cur.fetchone()[0]
        log(f"Всего записей за последний час: {total}")
        
        # Проверка: есть ли записи по регионам
        cur.execute("""
            SELECT COUNT(*) as region_records
            FROM reports r
            JOIN regions rg ON rg.id = r.region_id
            WHERE r.fetched_at >= NOW() - INTERVAL '1 hour'
              AND r.region_id IS NOT NULL
        """)
        region_count = cur.fetchone()[0]
        log(f"Записей по регионам: {region_count}")
        
        # Проверка: есть ли Москва
        cur.execute("""
            SELECT COUNT(*) as moscow_records
            FROM reports r
            JOIN regions rg ON rg.id = r.region_id
            WHERE r.fetched_at >= NOW() - INTERVAL '1 hour'
              AND rg.title = 'Москва'
        """)
        moscow_count = cur.fetchone()[0]
        log(f"Записей по Москве: {moscow_count}")
        
        cur.close()
        conn.close()
        
        return total > 0 and region_count > 0 and moscow_count > 0
        
    except Exception as e:
        log(f"Ошибка проверки данных: {e}")
        return False


def main():
    log("=== Начало автономной задачи ===")
    
    # 1. Проверить статус API
    log("1. Проверка статуса API...")
    status = check_api_status()
    if not status:
        log("ОШИБКА: API недоступен")
        return 1
    log(f"API статус: {status.get('status', 'unknown')}")
    
    # 2. Запустить скрапинг, если не запущен
    if status.get("status") != "running":
        log("2. Запуск скрапинга...")
        result = start_scraping()
        if not result:
            log("ОШИБКА: Не удалось запустить скрапинг")
            return 1
        log(f"Скрапинг запущен: {result.get('job_id', 'unknown')}")
    else:
        log("2. Скрапинг уже запущен")
    
    # 3. Ждать завершения
    log("3. Ожидание завершения...")
    if not wait_for_completion():
        log("ОШИБКА: Скрапинг не завершился")
        return 1
    
    # 4. Проверить качество данных
    log("4. Проверка качества данных...")
    if not check_data_quality():
        log("ОШИБКА: Проблемы с качеством данных")
        return 1
    
    log("=== Задача выполнена успешно! ===")
    log("Теперь можно использовать SQL запрос для анализа данных")
    return 0


if __name__ == "__main__":
    sys.exit(main())
