#!/usr/bin/env python3
"""
Исправление переноса таблицы skills
"""

import psycopg2
from psycopg2.extras import execute_values
import time

def connect_local():
    """Подключение к локальной БД"""
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='scraping_db',
        user='scraper',
        password='!!!!QQQQ2222'
    )
    return conn

def connect_supabase():
    """Подключение к Supabase"""
    conn = psycopg2.connect(
        host='aws-0-eu-central-1.pooler.supabase.com',
        port=5432,
        database='postgres',
        user='postgres.cehitgienxwzplcxbfdk',
        password='!!!!QQQQ2222'
    )
    return conn

def print_progress_bar(current: int, total: int, prefix: str = "", bar_length: int = 50):
    """Печатает прогресс-бар"""
    percent = current / total
    filled_length = int(bar_length * percent)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    print(f'\r{prefix} |{bar}| {current}/{total} ({percent:.1%})', end='', flush=True)

def fix_skills_transfer():
    """Исправляет перенос таблицы skills"""
    print("🔧 Исправляем перенос таблицы skills...")
    
    local_conn = connect_local()
    supabase_conn = connect_supabase()
    
    try:
        local_cursor = local_conn.cursor()
        supabase_cursor = supabase_conn.cursor()
        
        # Считаем записи в локальной БД
        local_cursor.execute("SELECT COUNT(*) FROM skills")
        total_count = local_cursor.fetchone()[0]
        print(f"📊 Всего записей в локальной БД: {total_count:,}")
        
        # Полностью очищаем таблицу в Supabase
        print("🧹 Полностью очищаем таблицу skills в Supabase...")
        supabase_cursor.execute("DELETE FROM skills")
        supabase_conn.commit()
        
        # Читаем все данные из локальной БД порциями
        batch_size = 500  # Уменьшаем размер порции для надежности
        processed = 0
        
        # Открываем серверный курсор для экономии памяти
        local_cursor.execute("SELECT id, title, alias FROM skills ORDER BY id")
        
        print("📤 Переносим данные порциями...")
        
        while True:
            rows = local_cursor.fetchmany(batch_size)
            if not rows:
                break
            
            # Вставляем порцию с более консервативными настройками
            try:
                execute_values(
                    supabase_cursor,
                    "INSERT INTO skills (id, title, alias) VALUES %s ON CONFLICT (alias) DO UPDATE SET title = EXCLUDED.title",
                    rows,
                    template=None,
                    page_size=50  # Еще меньший page_size
                )
                
                processed += len(rows)
                print_progress_bar(processed, total_count, f"📤 skills")
                
                # Коммитим каждую порцию
                supabase_conn.commit()
                
                # Небольшая пауза между порциями
                time.sleep(0.1)
                
            except Exception as e:
                print(f"\n❌ Ошибка при вставке порции: {e}")
                print(f"   Размер порции: {len(rows)}")
                print(f"   Первая запись: {rows[0] if rows else 'N/A'}")
                supabase_conn.rollback()
                
                # Пробуем вставить по одной записи
                print("🔄 Пробуем вставить по одной записи...")
                for row in rows:
                    try:
                        supabase_cursor.execute(
                            "INSERT INTO skills (id, title, alias) VALUES (%s, %s, %s) ON CONFLICT (alias) DO UPDATE SET title = EXCLUDED.title",
                            row
                        )
                        supabase_conn.commit()
                        processed += 1
                        print_progress_bar(processed, total_count, f"📤 skills")
                    except Exception as single_error:
                        print(f"\n⚠️  Пропускаем проблемную запись: {row} - {single_error}")
                        supabase_conn.rollback()
                        continue
        
        # Обновляем sequence
        supabase_cursor.execute("SELECT setval(pg_get_serial_sequence('skills', 'id'), COALESCE(MAX(id), 1)) FROM skills")
        supabase_conn.commit()
        
        # Проверяем результат
        supabase_cursor.execute("SELECT COUNT(*) FROM skills")
        final_count = supabase_cursor.fetchone()[0]
        
        print(f"\n✅ Перенос завершен!")
        print(f"📊 Итого перенесено: {final_count:,} из {total_count:,} записей")
        
        if final_count == total_count:
            print("🎉 Все данные успешно перенесены!")
        else:
            missing = total_count - final_count
            print(f"⚠️  Не перенесено {missing:,} записей")
            
            # Показываем примеры оставшихся записей
            supabase_cursor.execute("SELECT id, title, alias FROM skills LIMIT 5")
            sample = supabase_cursor.fetchall()
            print("📋 Примеры перенесенных записей:")
            for row in sample:
                print(f"   {row[0]}: {row[1]} ({row[2]})")
        
        local_cursor.close()
        supabase_cursor.close()
        
    finally:
        local_conn.close()
        supabase_conn.close()

if __name__ == "__main__":
    fix_skills_transfer() 