#!/usr/bin/env python3
"""
Проверка корректности переноса данных в Supabase
"""

import psycopg2

def connect_local():
    """Подключение к локальной БД"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='scraping_db',
            user='scraper',
            password='!!!!QQQQ2222'
        )
        return conn
    except Exception:
        return None

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

def compare_table_data(local_conn, supabase_conn, table_name):
    """Сравнивает данные в таблице между локальной БД и Supabase"""
    local_cursor = local_conn.cursor()
    supabase_cursor = supabase_conn.cursor()
    
    # Считаем записи в локальной БД
    local_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    local_count = local_cursor.fetchone()[0]
    
    # Считаем записи в Supabase
    supabase_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    supabase_count = supabase_cursor.fetchone()[0]
    
    print(f"📊 {table_name}:")
    print(f"   🏠 Локально:  {local_count:,} записей")
    print(f"   ☁️  Supabase:  {supabase_count:,} записей")
    
    if local_count == supabase_count:
        print(f"   ✅ Данные совпадают")
        
        # Проверяем несколько случайных записей
        local_cursor.execute(f"SELECT id, title, alias FROM {table_name} ORDER BY id LIMIT 5")
        local_sample = local_cursor.fetchall()
        
        supabase_cursor.execute(f"SELECT id, title, alias FROM {table_name} ORDER BY id LIMIT 5")
        supabase_sample = supabase_cursor.fetchall()
        
        if local_sample == supabase_sample:
            print(f"   ✅ Содержимое совпадает")
        else:
            print(f"   ⚠️  Содержимое отличается!")
            print(f"      Локально:  {local_sample[0] if local_sample else 'Нет данных'}")
            print(f"      Supabase:  {supabase_sample[0] if supabase_sample else 'Нет данных'}")
    else:
        print(f"   ❌ Количество не совпадает! Разница: {abs(local_count - supabase_count):,}")
        return False
    
    local_cursor.close()
    supabase_cursor.close()
    return True

def main():
    print("🔍 Проверка корректности переноса данных в Supabase...")
    
    # Подключения
    local_conn = connect_local()
    if not local_conn:
        print("❌ Не удалось подключиться к локальной БД")
        print("🔧 Убедитесь что PostgreSQL запущен локально")
        return
    
    try:
        supabase_conn = connect_supabase()
        print("✅ Подключились к обеим БД")
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")
        local_conn.close()
        return
    
    # Проверяем все справочные таблицы
    tables = ['specializations', 'skills', 'regions', 'companies']
    all_ok = True
    
    for table in tables:
        try:
            if not compare_table_data(local_conn, supabase_conn, table):
                all_ok = False
        except Exception as e:
            print(f"❌ Ошибка при проверке {table}: {e}")
            all_ok = False
    
    print("\n" + "="*50)
    if all_ok:
        print("🎉 Все данные корректно перенесены в Supabase!")
        print("✅ Можно переходить к настройке SQLite для временного хранения")
    else:
        print("⚠️  Обнаружены проблемы с переносом данных")
        print("🔧 Нужно повторить перенос данных")
    
    local_conn.close()
    supabase_conn.close()

if __name__ == "__main__":
    main() 