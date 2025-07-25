"""
Database implementation for salary scraper
"""

import psycopg2
from psycopg2.extras import Json, execute_values
from psycopg2.pool import SimpleConnectionPool
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from contextlib import contextmanager

from src.core import IRepository, Reference, SalaryData


class PostgresRepository(IRepository):
    """PostgreSQL implementation of repository"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._pool: SimpleConnectionPool | None = None
        self.transactions: Dict[str, list[SalaryData]] = {}

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
                    WHERE created_at = (SELECT MAX(created_at) FROM {table_name})
                    ORDER BY id
                    LIMIT %s
                """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            cursor.close()

        return [Reference(id=row[0], title=row[1], alias=row[2]) for row in rows]

    def save_report(self, data: SalaryData, transaction_id: str) -> bool:
        """Save report to transaction buffer"""
        if transaction_id not in self.transactions:
            self.transactions[transaction_id] = []

        self.transactions[transaction_id].append(data)
        return True

    def commit_transaction(self, transaction_id: str) -> None:
        """Commit all changes for transaction"""
        if transaction_id not in self.transactions:
            return

        reports = self.transactions[transaction_id]
        if not reports:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN")

            field_mapping = {
                'specializations': 'specialization_id',
                'skills': 'skills_1',
                'regions': 'region_id',
                'companies': 'company_id',
            }

            # Group rows by field for bulk insert
            bulk_dict: Dict[str, list[tuple]] = {}
            for rep in reports:
                field = field_mapping.get(rep.reference_type)
                if not field:
                    continue
                tup = (rep.reference_id, Json(rep.data), datetime.now())
                bulk_dict.setdefault(field, []).append(tup)

            try:
                for field, rows in bulk_dict.items():
                    query = f"INSERT INTO reports ({field}, data, fetched_at) VALUES %s"
                    execute_values(cursor, query, rows)

                cursor.execute(
                    "INSERT INTO report_log (report_date, report_type, total_variants, success_count, duration_seconds, status) VALUES (%s,%s,%s,%s,%s,%s)",
                    (datetime.now(), 'batch_import', len(reports), len(reports), 0, 'success'),
                )

                conn.commit()
                print(f"Successfully committed {len(reports)} reports")
            except Exception as e:
                conn.rollback()
                print(f"Error committing transaction: {e}")
                raise
            finally:
                cursor.close()
                del self.transactions[transaction_id]

    def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback transaction on error"""
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]
            print(f"Rolled back transaction {transaction_id}")
