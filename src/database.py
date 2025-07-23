"""
Database implementation for salary scraper
"""
import psycopg2
from psycopg2.extras import Json
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from contextlib import contextmanager

from src.core import IRepository, Reference, SalaryData


class PostgresRepository(IRepository):
    """PostgreSQL implementation of repository"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conn = None
        self.transactions = {}  # transaction_id -> list of changes
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connection"""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()
            
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
            
            # Start transaction
            cursor.execute("BEGIN")
            
            try:
                # Insert all reports
                for report in reports:
                    field_mapping = {
                        'specializations': 'specialization_id',
                        'skills': 'skills_1',
                        'regions': 'region_id', 
                        'companies': 'company_id'
                    }
                    
                    field = field_mapping.get(report.reference_type)
                    if not field:
                        continue
                        
                    query = f"""
                        INSERT INTO reports ({field}, data, fetched_at)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(query, (
                        report.reference_id,
                        Json(report.data),
                        datetime.now()
                    ))
                
                # Log the operation
                cursor.execute("""
                    INSERT INTO report_log (report_date, report_type, total_variants, success_count, duration_seconds, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now(),
                    'batch_import',
                    len(reports),
                    len(reports),
                    0,
                    'success'
                ))
                
                conn.commit()
                print(f"Successfully committed {len(reports)} reports")
                
            except Exception as e:
                conn.rollback()
                print(f"Error committing transaction: {e}")
                raise
            finally:
                # Clear transaction buffer
                del self.transactions[transaction_id]
                
    def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback transaction on error"""
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]
            print(f"Rolled back transaction {transaction_id}") 