"""
Unit tests for database module
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.database import PostgresRepository
from src.core import Reference, SalaryData


@unittest.skipIf(os.environ.get('GITHUB_ACTIONS'), "Skip DB tests in CI")
class TestPostgresRepository(unittest.TestCase):
    """Test PostgreSQL repository implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }
        self.repo = PostgresRepository(self.config)

    @patch('src.database.psycopg2.connect')
    def test_get_connection(self, mock_connect):
        """Test database connection context manager"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        # Mock the connection pool
        mock_pool = Mock()
        mock_pool.getconn.return_value = mock_conn
        self.repo._pool = mock_pool

        with self.repo.get_connection() as conn:
            self.assertEqual(conn, mock_conn)

        mock_pool.getconn.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)

    @patch('src.database.psycopg2.connect')
    def test_get_references_valid_table(self, mock_connect):
        """Test getting references from valid table"""
        # Mock database response
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, "Python", "python"), (2, "Java", "java")]

        references = self.repo.get_references("skills", limit=10)

        self.assertEqual(len(references), 2)
        self.assertIsInstance(references[0], Reference)
        self.assertEqual(references[0].id, 1)
        self.assertEqual(references[0].title, "Python")
        self.assertEqual(references[0].alias, "python")

        # Verify SQL query
        mock_cursor.execute.assert_called_once()
        query = mock_cursor.execute.call_args[0][0]
        self.assertIn("SELECT id, title, alias", query)
        self.assertIn("FROM skills", query)
        self.assertIn("LIMIT %s", query)

    def test_get_references_invalid_table(self):
        """Test getting references from invalid table"""
        with self.assertRaises(ValueError) as context:
            self.repo.get_references("invalid_table")
        self.assertIn("Invalid table", str(context.exception))

    def test_save_report(self):
        """Test saving report to transaction buffer"""
        transaction_id = "test-transaction-123"
        salary_data = SalaryData(data={"test": "data"}, reference_id=1, reference_type="skills")

        result = self.repo.save_report(salary_data, transaction_id)

        self.assertTrue(result)
        self.assertIn(transaction_id, self.repo.transactions)
        self.assertEqual(len(self.repo.transactions[transaction_id]), 1)
        self.assertEqual(self.repo.transactions[transaction_id][0], salary_data)

    def test_save_multiple_reports(self):
        """Test saving multiple reports to same transaction"""
        transaction_id = "test-transaction-456"

        for i in range(3):
            salary_data = SalaryData(data={"test": f"data{i}"}, reference_id=i, reference_type="skills")
            self.repo.save_report(salary_data, transaction_id)

        self.assertEqual(len(self.repo.transactions[transaction_id]), 3)

    @patch('src.database.execute_values')
    @patch('src.database.SimpleConnectionPool')
    def test_commit_transaction_success(self, mock_pool_class, mock_execute_values):
        """Test successful transaction commit"""
        # Setup mock database
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Add data to transaction
        transaction_id = "test-transaction-789"
        salary_data = SalaryData(data={"groups": [{"title": "test"}]}, reference_id=1, reference_type="skills")
        self.repo.save_report(salary_data, transaction_id)

        # Commit transaction
        self.repo.commit_transaction(transaction_id)

        # Verify database calls
        mock_cursor.execute.assert_any_call("BEGIN")
        mock_conn.commit.assert_called_once()
        mock_execute_values.assert_called()
        self.assertNotIn(transaction_id, self.repo.transactions)

    @patch('src.database.psycopg2.connect')
    def test_commit_transaction_error(self, mock_connect):
        """Test transaction commit with error"""
        # Setup mock database to raise error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        # First call for BEGIN succeeds, second call fails
        mock_cursor.execute.side_effect = [None, Exception("Database error")]

        # Add data to transaction
        transaction_id = "test-transaction-error"
        salary_data = SalaryData(data={"test": "data"}, reference_id=1, reference_type="skills")
        self.repo.save_report(salary_data, transaction_id)

        # Try to commit transaction
        with self.assertRaises(Exception):
            self.repo.commit_transaction(transaction_id)

        mock_conn.rollback.assert_called_once()
        self.assertNotIn(transaction_id, self.repo.transactions)

    def test_commit_nonexistent_transaction(self):
        """Test committing non-existent transaction"""
        # Should not raise error
        self.repo.commit_transaction("nonexistent-transaction")

    def test_rollback_transaction(self):
        """Test rolling back transaction"""
        transaction_id = "test-rollback"
        salary_data = SalaryData(data={"test": "data"}, reference_id=1, reference_type="skills")
        self.repo.save_report(salary_data, transaction_id)

        self.assertIn(transaction_id, self.repo.transactions)

        self.repo.rollback_transaction(transaction_id)

        self.assertNotIn(transaction_id, self.repo.transactions)

    def test_rollback_nonexistent_transaction(self):
        """Test rolling back non-existent transaction"""
        # Should not raise error
        self.repo.rollback_transaction("nonexistent-transaction")

    @patch('src.database.execute_values')
    @patch('src.database.SimpleConnectionPool')
    def test_field_mapping(self, mock_pool_class, mock_execute_values):
        """Test field mapping during transaction commit"""
        # Setup mock database
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Add data for different reference types
        transaction_id = "test-mapping-789"

        # Add skills data
        skills_data = SalaryData(data={"groups": [{"title": "Python"}]}, reference_id=1, reference_type="skills")
        self.repo.save_report(skills_data, transaction_id)

        # Add regions data
        regions_data = SalaryData(data={"groups": [{"title": "Moscow"}]}, reference_id=2, reference_type="regions")
        self.repo.save_report(regions_data, transaction_id)

        # Commit transaction
        self.repo.commit_transaction(transaction_id)

        # Verify execute_values was called
        mock_execute_values.assert_called()
        mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
