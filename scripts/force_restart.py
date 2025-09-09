#!/usr/bin/env python3
import subprocess
import time
import requests
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_git_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except:
        return False

def check_status():
    try:
        response = requests.get("https://habr-career-salaries-scrapper.onrender.com/api/status", timeout=10)
        return response.json()
    except:
        return None

log("=== Принудительный рестарт приложения ===")

# Создаём пустой коммит для рестарта
log("1. Создание пустого коммита...")
if run_git_command('git commit --allow-empty -m "restart: force redeploy to stop scraping"'):
    log("Коммит создан")
else:
    log("ОШИБКА: Не удалось создать коммит")
    exit(1)

# Пушим для запуска CI/CD
log("2. Пуш для запуска CI/CD...")
if run_git_command("git push"):
    log("Изменения запушены")
else:
    log("ОШИБКА: Не удалось запушить")
    exit(1)

# Ждём рестарта приложения (2-3 минуты)
log("3. Ожидание рестарта приложения...")
time.sleep(180)  # 3 минуты

# Проверяем, что приложение перезапустилось
log("4. Проверка статуса после рестарта...")
status = check_status()
if status:
    log(f"Статус: {status.get('status', 'unknown')}")
    if status.get("status") == "idle":
        log("✅ Приложение перезапущено, скрапинг остановлен")
    else:
        log("⚠️ Скрапинг всё ещё идёт")
else:
    log("❌ Приложение недоступно")

log("=== Рестарт завершён ===")
