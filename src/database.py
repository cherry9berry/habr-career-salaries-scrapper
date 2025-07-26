"""Database layer implementation using PostgreSQL with temporary table storage"""

import psycopg2
from psycopg2.extras import Json, execute_values
from psycopg2.pool import SimpleConnectionPool
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from contextlib import contextmanager
from src.core import IRepository, Reference, SalaryData


class PostgresRepository(IRepository):
    """PostgreSQL implementation of repository with temporary table storage"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._pool: Optional[SimpleConnectionPool] = None

    # ---------- Pool helpers ----------

    def _init_pool(self):
        if self._pool is None:
            self._pool = SimpleConnectionPool(minconn=1, maxconn=10, **self.config)

    @contextmanager
    def get_connection(self):
        """Context manager: obtain connection from pool"""
        self._init_pool()
        assert self._pool is not None
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def _create_temp_table(self, transaction_id: str, conn) -> None:
        """Create temporary table for transaction"""
        table_name = f"temp_scraping_{transaction_id.replace('-', '_')}"
        cursor = conn.cursor()

        # Create temporary table with same structure as reports
        cursor.execute(
            f"""
            CREATE TEMPORARY TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                specialization_id INTEGER,
                skills_1 INTEGER,
                region_id INTEGER,
                company_id INTEGER,  
                data JSONB NOT NULL,
                fetched_at TIMESTAMP DEFAULT NOW()
            )
        """
        )
        cursor.close()

    def _get_temp_table_name(self, transaction_id: str) -> str:
        """Get temporary table name for transaction"""
        return f"temp_scraping_{transaction_id.replace('-', '_')}"

    def get_references(self, table_name: str, limit: int = 2000) -> List[Reference]:
        """Get references from database"""
        valid_tables = ["specializations", "skills", "regions", "companies"]
        if table_name not in valid_tables:
            raise ValueError(f"Invalid table: {table_name}. Must be one of {valid_tables}")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = f"""
                    SELECT id, title, alias
                    FROM {table_name}
                    ORDER BY id
                    LIMIT %s
                    """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            cursor.close()

        return [Reference(id=row[0], title=row[1], alias=row[2]) for row in rows]

    def save_report(self, data: SalaryData, transaction_id: str) -> bool:
        """Save report to temporary table"""
        try:
            with self.get_connection() as conn:
                table_name = self._get_temp_table_name(transaction_id)
                cursor = conn.cursor()

                # Check if temp table exists, create if not
                # Use a more reliable way to check temp table existence
                try:
                    cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                    # Table exists
                except psycopg2.Error:
                    # Table doesn't exist, create it
                    cursor.close()
                    self._create_temp_table(transaction_id, conn)
                    cursor = conn.cursor()

                # Determine field mapping
                field_mapping = {
                    'specializations': 'specialization_id',
                    'skills': 'skills_1',
                    'regions': 'region_id',
                    'companies': 'company_id',
                }

                field_name = field_mapping.get(data.reference_type)
                if not field_name:
                    cursor.close()
                    return False

                # Insert into temporary table
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} ({field_name}, data, fetched_at)
                    VALUES (%s, %s, %s)
                """,
                    (data.reference_id, Json(data.data), datetime.now()),
                )

                conn.commit()
                cursor.close()
                return True

        except Exception as e:
            print(f"Error saving report to temp table: {e}")
            return False

    def commit_transaction(self, transaction_id: str) -> None:
        """Move data from temporary table to permanent reports table"""
        try:
            with self.get_connection() as conn:
                table_name = self._get_temp_table_name(transaction_id)
                cursor = conn.cursor()

                # Check if temp table exists
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                except psycopg2.Error:
                    print(f"No temporary table found for transaction {transaction_id}")
                    cursor.close()
                    return

                cursor.execute("BEGIN")

                try:
                    if count == 0:
                        print("No data to commit")
                        cursor.close()
                        return

                    # Move data from temp table to reports table
                    cursor.execute(
                        f"""
                        INSERT INTO reports (specialization_id, skills_1, region_id, company_id, data, fetched_at)
                        SELECT specialization_id, skills_1, region_id, company_id, data, fetched_at
                        FROM {table_name}
                    """
                    )

                    # Log the operation
                    cursor.execute(
                        """
                        INSERT INTO report_log (report_date, report_type, total_variants, success_count, duration_seconds, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (datetime.now(), 'batch_import', count, count, 0, 'success'),
                    )

                    # Drop temporary table
                    cursor.execute(f"DROP TABLE {table_name}")

                    conn.commit()
                    print(f"Successfully committed {count} reports from temporary storage")

                except Exception as e:
                    conn.rollback()
                    print(f"Error committing transaction: {e}")
                    raise
                finally:
                    cursor.close()

        except Exception as e:
            print(f"Critical error during commit: {e}")
            raise

    def rollback_transaction(self, transaction_id: str) -> None:
        """Drop temporary table to rollback transaction"""
        try:
            with self.get_connection() as conn:
                table_name = self._get_temp_table_name(transaction_id)
                cursor = conn.cursor()

                # Check if temp table exists and drop it
                try:
                    cursor.execute(f"DROP TABLE {table_name}")
                    conn.commit()
                    print(f"Rolled back transaction {transaction_id} (dropped temp table)")
                except psycopg2.Error:
                    print(f"No temp table to rollback for transaction {transaction_id}")

                cursor.close()

        except Exception as e:
            print(f"Error during rollback: {e}")

    def transaction_exists(self, transaction_id: str) -> bool:
        """Check if transaction exists (temp table exists)"""
        try:
            with self.get_connection() as conn:
                table_name = self._get_temp_table_name(transaction_id)
                cursor = conn.cursor()

                try:
                    cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                    cursor.close()
                    return True
                except psycopg2.Error:
                    cursor.close()
                    return False

        except Exception:
            return False
