#!/usr/bin/env python3
"""
Исправление дубликатов в таблице skills и корректный перенос
"""

import psycopg2
from psycopg2.extras import execute_values
import time
from collections import defaultdict

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

def analyze_duplicates():
    """Анализирует дубликаты в локальной БД"""
    print("🔍 Анализируем дубликаты в локальной БД...")
    
    local_conn = connect_local()
    cursor = local_conn.cursor()
    
    # Ищем дубликаты по alias
    cursor.execute("""
        SELECT alias, COUNT(*), STRING_AGG(title, '; ') as titles
        FROM skills 
        GROUP BY alias 
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"❌ Найдено {len(duplicates)} дубликатов по alias:")
        for alias, count, titles in duplicates[:5]:
            print(f"   '{alias}': {count} раз - {titles[:100]}...")
    
    # Считаем уникальные alias
    cursor.execute("SELECT COUNT(DISTINCT alias) FROM skills")
    unique_aliases = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM skills")
    total_records = cursor.fetchone()[0]
    
    print(f"📊 Всего записей: {total_records:,}")
    print(f"📊 Уникальных alias: {unique_aliases:,}")
    print(f"📊 Дубликатов: {total_records - unique_aliases:,}")
    
    cursor.close()
    local_conn.close()
    
    return unique_aliases

def transfer_unique_skills():
    """Переносит только уникальные записи (берет первую по id для каждого alias)"""
    print("\n🔄 Переносим уникальные skills...")
    
    local_conn = connect_local()
    supabase_conn = connect_supabase()
    
    try:
        local_cursor = local_conn.cursor()
        supabase_cursor = supabase_conn.cursor()
        
        # Очищаем таблицу в Supabase
        print("🧹 Очищаем таблицу skills в Supabase...")
        supabase_cursor.execute("DELETE FROM skills")
        supabase_conn.commit()
        
        # Выбираем только уникальные записи (первую по id для каждого alias)
        query = """
        SELECT DISTINCT ON (alias) id, title, alias
        FROM skills 
        ORDER BY alias, id
        """
        
        local_cursor.execute(query)
        unique_records = local_cursor.fetchall()
        
        print(f"📊 Найдено {len(unique_records):,} уникальных записей")
        
        # Переносим порциями
        batch_size = 500
        processed = 0
        
        for i in range(0, len(unique_records), batch_size):
            batch = unique_records[i:i + batch_size]
            
            try:
                execute_values(
                    supabase_cursor,
                    "INSERT INTO skills (id, title, alias) VALUES %s",
                    batch,
                    template=None,
                    page_size=100
                )
                
                processed += len(batch)
                percent = (processed / len(unique_records)) * 100
                print(f"\r📤 Перенесено {processed:,}/{len(unique_records):,} ({percent:.1f}%)", end='', flush=True)
                
                supabase_conn.commit()
                time.sleep(0.05)  # Пауза между порциями
                
            except Exception as e:
                print(f"\n❌ Ошибка при вставке порции: {e}")
                supabase_conn.rollback()
                
                # Вставляем по одной записи
                for record in batch:
                    try:
                        supabase_cursor.execute(
                            "INSERT INTO skills (id, title, alias) VALUES (%s, %s, %s)",
                            record
                        )
                        supabase_conn.commit()
                        processed += 1
                    except Exception as single_error:
                        print(f"\n⚠️  Пропускаем: {record} - {single_error}")
                        supabase_conn.rollback()
        
        # Обновляем sequence
        supabase_cursor.execute("SELECT setval(pg_get_serial_sequence('skills', 'id'), COALESCE(MAX(id), 1)) FROM skills")
        supabase_conn.commit()
        
        # Проверяем результат
        supabase_cursor.execute("SELECT COUNT(*) FROM skills")
        final_count = supabase_cursor.fetchone()[0]
        
        print(f"\n✅ Перенесено {final_count:,} уникальных записей")
        
        # Показываем примеры
        supabase_cursor.execute("SELECT id, title, alias FROM skills ORDER BY id LIMIT 5")
        sample = supabase_cursor.fetchall()
        print("📋 Примеры записей:")
        for row in sample:
            print(f"   {row[0]}: {row[1]} ({row[2]})")
        
        local_cursor.close()
        supabase_cursor.close()
        
        return final_count
        
    finally:
        local_conn.close()
        supabase_conn.close()

def main():
    print("🔧 Исправление дубликатов в таблице skills")
    print("=" * 50)
    
    # Анализируем дубликаты
    expected_unique = analyze_duplicates()
    
    # Переносим уникальные записи
    actual_transferred = transfer_unique_skills()
    
    print(f"\n📊 Итоговая статистика:")
    print(f"   Ожидалось уникальных: {expected_unique:,}")
    print(f"   Перенесено в Supabase: {actual_transferred:,}")
    
    if actual_transferred == expected_unique:
        print("🎉 Все уникальные записи успешно перенесены!")
    else:
        print(f"⚠️  Разница: {abs(expected_unique - actual_transferred):,} записей")

if __name__ == "__main__":
    main() 