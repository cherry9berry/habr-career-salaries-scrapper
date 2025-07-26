# Habr Career Salary Scraper

A production-ready salary data scraper for Habr Career with REST API, CI/CD pipeline, and cloud deployment.

## 🚀 Live Demo

**API is running at:** https://habr-career-salaries-scrapper.onrender.com/

### Quick Start Examples

```bash
# Check API health
curl https://habr-career-salaries-scrapper.onrender.com/health

# Start full scraping (all reference types)
curl -X POST https://habr-career-salaries-scrapper.onrender.com/api/scrape

# Upload custom CSV configuration
curl -X POST -F 'config=@config.csv' https://habr-career-salaries-scrapper.onrender.com/api/scrape/upload

# Check scraping status
curl https://habr-career-salaries-scrapper.onrender.com/api/status
```

**API Documentation:**
- Swagger UI: https://habr-career-salaries-scrapper.onrender.com/docs
- ReDoc: https://habr-career-salaries-scrapper.onrender.com/redoc

## 🏗️ Architecture

### Project Structure
```
salary_scrapping/
├── src/                    # Core application code
│   ├── api/               # REST API (FastAPI)
│   ├── core.py            # Interfaces and DTOs (SOLID principles)
│   ├── database.py        # PostgreSQL repository implementation
│   ├── scraper.py         # Habr API client and scraping logic
│   ├── async_*.py         # Async versions for parallel scraping
│   ├── config_parser.py   # CSV configuration parsing
│   ├── settings.py        # YAML/env configuration loading
│   └── sqlite_storage.py  # Alternative SQLite temp storage
├── tests/                 # Test suite (71 tests, 68% coverage)
│   ├── unit/             # Unit tests for each module
│   └── integration/      # End-to-end integration tests
├── sql queries/          # SQL report templates
├── examples/             # Example CSV configurations
├── main.py               # CLI entry point
├── run_api.py            # API server entry point
└── config.yaml           # Database and API configuration
```

### Key Design Principles
- **SOLID principles** - Single responsibility, dependency injection
- **Repository pattern** - Database abstraction layer
- **Interface segregation** - Clean contracts for each component
- **Temporary storage** - SQLite files instead of RAM for reliability
- **Async support** - Both sync and async implementations

## 💾 Data Storage Strategy

### Temporary Storage During Scraping
- **SQLite files** (default) - Reliable, file-based, no extra connections
- **PostgreSQL temp tables** (optional) - Same DB transactions, auto cleanup

### Permanent Storage
- **PostgreSQL** (Supabase) - All scraped salary data and references
- **Reference tables**: specializations (165), skills (1,572), regions (93), companies (467)
- **Reports table**: JSON salary data with timestamps

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| GET | `/health` | Health check and database status |
| GET | `/api/status` | Current scraping job status |
| POST | `/api/scrape` | Start full scraping (all references) |
| POST | `/api/scrape/upload` | Upload CSV config and start custom scraping |
| GET | `/docs` | Interactive Swagger documentation |
| GET | `/redoc` | Alternative API documentation |

### API Features
- **Concurrent job prevention** - Only one scraping job at a time
- **Background processing** - Non-blocking async execution
- **File upload support** - Multipart form data for CSV configs
- **Automatic retries** - Built-in retry logic for API calls
- **Rate limiting** - Configurable delays between requests

## 🚀 Deployment

### Current Infrastructure
- **API hosting**: Render.com (free tier)
- **Database**: Supabase PostgreSQL (free tier)
- **CI/CD**: GitHub Actions
- **Monitoring**: Built-in health checks and status endpoints

### Environment Variables
```env
# Database connection (Supabase)
DATABASE_HOST=aws-0-eu-central-1.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres.cehitgienxwzplcxbfdk
DATABASE_PASSWORD=your_password

# API configuration
API_URL=https://career.habr.com/api/frontend_v1/salary_calculator/general_graph
API_DELAY_MIN=1.5
API_DELAY_MAX=2.5

# Storage type (optional)
USE_SQLITE_TEMP=true  # or false for PostgreSQL temp tables
```

## 🧪 Local Development

### Prerequisites
- Python 3.9+
- PostgreSQL (or use Docker)
- pip or Poetry

### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/your-username/salary_scrapping.git
cd salary_scrapping

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure database (edit config.yaml)
# Or use environment variables

# 4. Run API server
python run_api.py
# API available at http://localhost:8000

# 5. Or use CLI version
python main.py                    # Scrape all references
python main.py config.csv         # Use custom CSV config
```

### Docker Setup
```bash
# Start PostgreSQL + API
docker-compose up

# API: http://localhost:8000
# PostgreSQL: localhost:5432
```

### Running Tests
```bash
# Run all tests
pytest

# With coverage report
pytest --cov=src --cov-report=html

# Run specific test category
python run_tests.py unit
python run_tests.py integration
```

### Code Quality
```bash
# Linting
ruff check src

# Formatting
black .

# Type checking
mypy src
```

## 📊 CSV Configuration Format

Create custom scraping configurations with CSV files:

```csv
skills,regions,specializations
python,c_678,backend
javascript,russian_capitals,frontend
docker,ekaterinburg,devops
```

Each row represents a combination to scrape. The scraper will:
1. Parse headers as reference types
2. Read each row as specific combinations
3. Make API calls for each combination
4. Save results to database

## 🔄 CI/CD Pipeline

GitHub Actions workflow on every push:
1. **Setup** - Python 3.9 environment
2. **Dependencies** - Install requirements
3. **Linting** - ruff, black, mypy checks
4. **Testing** - Run 71 tests with coverage
5. **Deploy** - Auto-deploy to Render.com on main branch

## 📈 SQL Reports

Pre-built SQL queries in `sql queries/` folder:
- `readable_report.sql` - Human-friendly salary report
- `summary_report.sql` - Aggregated statistics by type
- `top_salaries.sql` - Top 20 highest salaries
- `simple_report.sql` - Basic data overview

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Ensure all tests pass (`pytest`)
5. Check code quality (`ruff check`, `black .`, `mypy src`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

## 📝 License

This project is for educational purposes. Please respect Habr Career's terms of service when using this scraper.

## 🙏 Acknowledgments

- Built with FastAPI, PostgreSQL, and modern Python practices
- Deployed on Render.com and Supabase free tiers
- Inspired by the need for salary transparency in IT