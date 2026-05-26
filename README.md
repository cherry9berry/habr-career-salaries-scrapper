# habr-career-salaries-scraper

Scraper for the Habr Career salary calculator API. Iterates through all entries in each reference dimension (specializations, skills, regions, companies), fetches salary distribution data per entry, and persists results to PostgreSQL.

Built as a data pipeline microservice: REST API for job control, structured storage for downstream BI queries.

## How it works

Habr Career exposes a salary calculator endpoint that returns percentile salary distributions filtered by a single dimension — specialization, skill, region, or company. This service:

1. Loads all reference entries from PostgreSQL (populated once via `03_initial_data.sql`)
2. Iterates through each dimension sequentially, fetching one entry at a time
3. Persists raw JSON response alongside reference FK and run metadata
4. Commits the entire batch atomically on success; rolls back on failure

Scraping is intentionally **sequential with randomized delays** — the target is a public frontend API, not a documented data endpoint. Parallel scraping would create disproportionate load and risk IP blocks.

## Architecture

```
src/
├── core.py            # Domain interfaces and value objects (IRepository, IApiClient, IScraper)
├── scraper.py         # Habr API client + scraping orchestration
├── database.py        # PostgreSQL repository (repository pattern)
├── config_parser.py   # Scraping scope configuration
├── settings.py        # Config loading: env vars → YAML fallback
└── api/
    └── app.py         # FastAPI: job control endpoints
```

Dependency injection via interfaces — storage backend is swappable by implementing `IRepository`.

## Data model

Reference tables (populated before first run):

| Table | Entries | Description |
|---|---|---|
| `specializations` | 165 | Job specializations |
| `skills` | 1,572 | Technical skills |
| `regions` | 93 | Geographic regions |
| `companies` | 467 | Companies |

Fact table:

```sql
reports (
    id              BIGSERIAL PRIMARY KEY,
    specialization_id INTEGER REFERENCES specializations(id),
    skill_id          INTEGER REFERENCES skills(id),
    region_id         INTEGER REFERENCES regions(id),
    company_id        INTEGER REFERENCES companies(id),
    data              JSONB NOT NULL,      -- raw API response
    fetched_at        TIMESTAMP NOT NULL
)
```

Each row stores the full API response for one reference entry. Salary percentiles (p25/p50/p75), sample size, and experience breakdowns are extracted from `data` at query time via SQL or Superset.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Database connectivity check |
| GET | `/api/status` | Current job state and job ID |
| POST | `/api/scrape` | Start a full scraping run |
| GET | `/docs` | OpenAPI spec (Swagger UI) |

Only one scraping job runs at a time. Subsequent `POST /api/scrape` requests return `409` while a job is active.

## Configuration

Environment variables (`.env` or host env):

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=salaries
DATABASE_USER=scraper
DATABASE_PASSWORD=...

API_DELAY_MIN=1.5
API_DELAY_MAX=2.5
API_RETRY_ATTEMPTS=3
```

Falls back to `config.yaml` if `DATABASE_HOST` is not set in environment.

## Running

**API server:**
```bash
pip install -r requirements.txt
python run_api.py
# http://localhost:8000
```

**CLI (one-shot run):**
```bash
python main.py
```

**Docker:**
```bash
docker-compose up
```

## Database setup

```bash
psql -d salaries -f "sql queries/01_create_tables.sql"
psql -d salaries -f "sql queries/03_initial_data.sql"
```

## BI / Superset

Connect Superset to the same PostgreSQL instance. Salary percentiles and experience distributions are extracted from the `data` JSONB column at query time — no additional ETL step required.

SQL view examples are in `sql queries/`.

## Tests

```bash
pytest --cov=src
```

## Stack

Python · FastAPI · PostgreSQL · psycopg2 · Docker