"""
Unit tests for config_parser module
"""

import unittest
import tempfile
import os
from src.config_parser import CsvConfigParser, DefaultConfigParser
from src.core import ScrapingConfig


class TestCsvConfigParser(unittest.TestCase):
    """Test CSV configuration parser"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = CsvConfigParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temp files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def create_csv_file(self, content: str, filename: str = "test.csv") -> str:
        """Helper to create CSV file"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    def test_parse_single_header(self):
        """Test parsing CSV with single header"""
        csv_path = self.create_csv_file("skills\nPython\nJava")
        config = self.parser.parse(csv_path)

        self.assertEqual(config.reference_types, ["skills"])
        # Single header still generates combinations - one combination per value
        self.assertIsNotNone(config.combinations)

    def test_parse_multiple_headers(self):
        """Test parsing CSV with multiple headers"""
        csv_path = self.create_csv_file("skills,regions\nPython,Moscow\nJava,SPB")
        config = self.parser.parse(csv_path)

        self.assertIn("skills", config.reference_types)
        self.assertIn("regions", config.reference_types)
        self.assertIsNotNone(config.combinations)
        # Check specific combinations from CSV data
        expected_combinations = [
            (('skills', 'Python'), ('regions', 'Moscow')),
            (('skills', 'Java'), ('regions', 'SPB')),
        ]
        for expected_combo in expected_combinations:
            # Check that combination exists regardless of order
            combo_sorted = tuple(sorted(expected_combo))
            combinations_sorted = [tuple(sorted(c)) for c in config.combinations]
            self.assertIn(combo_sorted, combinations_sorted)

    def test_parse_all_headers(self):
        """Test parsing CSV with all valid headers"""
        csv_path = self.create_csv_file("specializations,skills,regions,companies\nBackend,Python,Moscow,Google")
        config = self.parser.parse(csv_path)

        self.assertEqual(len(config.reference_types), 4)
        self.assertIsNotNone(config.combinations)
        # Combinations are generated from data rows, not headers
        self.assertGreater(len(config.combinations), 0)

    def test_parse_invalid_header(self):
        """Test parsing CSV with invalid header"""
        csv_path = self.create_csv_file("invalid_header,skills\nData1,Python")

        with self.assertRaises(ValueError) as context:
            self.parser.parse(csv_path)
        self.assertIn("Invalid headers", str(context.exception))

    def test_parse_empty_csv(self):
        """Test parsing empty CSV file"""
        csv_path = self.create_csv_file("")

        with self.assertRaises(ValueError) as context:
            self.parser.parse(csv_path)
        self.assertIn("Empty CSV file or no headers found", str(context.exception))

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse("nonexistent.csv")

    def test_valid_headers_constant(self):
        """Test VALID_HEADERS constant"""
        expected_headers = {'specializations', 'skills', 'regions', 'companies'}
        self.assertEqual(self.parser.VALID_HEADERS, expected_headers)


class TestDefaultConfigParser(unittest.TestCase):
    """Test default configuration parser"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = DefaultConfigParser()

    def test_parse_default(self):
        """Test default configuration"""
        config = self.parser.parse()

        expected_types = ['specializations', 'skills', 'regions', 'companies']
        self.assertEqual(config.reference_types, expected_types)
        self.assertIsNone(config.combinations)

    def test_parse_with_source(self):
        """Test parsing with source parameter (should be ignored)"""
        config = self.parser.parse("ignored_source.csv")

        expected_types = ['specializations', 'skills', 'regions', 'companies']
        self.assertEqual(config.reference_types, expected_types)
        self.assertIsNone(config.combinations)


if __name__ == "__main__":
    unittest.main()
