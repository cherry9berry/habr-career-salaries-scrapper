"""
Configuration parser implementation
"""

import csv
import logging
from typing import List, Set, Tuple, Optional
from pathlib import Path

from src.core import IConfigParser, ScrapingConfig


class CsvConfigParser(IConfigParser):
    """CSV configuration parser"""

    VALID_HEADERS = {'specializations', 'skills', 'regions', 'companies'}

    def __init__(self, csv_path: Optional[str] = None):
        """Initialize with optional CSV path"""
        self.csv_path = csv_path

    def parse(self, source: Optional[str] = None) -> ScrapingConfig:
        """Parse CSV configuration file"""
        # Use provided source or stored csv_path
        file_path = source or self.csv_path
        if not file_path:
            raise ValueError("No CSV file path provided")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

            # Validate headers
            invalid_headers = headers - self.VALID_HEADERS
            if invalid_headers:
                logging.error(f"Invalid headers found: {invalid_headers}")
                logging.error(f"   Valid headers are: {self.VALID_HEADERS}")
                raise ValueError(f"Invalid headers: {invalid_headers}")

            if not headers:
                raise ValueError("Empty CSV file or no headers found")

            # Read all combinations from data rows
            combinations = []
            for row in reader:
                # Skip empty rows
                if not any(row.values()):
                    continue
                # Store the actual values from the row, not just keys
                row_values = tuple((header, value) for header, value in row.items() if value.strip())
                if row_values:
                    combinations.append(row_values)

            if not combinations:
                raise ValueError("No valid data rows found in CSV file")

        return ScrapingConfig(reference_types=list(headers), combinations=combinations)


class DefaultConfigParser(IConfigParser):
    """Default configuration parser for full scraping"""

    def parse(self, source: Optional[str] = None) -> ScrapingConfig:
        """Parse default configuration (all reference types)"""
        return ScrapingConfig(reference_types=['specializations', 'skills', 'regions', 'companies'], combinations=None)
