#!/usr/bin/env python3
"""
Бенчмарк для сравнения PostgreSQL temp tables vs SQLite
"""

import time
import uuid
from dataclasses import asdict
from src.settings import Settings
from src.core import SalaryData
from src.database import PostgresRepository
from src.sqlite_storage import PostgresRepositoryWithSQLite

def create_test_data(count: int = 1000):
    """Создает тестовые данные"""
    test_data = []
    for i in range(count):
        data = SalaryData(
            reference_id=i % 100 + 1,  # Случайные ID от 1 до 100
            reference_type='skills',
            data={
                'salary_from': 50000 + i * 10,
                'salary_to': 100000 + i * 20,
                'currency': 'RUB',
                'experience': 'junior' if i % 3 == 0 else 'middle' if i % 3 == 1 else 'senior'
            }
        )
        test_data.append(data)
    return test_data

def benchmark_postgres_temp(test_data, settings):
    """Бенчмарк PostgreSQL temp tables"""
    print("🔥 Тестируем PostgreSQL temp tables...")
    
    repo = PostgresRepository(asdict(settings.database))
    transaction_id = str(uuid.uuid4())
    
    # Тест записи
    start_time = time.time()
    for data in test_data:
        repo.save_report(data, transaction_id)
    write_time = time.time() - start_time
    
    # Тест коммита
    start_time = time.time()
    repo.commit_transaction(transaction_id)
    commit_time = time.time() - start_time
    
    return write_time, commit_time

def benchmark_sqlite(test_data, settings):
    """Бенчмарк SQLite"""
    print("🗄️  Тестируем SQLite...")
    
    repo = PostgresRepositoryWithSQLite(asdict(settings.database))
    transaction_id = str(uuid.uuid4())
    
    # Тест записи
    start_time = time.time()
    for data in test_data:
        repo.save_report(data, transaction_id)
    write_time = time.time() - start_time
    
    # Тест коммита (SQLite -> PostgreSQL)
    start_time = time.time()
    repo.commit_transaction(transaction_id)
    commit_time = time.time() - start_time
    
    return write_time, commit_time

def main():
    print("⚡ Бенчмарк временного хранения данных")
    print("=" * 50)
    
    # Загружаем настройки
    try:
        settings = Settings.load("config.yaml")
        print("✅ Настройки загружены")
    except Exception as e:
        print(f"❌ Ошибка загрузки настроек: {e}")
        return
    
    # Создаем тестовые данные
    test_counts = [100, 1000, 5000]
    
    for count in test_counts:
        print(f"\n📊 Тестируем с {count} записями...")
        test_data = create_test_data(count)
        
        try:
            # PostgreSQL temp tables
            pg_write_time, pg_commit_time = benchmark_postgres_temp(test_data, settings)
            pg_total_time = pg_write_time + pg_commit_time
            
            # SQLite
            sqlite_write_time, sqlite_commit_time = benchmark_sqlite(test_data, settings)
            sqlite_total_time = sqlite_write_time + sqlite_commit_time
            
            # Результаты
            print(f"\n📈 Результаты для {count} записей:")
            print(f"PostgreSQL temp tables:")
            print(f"  ✏️  Запись: {pg_write_time:.3f}s ({count/pg_write_time:.0f} записей/сек)")
            print(f"  💾 Коммит: {pg_commit_time:.3f}s")
            print(f"  🏁 Всего:  {pg_total_time:.3f}s")
            
            print(f"SQLite:")
            print(f"  ✏️  Запись: {sqlite_write_time:.3f}s ({count/sqlite_write_time:.0f} записей/сек)")
            print(f"  💾 Коммит: {sqlite_commit_time:.3f}s")
            print(f"  🏁 Всего:  {sqlite_total_time:.3f}s")
            
            # Сравнение
            if sqlite_total_time < pg_total_time:
                speedup = pg_total_time / sqlite_total_time
                print(f"🚀 SQLite быстрее в {speedup:.1f}x раз")
            else:
                slowdown = sqlite_total_time / pg_total_time
                print(f"🐌 PostgreSQL быстрее в {slowdown:.1f}x раз")
            
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            continue
    
    print(f"\n🏆 Бенчмарк завершен!")

if __name__ == "__main__":
    main() 