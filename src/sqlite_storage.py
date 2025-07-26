"""
Альтернативная реализация временного хранения через SQLite
"""

import sqlite3
import tempfile
import os
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from src.core import IRepository, Reference, SalaryData


class SQLiteTemporaryStorage:
    """Временное хранилище данных в SQLite"""

    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        # Создаем временный файл для SQLite
        self.temp_file = tempfile.NamedTemporaryFile(
            suffix=f'_{transaction_id}.db', delete=False, prefix='scraper_temp_'
        )
        self.db_path = self.temp_file.name
        self.temp_file.close()  # Закрываем файл, но не удаляем

        # Подключаемся к SQLite
        self.conn = sqlite3.connect(self.db_path)
        self._create_temp_table()

    def _create_temp_table(self):
        """Создает временную таблицу в SQLite"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE temp_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                specialization_id INTEGER,
                skills_1 INTEGER,
                region_id INTEGER,
                company_id INTEGER,
                data TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
        """
        )

        # Создаем индексы для быстрого поиска
        cursor.execute("CREATE INDEX idx_temp_specialization ON temp_reports(specialization_id)")
        cursor.execute("CREATE INDEX idx_temp_skills ON temp_reports(skills_1)")
        cursor.execute("CREATE INDEX idx_temp_region ON temp_reports(region_id)")
        cursor.execute("CREATE INDEX idx_temp_company ON temp_reports(company_id)")

        self.conn.commit()
        cursor.close()

    def save_report(self, data: SalaryData) -> bool:
        """Сохранить данные во временное хранилище"""
        try:
            cursor = self.conn.cursor()

            # Определяем поле для вставки
            field_mapping = {
                'specializations': 'specialization_id',
                'skills': 'skills_1',
                'regions': 'region_id',
                'companies': 'company_id',
            }

            field_name = field_mapping.get(data.reference_type)
            if not field_name:
                return False

            # Формируем SQL с правильным полем
            if field_name == 'specialization_id':
                cursor.execute(
                    """
                    INSERT INTO temp_reports (specialization_id, skills_1, region_id, company_id, data, fetched_at)
                    VALUES (?, NULL, NULL, NULL, ?, ?)
                """,
                    (data.reference_id, json.dumps(data.data), datetime.now().isoformat()),
                )
            elif field_name == 'skills_1':
                cursor.execute(
                    """
                    INSERT INTO temp_reports (specialization_id, skills_1, region_id, company_id, data, fetched_at)
                    VALUES (NULL, ?, NULL, NULL, ?, ?)
                """,
                    (data.reference_id, json.dumps(data.data), datetime.now().isoformat()),
                )
            elif field_name == 'region_id':
                cursor.execute(
                    """
                    INSERT INTO temp_reports (specialization_id, skills_1, region_id, company_id, data, fetched_at)
                    VALUES (NULL, NULL, ?, NULL, ?, ?)
                """,
                    (data.reference_id, json.dumps(data.data), datetime.now().isoformat()),
                )
            elif field_name == 'company_id':
                cursor.execute(
                    """
                    INSERT INTO temp_reports (specialization_id, skills_1, region_id, company_id, data, fetched_at)
                    VALUES (NULL, NULL, NULL, ?, ?, ?)
                """,
                    (data.reference_id, json.dumps(data.data), datetime.now().isoformat()),
                )

            self.conn.commit()
            cursor.close()
            return True

        except Exception as e:
            print(f"Error saving to SQLite temp storage: {e}")
            return False

    def get_all_reports(self) -> List[tuple]:
        """Получить все данные из временного хранилища"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT specialization_id, skills_1, region_id, company_id, data, fetched_at
            FROM temp_reports
            ORDER BY id
        """
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def count_reports(self) -> int:
        """Подсчитать количество записей"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM temp_reports")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def cleanup(self):
        """Закрыть соединение и удалить временный файл"""
        if self.conn:
            self.conn.close()

        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
                print(f"Cleaned up SQLite temp file: {self.db_path}")
            except Exception as e:
                print(f"Warning: Could not remove temp file {self.db_path}: {e}")


class PostgresRepositoryWithSQLite(IRepository):
    """PostgreSQL репозиторий с SQLite для временного хранения"""

    def __init__(self, config: dict):
        from src.database import PostgresRepository

        self.postgres_repo = PostgresRepository(config)
        self.temp_storages: dict[str, SQLiteTemporaryStorage] = {}

    def get_references(self, table_name: str, limit: int = 2000) -> List[Reference]:
        """Получить справочники из PostgreSQL"""
        return self.postgres_repo.get_references(table_name, limit)

    def save_report(self, data: SalaryData, transaction_id: str) -> bool:
        """Сохранить во временное SQLite хранилище"""
        # Создаем SQLite хранилище если еще нет
        if transaction_id not in self.temp_storages:
            self.temp_storages[transaction_id] = SQLiteTemporaryStorage(transaction_id)

        return self.temp_storages[transaction_id].save_report(data)

    def commit_transaction(self, transaction_id: str) -> None:
        """Перенести данные из SQLite в PostgreSQL"""
        if transaction_id not in self.temp_storages:
            print(f"No SQLite storage found for transaction {transaction_id}")
            return

        temp_storage = self.temp_storages[transaction_id]
        reports = temp_storage.get_all_reports()
        count = len(reports)

        if count == 0:
            print("No data to commit")
            temp_storage.cleanup()
            del self.temp_storages[transaction_id]
            return

        print(f"Committing {count} reports from SQLite to PostgreSQL...")

        # Используем PostgreSQL соединение для коммита
        with self.postgres_repo.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN")

            try:
                # Переносим данные порциями
                from psycopg2.extras import execute_values

                batch_data = []
                for row in reports:
                    # row: (specialization_id, skills_1, region_id, company_id, data, fetched_at)
                    batch_data.append(
                        (
                            row[0],  # specialization_id
                            row[1],  # skills_1
                            row[2],  # region_id
                            row[3],  # company_id
                            row[4],  # data (JSON string)
                            row[5],  # fetched_at
                        )
                    )

                execute_values(
                    cursor,
                    """INSERT INTO reports (specialization_id, skills_1, region_id, company_id, data, fetched_at)
                       VALUES %s""",
                    batch_data,
                    template=None,
                    page_size=1000,
                )

                # Логируем операцию
                cursor.execute(
                    """
                    INSERT INTO report_log (report_date, report_type, total_variants, success_count, duration_seconds, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (datetime.now(), 'sqlite_import', count, count, 0, 'success'),
                )

                conn.commit()
                print(f"Successfully committed {count} reports from SQLite to PostgreSQL")

            except Exception as e:
                conn.rollback()
                print(f"Error committing from SQLite: {e}")
                raise
            finally:
                cursor.close()

        # Очищаем временное хранилище
        temp_storage.cleanup()
        del self.temp_storages[transaction_id]

    def rollback_transaction(self, transaction_id: str) -> None:
        """Откатить транзакцию - просто удалить SQLite файл"""
        if transaction_id in self.temp_storages:
            temp_storage = self.temp_storages[transaction_id]
            temp_storage.cleanup()
            del self.temp_storages[transaction_id]
            print(f"Rolled back SQLite transaction {transaction_id}")
        else:
            print(f"No SQLite storage to rollback for transaction {transaction_id}")

    def transaction_exists(self, transaction_id: str) -> bool:
        """Проверить существование транзакции"""
        return transaction_id in self.temp_storages
