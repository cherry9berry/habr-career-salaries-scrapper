"""
API client and scraper implementation
"""

import requests
import time
import random
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime
import warnings
import uuid

from src.core import IApiClient, IScraper, IRepository, ScrapingConfig, SalaryData, Reference

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)


class HabrApiClient(IApiClient):
    """Habr Career API client implementation"""

    def __init__(self, url: str, delay_min: float = 1.5, delay_max: float = 2.5, retry_attempts: int = 3):
        self.url = url
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.retry_attempts = retry_attempts

    def fetch_salary_data(self, **params) -> Optional[Dict[str, Any]]:
        """Fetch salary data from API"""
        api_params = {"employment_type": 0}

        # Map internal params to API params
        if 'spec_alias' in params:
            api_params["spec_aliases[]"] = params['spec_alias']
        if 'skill_aliases' in params:
            api_params["skills[]"] = params['skill_aliases']
        if 'region_alias' in params:
            api_params["region_aliases[]"] = params['region_alias']
        if 'company_alias' in params:
            api_params["company_alias"] = params['company_alias']

        full_url = f"{self.url}?{urllib.parse.urlencode(api_params, doseq=True)}"

        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(self.url, params=api_params, verify=False)
                response.raise_for_status()
                data = response.json()

                # Validate response
                if not data.get('groups') or len(data['groups']) == 0:
                    print(f"Warning: Empty response for {full_url}")
                    return None

                # Add delay between requests
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                return data

            except Exception as e:
                print(f"API error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.delay_max)

        return None


class SalaryScraper(IScraper):
    """Main scraper implementation"""

    def __init__(self, repository: IRepository, api_client: IApiClient):
        self.repository = repository
        self.api_client = api_client

    def scrape(self, config: ScrapingConfig) -> bool:
        """Execute scraping based on configuration"""
        transaction_id = str(uuid.uuid4())
        total_count = 0
        success_count = 0

        try:
            if config.combinations:
                # Scrape specific combinations
                print(f"Scraping combinations: {config.combinations}")
                for combination in config.combinations:
                    count, success = self._scrape_combination(combination, transaction_id)
                    total_count += count
                    success_count += success
            else:
                # Scrape individual reference types
                print(f"Scraping individual references: {config.reference_types}")
                for ref_type in config.reference_types:
                    count, success = self._scrape_reference_type(ref_type, transaction_id)
                    total_count += count
                    success_count += success

            # Commit if any work was done
            if total_count == 0:
                print("No data to scrape")
                return True
            else:
                self.repository.commit_transaction(transaction_id)
                print(f"Scraping completed: {success_count}/{total_count} successful")
                return True

        except Exception as e:
            self.repository.rollback_transaction(transaction_id)
            print(f"Critical error during scraping: {e}")
            return False

    def _scrape_reference_type(self, ref_type: str, transaction_id: str) -> tuple[int, int]:
        """Scrape single reference type"""
        references = self.repository.get_references(ref_type)
        total = len(references)
        success = 0

        print(f"Processing {total} {ref_type}")

        for i, ref in enumerate(references):
            params = self._build_params(ref_type, ref)
            data = self.api_client.fetch_salary_data(**params)

            if data:
                salary_data = SalaryData(data=data, reference_id=ref.id, reference_type=ref_type)
                self.repository.save_report(salary_data, transaction_id)
                success += 1

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{total} ({success} successful)")

        return total, success

    def _scrape_combination(self, combination: tuple, transaction_id: str) -> tuple[int, int]:
        """Scrape specific combination from CSV row"""
        print(f"Processing combination: {combination}")

        # New format: (('skills', 'Python'), ('regions', 'Moscow'))
        combined_params = {}
        ref_data = []

        try:
            for ref_type, value in combination:
                # Find reference by alias/title
                references = self.repository.get_references(ref_type)

                # Look for reference by alias first, then by title
                found_ref = None
                for ref in references:
                    if ref.alias.lower() == value.lower() or ref.title.lower() == value.lower():
                        found_ref = ref
                        break

                if not found_ref:
                    print(f"Reference not found: {ref_type}={value}")
                    return 0, 0

                # Build API parameters
                params = self._build_params(ref_type, found_ref)
                combined_params.update(params)
                ref_data.append((ref_type, found_ref))

            # Call API once with combined parameters
            print(f"API call: {', '.join(f'{rt}={ref.title}' for rt, ref in ref_data)}")
            data = self.api_client.fetch_salary_data(**combined_params)

            if data:
                # Save data for each reference type in the combination
                for ref_type, ref in ref_data:
                    salary_data = SalaryData(data=data, reference_id=ref.id, reference_type=ref_type)
                    self.repository.save_report(salary_data, transaction_id)

                return 1, 1  # 1 combination processed, 1 successful
            else:
                return 1, 0  # 1 combination processed, 0 successful

        except Exception as e:
            print(f"Error processing combination: {e}")
            return 1, 0

    def _build_params(self, ref_type: str, ref: Reference) -> Dict[str, Any]:
        """Build API parameters based on reference type"""
        param_mapping = {
            'specializations': ('spec_alias', ref.alias),
            'skills': ('skill_aliases', [ref.alias]),
            'regions': ('region_alias', ref.alias),
            'companies': ('company_alias', ref.alias),
        }

        param_name, param_value = param_mapping.get(ref_type, (None, None))
        if param_name:
            return {param_name: param_value}
        return {}
