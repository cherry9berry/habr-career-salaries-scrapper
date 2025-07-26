-- Справочник специализаций
CREATE TABLE IF NOT EXISTS specializations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    alias VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Справочник навыков
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    alias VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Справочник регионов
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    alias VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Справочник компаний
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    alias VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Основная таблица с зарплатными данными
CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    specialization_id INTEGER REFERENCES specializations(id),
    skills_1 INTEGER REFERENCES skills(id),
    region_id INTEGER REFERENCES regions(id),
    company_id INTEGER REFERENCES companies(id),
    data JSONB NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Логи операций
CREATE TABLE IF NOT EXISTS report_log (
    id BIGSERIAL PRIMARY KEY,
    report_date TIMESTAMP NOT NULL DEFAULT NOW(),
    report_type VARCHAR(50) NOT NULL,
    total_variants INTEGER NOT NULL,
    success_count INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_reports_specialization ON reports(specialization_id);
CREATE INDEX IF NOT EXISTS idx_reports_skills ON reports(skills_1);
CREATE INDEX IF NOT EXISTS idx_reports_region ON reports(region_id);
CREATE INDEX IF NOT EXISTS idx_reports_company ON reports(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_fetched_at ON reports(fetched_at);

-- Индексы для поиска по справочникам
CREATE INDEX IF NOT EXISTS idx_specializations_alias ON specializations(alias);
CREATE INDEX IF NOT EXISTS idx_skills_alias ON skills(alias);
CREATE INDEX IF NOT EXISTS idx_regions_alias ON regions(alias);
CREATE INDEX IF NOT EXISTS idx_companies_alias ON companies(alias); 