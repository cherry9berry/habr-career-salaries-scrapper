"""
Unit tests for core module
"""

import unittest
from src.core import Reference, SalaryData, ScrapingConfig


class TestReference(unittest.TestCase):
    """Test Reference dataclass"""

    def test_reference_creation(self):
        """Test creating Reference instance"""
        ref = Reference(id=1, title="Python", alias="python")
        self.assertEqual(ref.id, 1)
        self.assertEqual(ref.title, "Python")
        self.assertEqual(ref.alias, "python")

    def test_reference_equality(self):
        """Test Reference equality"""
        ref1 = Reference(id=1, title="Python", alias="python")
        ref2 = Reference(id=1, title="Python", alias="python")
        ref3 = Reference(id=2, title="Java", alias="java")

        self.assertEqual(ref1, ref2)
        self.assertNotEqual(ref1, ref3)


class TestSalaryData(unittest.TestCase):
    """Test SalaryData dataclass"""

    def test_salary_data_creation(self):
        """Test creating SalaryData instance"""
        data = {"groups": [{"title": "test"}]}
        salary_data = SalaryData(data=data, reference_id=1, reference_type="skills")

        self.assertEqual(salary_data.data, data)
        self.assertEqual(salary_data.reference_id, 1)
        self.assertEqual(salary_data.reference_type, "skills")

    def test_salary_data_with_empty_data(self):
        """Test SalaryData with empty data"""
        salary_data = SalaryData(data={}, reference_id=1, reference_type="regions")

        self.assertEqual(salary_data.data, {})
        self.assertEqual(salary_data.reference_type, "regions")


class TestScrapingConfig(unittest.TestCase):
    """Test ScrapingConfig dataclass"""

    def test_scraping_config_default(self):
        """Test ScrapingConfig with default values"""
        config = ScrapingConfig(reference_types=["skills", "regions"])

        self.assertEqual(config.reference_types, ["skills", "regions"])
        self.assertIsNone(config.combinations)

    def test_scraping_config_with_combinations(self):
        """Test ScrapingConfig with combinations"""
        combinations = [("skills", "regions"), ("companies", "skills")]
        config = ScrapingConfig(reference_types=["skills", "regions", "companies"], combinations=combinations)

        self.assertEqual(len(config.reference_types), 3)
        self.assertEqual(len(config.combinations), 2)
        self.assertIn(("skills", "regions"), config.combinations)

    def test_scraping_config_empty_reference_types(self):
        """Test ScrapingConfig with empty reference types"""
        config = ScrapingConfig(reference_types=[])
        self.assertEqual(config.reference_types, [])
        self.assertIsNone(config.combinations)


if __name__ == "__main__":
    unittest.main()
