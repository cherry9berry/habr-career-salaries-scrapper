"""
Core classes and interfaces for salary scraper following SOLID principles
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json


@dataclass
class Reference:
    """Value object for reference data"""
    id: int
    title: str
    alias: str
    
    
@dataclass
class SalaryData:
    """Value object for salary API response"""
    data: Dict[str, Any]
    reference_id: int
    reference_type: str
    

@dataclass
class ScrapingConfig:
    """Configuration for scraping task"""
    reference_types: List[str]  # ['specializations', 'skills', 'regions', 'companies']
    combinations: Optional[List[Tuple[str, ...]]] = None  # [('skills', 'regions'), ...]
    

class IRepository(ABC):
    """Repository interface (Repository pattern)"""
    
    @abstractmethod
    def get_references(self, table_name: str, limit: int = 2000) -> List[Reference]:
        """Get references from database"""
        pass
        
    @abstractmethod
    def save_report(self, data: SalaryData, transaction_id: str) -> bool:
        """Save report to database"""
        pass
        
    @abstractmethod
    def commit_transaction(self, transaction_id: str) -> None:
        """Commit all changes for transaction"""
        pass
        
    @abstractmethod
    def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback transaction on error"""
        pass


class IApiClient(ABC):
    """API client interface"""
    
    @abstractmethod
    def fetch_salary_data(self, **params) -> Optional[Dict[str, Any]]:
        """Fetch salary data from API"""
        pass


class IScraper(ABC):
    """Scraper interface"""
    
    @abstractmethod
    def scrape(self, config: ScrapingConfig) -> bool:
        """Execute scraping based on configuration"""
        pass


class IConfigParser(ABC):
    """Configuration parser interface"""
    
    @abstractmethod
    def parse(self, source: str) -> ScrapingConfig:
        """Parse configuration from source"""
        pass 