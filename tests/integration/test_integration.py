"""
Integration tests for salary scraper
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, Mock
from src.database import PostgresRepository
from src.scraper import HabrApiClient, SalaryScraper
from src.config_parser import CsvConfigParser, DefaultConfigParser
from src.core import ScrapingConfig


@unittest.skipIf(os.environ.get('GITHUB_ACTIONS'), "Skip integration tests in CI")
class TestEndToEndScraping(unittest.TestCase):
    """Test complete scraping workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
            },
            "api": {"url": "https://test.api.com", "delay_min": 0.1, "delay_max": 0.2, "retry_attempts": 3},
        }

    def tearDown(self):
        """Clean up test fixtures"""
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    @patch('src.database.execute_values')
    @patch('src.database.psycopg2.connect')
    @patch('src.scraper.requests.get')
    @patch('src.scraper.time.sleep')
    def test_full_scraping_workflow(self, mock_sleep, mock_requests, mock_db_connect, mock_execute_values):
        """Test complete scraping workflow from config to database"""
        # Setup database mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(1, "Python", "python"), (2, "Java", "java")]

        # Setup API mock
        mock_response = Mock()
        mock_response.json.return_value = {"groups": [{"title": "Test Group", "median": 100000}]}
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Create components
        repository = PostgresRepository(self.config["database"])
        api_client = HabrApiClient(**self.config["api"])
        scraper = SalaryScraper(repository, api_client)

        # Create config
        config = ScrapingConfig(reference_types=["skills"], combinations=None)

        # Run scraping
        result = scraper.scrape(config)

        # Verify results
        self.assertTrue(result)
        mock_cursor.execute.assert_any_call("BEGIN")
        mock_conn.commit.assert_called()
        mock_execute_values.assert_called()

    def test_csv_config_to_scraping(self):
        """Test CSV configuration parsing to scraping config"""
        # Create CSV file
        csv_path = os.path.join(self.temp_dir, "config.csv")
        with open(csv_path, 'w') as f:
            f.write("skills,regions\nPython,Moscow\nJava,SPB")

        # Parse config
        parser = CsvConfigParser()
        config = parser.parse(csv_path)

        # Verify config
        self.assertIn("skills", config.reference_types)
        self.assertIn("regions", config.reference_types)
        self.assertIsNotNone(config.combinations)
        self.assertEqual(len(config.combinations), 1)
        # Check that combination exists regardless of order
        combinations_tuples = [tuple(sorted(c)) for c in config.combinations]
        self.assertIn(("regions", "skills"), combinations_tuples)

    @patch('src.database.psycopg2.connect')
    def test_database_error_handling(self, mock_db_connect):
        """Test handling of database connection errors"""
        # Make connection fail
        mock_db_connect.side_effect = Exception("Database connection failed")

        repository = PostgresRepository(self.config["database"])

        # Should raise exception when trying to get references
        with self.assertRaises(Exception):
            repository.get_references("skills")

    @patch('src.scraper.requests.get')
    def test_api_error_handling(self, mock_requests):
        """Test handling of API errors"""
        # Make all API calls fail
        mock_requests.side_effect = Exception("API error")

        api_client = HabrApiClient(**self.config["api"])
        result = api_client.fetch_salary_data(skill_aliases=["python"])

        # Should return None after all retries
        self.assertIsNone(result)
        self.assertEqual(mock_requests.call_count, 3)  # All retries


@unittest.skipIf(os.environ.get('GITHUB_ACTIONS'), "Skip integration tests in CI")
class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading and validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_load_json_config(self):
        """Test loading JSON configuration"""
        config_path = os.path.join(self.temp_dir, "config.json")
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "user": "test_user",
                "password": "test_pass",
            },
            "api": {"url": "https://api.test.com", "delay_min": 1.5, "delay_max": 2.5, "retry_attempts": 3},
        }

        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        # Load config
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)

        self.assertEqual(loaded_config, config_data)
        self.assertIn("database", loaded_config)
        self.assertIn("api", loaded_config)

    def test_invalid_csv_headers(self):
        """Test CSV with invalid headers"""
        csv_path = os.path.join(self.temp_dir, "invalid.csv")
        with open(csv_path, 'w') as f:
            f.write("invalid_header1,invalid_header2\nData1,Data2")

        parser = CsvConfigParser()

        with self.assertRaises(ValueError) as context:
            parser.parse(csv_path)

        self.assertIn("Invalid headers", str(context.exception))

    def test_mixed_valid_invalid_headers(self):
        """Test CSV with mixed valid and invalid headers"""
        csv_path = os.path.join(self.temp_dir, "mixed.csv")
        with open(csv_path, 'w') as f:
            f.write("skills,invalid_header\nPython,Data")

        parser = CsvConfigParser()

        with self.assertRaises(ValueError):
            parser.parse(csv_path)


@unittest.skipIf(os.environ.get('GITHUB_ACTIONS'), "Skip integration tests in CI")
class TestErrorRecovery(unittest.TestCase):
    """Test error recovery and resilience"""

    @patch('src.database.execute_values')
    @patch('src.database.psycopg2.connect')
    @patch('src.scraper.requests.get')
    def test_partial_api_failures(self, mock_requests, mock_db_connect, mock_execute_values):
        """Test handling partial API failures"""
        # Setup database mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(1, "Python", "python"), (2, "Java", "java"), (3, "Go", "go")]

        # Setup API mock - 2 successes, 1 failure (66% success rate)
        responses = [
            Mock(json=lambda: {"groups": [{"data": "test1"}]}, raise_for_status=Mock()),
            Exception("API Error"),
            Mock(json=lambda: {"groups": [{"data": "test3"}]}, raise_for_status=Mock()),
        ]
        mock_requests.side_effect = responses

        # Create components
        repository = PostgresRepository({"host": "localhost", "database": "test"})
        api_client = HabrApiClient("https://api.test.com", 0.1, 0.2, 1)  # Only 1 retry
        scraper = SalaryScraper(repository, api_client)

        # Run scraping
        config = ScrapingConfig(reference_types=["skills"], combinations=None)
        result = scraper.scrape(config)

        # Should succeed because 66% > 60%
        self.assertTrue(result)
        mock_conn.commit.assert_called()
        mock_execute_values.assert_called()

    def test_transaction_rollback_on_error(self):
        """Test transaction rollback on critical error"""
        repository = PostgresRepository({"host": "localhost", "database": "test"})

        # Add data to transaction
        transaction_id = "test-transaction"
        from src.core import SalaryData

        salary_data = SalaryData(data={"test": "data"}, reference_id=1, reference_type="skills")
        repository.save_report(salary_data, transaction_id)

        # Verify data is in transaction
        self.assertIn(transaction_id, repository.transactions)

        # Rollback
        repository.rollback_transaction(transaction_id)

        # Verify transaction is cleared
        self.assertNotIn(transaction_id, repository.transactions)


if __name__ == "__main__":
    unittest.main()
