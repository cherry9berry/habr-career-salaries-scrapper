"""
Configuration parser implementation
"""

import csv
from typing import List, Set
from pathlib import Path

from src.core import IConfigParser, ScrapingConfig


class CsvConfigParser(IConfigParser):
    """CSV configuration parser"""

    VALID_HEADERS = {'specializations', 'skills', 'regions', 'companies'}

    def parse(self, source: str) -> ScrapingConfig:
        """Parse CSV configuration file"""
        if not Path(source).exists():
            raise FileNotFoundError(f"Configuration file not found: {source}")

        with open(source, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

            # Validate headers
            invalid_headers = headers - self.VALID_HEADERS
            if invalid_headers:
                print(f"Invalid headers found: {invalid_headers}")
                print(f"   Valid headers are: {self.VALID_HEADERS}")
                raise ValueError(f"Invalid headers: {invalid_headers}")

            valid_headers = headers & self.VALID_HEADERS

            if not valid_headers:
                raise ValueError("No valid headers found in CSV file")

            # Determine if we need combinations
            if len(valid_headers) > 1:
                # For now, create pairs of headers for combinations
                combinations = []
                headers_list = list(valid_headers)
                for i in range(len(headers_list)):
                    for j in range(i + 1, len(headers_list)):
                        combinations.append((headers_list[i], headers_list[j]))

                return ScrapingConfig(
                    reference_types=list(valid_headers), combinations=combinations
                )
            else:
                # Single header - no combinations needed
                return ScrapingConfig(reference_types=list(valid_headers), combinations=None)


class DefaultConfigParser(IConfigParser):
    """Default configuration parser - uses all reference types"""

    def parse(self, source: str = "") -> ScrapingConfig:
        """Return default configuration"""
        return ScrapingConfig(
            reference_types=['specializations', 'skills', 'regions', 'companies'], combinations=None
        )
