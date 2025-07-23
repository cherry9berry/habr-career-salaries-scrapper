"""
Salary scraper main entry point with new interface
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from src.database import PostgresRepository
from src.scraper import HabrApiClient, SalaryScraper
from src.config_parser import CsvConfigParser, DefaultConfigParser


def load_config() -> dict:
    """Load application configuration"""
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Salary data scraper - scrape salary data from Habr Career API",
        epilog="""
Examples:
  python main.py                    # Scrape all reference types individually
  python main.py config.csv         # Use CSV file for configuration
  
CSV file format:
  First row should contain headers: specializations,skills,regions,companies
  Use only the headers you need for your scraping task
        """
    )
    
    parser.add_argument(
        "config_file",
        nargs="?",
        help="CSV configuration file (optional). If not provided, scrapes all reference types individually"
    )
    
    return parser.parse_args()


def main():
    """Main application entry point"""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Load app configuration
        config = load_config()
        
        print(f"Salary scraper started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Parse scraping configuration
        if args.config_file:
            if not args.config_file.endswith('.csv'):
                print(f"Error: Configuration file must be a CSV file, got: {args.config_file}")
                sys.exit(1)
                
            print(f"Using configuration from: {args.config_file}")
            config_parser = CsvConfigParser()
            scraping_config = config_parser.parse(args.config_file)
        else:
            print("Using default configuration (all reference types)")
            config_parser = DefaultConfigParser()
            scraping_config = config_parser.parse()
            
        # Initialize components
        repository = PostgresRepository(config["database"])
        api_client = HabrApiClient(
            url=config["api"]["url"],
            delay_min=config["api"]["delay_min"],
            delay_max=config["api"]["delay_max"],
            retry_attempts=config["api"]["retry_attempts"]
        )
        scraper = SalaryScraper(repository, api_client)
        
        # Execute scraping
        print(f"Configuration: {scraping_config.reference_types}")
        if scraping_config.combinations:
            print(f"Combinations: {scraping_config.combinations}")
            
        success = scraper.scrape(scraping_config)
        
        if success:
            print("Scraping completed successfully")
            sys.exit(0)
        else:
            print("Scraping failed")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()