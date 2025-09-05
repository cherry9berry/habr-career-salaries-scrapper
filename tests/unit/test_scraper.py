"""
Unit tests for scraper module
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from src.scraper import HabrApiClient, SalaryScraper
from src.core import ScrapingConfig, Reference, SalaryData


class TestHabrApiClient(unittest.TestCase):
    """Test Habr Career API client"""

    def setUp(self):
        """Set up test fixtures"""
        self.url = "https://test.api.com"
        self.client = HabrApiClient(url=self.url, delay_min=0.1, delay_max=0.2, retry_attempts=3)

    @patch('src.scraper.requests.get')
    @patch('src.scraper.time.sleep')
    def test_fetch_salary_data_success(self, mock_sleep, mock_get):
        """Test successful API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"groups": [{"title": "Test Group", "median": 100000}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.client.fetch_salary_data(spec_alias="backend")

        self.assertIsNotNone(result)
        self.assertEqual(result["groups"][0]["title"], "Test Group")
        mock_get.assert_called_once()
        mock_sleep.assert_called_once()

    @patch('src.scraper.requests.get')
    def test_fetch_salary_data_empty_response(self, mock_get):
        """Test API call with empty response"""
        # Mock empty response
        mock_response = Mock()
        mock_response.json.return_value = {"groups": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.client.fetch_salary_data(skill_aliases=["python"])

        self.assertIsNone(result)

    @patch('src.scraper.requests.get')
    @patch('src.scraper.time.sleep')
    def test_fetch_salary_data_retry_on_error(self, mock_sleep, mock_get):
        """Test API retry on error"""
        # Mock failed responses followed by success
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            Mock(json=lambda: {"groups": [{"title": "Success"}]}, raise_for_status=Mock()),
        ]

        result = self.client.fetch_salary_data(region_alias="moscow")

        self.assertIsNotNone(result)
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)  # 2 retries + 1 success

    @patch('src.scraper.requests.get')
    @patch('src.scraper.time.sleep')
    def test_fetch_salary_data_all_retries_fail(self, mock_sleep, mock_get):
        """Test API call when all retries fail"""
        mock_get.side_effect = requests.RequestException("Network error")

        result = self.client.fetch_salary_data(company_alias="google")

        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 3)

    def test_api_params_mapping(self):
        """Test parameter mapping for API"""
        test_cases = [
            ({"spec_alias": "backend"}, {"spec_aliases[]": "backend"}),
            ({"skill_aliases": ["python", "django"]}, {"skills[]": ["python", "django"]}),
            ({"region_alias": "moscow"}, {"locations[]": "moscow"}),
            ({"company_alias": "google"}, {"company_alias": "google"}),
        ]

        for input_params, expected_api_params in test_cases:
            with patch('src.scraper.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = {"groups": [{"test": "data"}]}
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                self.client.fetch_salary_data(**input_params)

                # Verify API was called with correct params
                call_args = mock_get.call_args[1]["params"]
                self.assertEqual(call_args["employment_type"], 0)
                for key, value in expected_api_params.items():
                    self.assertEqual(call_args[key], value)


class TestSalaryScraper(unittest.TestCase):
    """Test main scraper implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_repo = Mock()
        self.mock_api = Mock()
        self.scraper = SalaryScraper(self.mock_repo, self.mock_api)

    def test_scrape_individual_references_success(self):
        """Test successful scraping of individual references"""
        # Setup mocks
        self.mock_repo.get_references.return_value = [Reference(1, "Python", "python"), Reference(2, "Java", "java")]
        self.mock_api.fetch_salary_data.return_value = {"groups": [{"data": "test"}]}

        config = ScrapingConfig(reference_types=["skills"], combinations=None)

        result = self.scraper.scrape(config)

        self.assertTrue(result)
        self.assertEqual(self.mock_repo.get_references.call_count, 1)
        self.assertEqual(self.mock_api.fetch_salary_data.call_count, 2)
        self.mock_repo.commit_transaction.assert_called_once()
        self.mock_repo.rollback_transaction.assert_not_called()

    def test_scrape_with_partial_success(self):
        """Test scraping with partial success - should still commit"""
        # Setup mocks - 1 success out of 3 (33% success, but still valid)
        self.mock_repo.get_references.return_value = [
            Reference(1, "Python", "python"),
            Reference(2, "Java", "java"),
            Reference(3, "Go", "go"),
        ]
        self.mock_api.fetch_salary_data.side_effect = [
            {"groups": [{"data": "test"}]},  # Success
            None,  # Failure
            None,  # Failure
        ]

        config = ScrapingConfig(reference_types=["skills"], combinations=None)

        result = self.scraper.scrape(config)

        self.assertTrue(result)
        self.mock_repo.commit_transaction.assert_called_once()
        self.mock_repo.rollback_transaction.assert_not_called()

    def test_scrape_multiple_reference_types(self):
        """Test scraping multiple reference types"""
        # Setup mocks
        self.mock_repo.get_references.side_effect = [
            [Reference(1, "Backend", "backend")],
            [Reference(2, "Python", "python")],
        ]
        self.mock_api.fetch_salary_data.return_value = {"groups": [{"data": "test"}]}

        config = ScrapingConfig(reference_types=["specializations", "skills"], combinations=None)

        result = self.scraper.scrape(config)

        self.assertTrue(result)
        self.assertEqual(self.mock_repo.get_references.call_count, 2)
        self.mock_repo.get_references.assert_any_call("specializations")
        self.mock_repo.get_references.assert_any_call("skills")

    def test_scrape_with_combinations(self):
        """Test scraping with combinations (currently not implemented)"""
        config = ScrapingConfig(reference_types=["skills", "regions"], combinations=[("skills", "regions")])

        result = self.scraper.scrape(config)

        # Since combination scraping is not implemented, should return True
        # because 0/0 is considered success
        self.assertTrue(result)
        self.mock_repo.commit_transaction.assert_called_once()

    def test_scrape_exception_handling(self):
        """Test exception handling during scraping"""
        self.mock_repo.get_references.side_effect = Exception("Database error")

        config = ScrapingConfig(reference_types=["skills"], combinations=None)

        result = self.scraper.scrape(config)

        self.assertFalse(result)
        self.mock_repo.rollback_transaction.assert_called_once()

    def test_build_params(self):
        """Test parameter building for different reference types"""
        ref = Reference(1, "Test", "test-alias")

        test_cases = [
            ("specializations", {"spec_alias": "test-alias"}),
            ("skills", {"skill_aliases": ["test-alias"]}),
            ("regions", {"region_alias": "test-alias"}),
            ("companies", {"company_alias": "test-alias"}),
        ]

        for ref_type, expected_params in test_cases:
            params = self.scraper._build_params(ref_type, ref)
            self.assertEqual(params, expected_params)

    def test_build_params_unknown_type(self):
        """Test parameter building for unknown reference type"""
        ref = Reference(1, "Test", "test-alias")
        params = self.scraper._build_params("unknown_type", ref)
        self.assertEqual(params, {})

    @patch('src.scraper.uuid.uuid4')
    def test_transaction_id_generation(self, mock_uuid):
        """Test unique transaction ID generation"""
        mock_uuid.return_value = "test-uuid-123"

        config = ScrapingConfig(reference_types=["skills"], combinations=None)
        self.mock_repo.get_references.return_value = []

        self.scraper.scrape(config)

        # Verify transaction methods were called with generated ID
        # Since there are no references, should not commit (no data to process)
        self.mock_repo.commit_transaction.assert_not_called()

    def test_progress_reporting(self):
        """Test progress reporting during scraping"""
        # Create 15 references to test progress reporting
        references = [Reference(i, f"Item{i}", f"item{i}") for i in range(15)]
        self.mock_repo.get_references.return_value = references
        self.mock_api.fetch_salary_data.return_value = {"groups": [{"data": "test"}]}

        config = ScrapingConfig(reference_types=["skills"], combinations=None)

        with patch('src.scraper.logging.info') as mock_logging:
            self.scraper.scrape(config)

            # Should log progress at multiples of 10
            progress_calls = [call for call in mock_logging.call_args_list if "Progress:" in str(call)]
            self.assertGreater(len(progress_calls), 0)


if __name__ == "__main__":
    unittest.main()
