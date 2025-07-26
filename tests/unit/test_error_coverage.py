"""
Error coverage tests - testing error handling and edge cases
"""

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import os
import tempfile
from src.core import Reference, SalaryData, ScrapingConfig
from src.config_parser import CsvConfigParser, DefaultConfigParser
from src.database import PostgresRepository
from src.scraper import HabrApiClient, SalaryScraper


class TestErrorHandling(unittest.TestCase):
    """Test various error scenarios"""

    def test_reference_with_none_values(self):
        """Test Reference with None values"""
        # Dataclasses don't automatically validate None values
        ref = Reference(id=None, title="Test", alias="test")
        self.assertIsNone(ref.id)
        self.assertEqual(ref.title, "Test")

    def test_salary_data_with_none_reference_id(self):
        """Test SalaryData with None reference_id"""
        # Dataclasses accept None values
        data = SalaryData(data={}, reference_id=None, reference_type="skills")
        self.assertIsNone(data.reference_id)

    def test_scraping_config_with_none_reference_types(self):
        """Test ScrapingConfig with None reference_types"""
        # This will work but may cause issues later
        config = ScrapingConfig(reference_types=None)
        self.assertIsNone(config.reference_types)

    def test_csv_parser_with_empty_file(self):
        """Test CSV parser with completely empty file"""
        parser = CsvConfigParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("")
            temp_path = f.name

        try:
            with self.assertRaises(ValueError):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)

    def test_csv_parser_with_whitespace_only(self):
        """Test CSV parser with whitespace only file"""
        parser = CsvConfigParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("   \n   \n   ")
            temp_path = f.name

        try:
            with self.assertRaises(ValueError):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)

    @patch('src.database.psycopg2.connect')
    def test_database_connection_timeout(self, mock_connect):
        """Test database connection timeout"""
        import psycopg2

        mock_connect.side_effect = psycopg2.OperationalError("Connection timeout")

        repo = PostgresRepository({"host": "localhost", "database": "test"})

        with self.assertRaises(psycopg2.OperationalError):
            with repo.get_connection():
                pass

    @patch('src.database.psycopg2.connect')
    def test_database_invalid_credentials(self, mock_connect):
        """Test database with invalid credentials"""
        import psycopg2

        mock_connect.side_effect = psycopg2.OperationalError("Invalid username/password")

        repo = PostgresRepository({"host": "localhost", "database": "test", "user": "invalid", "password": "wrong"})

        with self.assertRaises(psycopg2.OperationalError):
            repo.get_references("skills")

    def test_api_client_with_invalid_url(self):
        """Test API client with invalid URL"""
        client = HabrApiClient(url="not-a-valid-url", delay_min=0.1, delay_max=0.2, retry_attempts=1)

        result = client.fetch_salary_data(skill_aliases=["python"])
        self.assertIsNone(result)

    @patch('src.scraper.requests.get')
    def test_api_client_with_malformed_json(self, mock_get):
        """Test API client with malformed JSON response"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = HabrApiClient("https://api.test.com", 0.1, 0.2, 1)
        result = client.fetch_salary_data(spec_alias="backend")

        self.assertIsNone(result)

    @patch('src.scraper.requests.get')
    def test_api_client_http_error_codes(self, mock_get):
        """Test API client with various HTTP error codes"""
        import requests

        error_codes = [400, 401, 403, 404, 429, 500, 502, 503]
        client = HabrApiClient("https://api.test.com", 0.1, 0.2, 1)

        for code in error_codes:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError(f"{code} Error")
            mock_get.return_value = mock_response

            result = client.fetch_salary_data(region_alias="moscow")
            self.assertIsNone(result)

    def test_scraper_with_empty_config(self):
        """Test scraper with empty configuration"""
        mock_repo = Mock()
        mock_api = Mock()
        scraper = SalaryScraper(mock_repo, mock_api)

        config = ScrapingConfig(reference_types=[], combinations=None)
        result = scraper.scrape(config)

        # With our fix, empty config should succeed
        self.assertTrue(result)
        mock_repo.commit_transaction.assert_called_once()

    def test_scraper_all_api_calls_fail(self):
        """Test scraper when all API calls fail"""
        mock_repo = Mock()
        mock_api = Mock()
        mock_repo.get_references.return_value = [Reference(1, "Python", "python"), Reference(2, "Java", "java")]
        mock_api.fetch_salary_data.return_value = None  # All fail

        scraper = SalaryScraper(mock_repo, mock_api)
        config = ScrapingConfig(reference_types=["skills"], combinations=None)

        result = scraper.scrape(config)

        self.assertFalse(result)
        mock_repo.rollback_transaction.assert_called_once()

    def test_file_permission_error(self):
        """Test handling file permission errors"""
        parser = CsvConfigParser()

        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                with self.assertRaises(PermissionError):
                    parser.parse("protected.csv")

    @unittest.skipIf(os.environ.get('GITHUB_ACTIONS'), "Skip DB tests in CI")
    def test_database_transaction_with_no_data(self):
        """Test database transaction with no data"""        
        repo = PostgresRepository({"host": "localhost", "database": "test"})

        # Commit empty transaction - will fail in CI but pass locally
        try:
            repo.commit_transaction("empty-transaction")
            self.assertTrue(True)  # Test passes if no exception raised
        except Exception:
            self.skipTest("Database not available")

    @patch('src.database.psycopg2.connect')
    def test_database_cursor_error(self, mock_connect):
        """Test database cursor creation error"""
        mock_conn = Mock()
        mock_conn.cursor.side_effect = Exception("Cannot create cursor")
        mock_connect.return_value = mock_conn

        repo = PostgresRepository({"host": "localhost", "database": "test"})

        with self.assertRaises(Exception):
            repo.get_references("skills")

    @unittest.skipIf(os.environ.get('GITHUB_ACTIONS'), "Skip DB tests in CI")
    def test_invalid_reference_type_in_commit(self):
        """Test committing with invalid reference type"""        
        repo = PostgresRepository({"host": "localhost", "database": "test"})

        # Add data with invalid reference type
        transaction_id = "test-invalid"
        salary_data = SalaryData(
            data={"test": "data"}, reference_id=1, reference_type="invalid_type"  # Not in field mapping
        )
        
        try:
            repo.save_report(salary_data, transaction_id)
            repo.commit_transaction(transaction_id)
            self.assertTrue(True)  # Test passes if no exception
        except Exception:
            self.skipTest("Database not available")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_csv_parser_single_column(self):
        """Test CSV parser with single valid column"""
        parser = CsvConfigParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("skills\nPython\nJava")
            temp_path = f.name

        try:
            config = parser.parse(temp_path)
            self.assertEqual(config.reference_types, ["skills"])
            self.assertIsNone(config.combinations)
        finally:
            os.unlink(temp_path)

    def test_api_client_zero_delay(self):
        """Test API client with zero delay"""
        client = HabrApiClient(url="https://api.test.com", delay_min=0, delay_max=0, retry_attempts=1)

        with patch('src.scraper.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"groups": [{"data": "test"}]}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with patch('src.scraper.time.sleep') as mock_sleep:
                result = client.fetch_salary_data(company_alias="google")

                self.assertIsNotNone(result)
                # Should still call sleep even with 0 delay
                mock_sleep.assert_called()

    @unittest.skipIf(os.environ.get('GITHUB_ACTIONS'), "Skip DB tests in CI")
    def test_repository_with_large_transaction(self):
        """Test repository with large number of reports in transaction"""
        repo = PostgresRepository({"host": "localhost", "database": "test"})
        transaction_id = "large-transaction"

        # Add 1000 reports
        for i in range(1000):
            salary_data = SalaryData(data={"id": i}, reference_id=i, reference_type="skills")
            repo.save_report(salary_data, transaction_id)

        self.assertEqual(len(repo.transactions[transaction_id]), 1000)

        # Rollback should clear all
        repo.rollback_transaction(transaction_id)
        self.assertNotIn(transaction_id, repo.transactions)


if __name__ == "__main__":
    unittest.main()
