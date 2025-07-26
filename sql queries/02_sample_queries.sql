-- Последние зарплаты по навыку и региону
SELECT 
    s.title as skill,
    r.title as region,
    rp.data->>'salary_from' as salary_from,
    rp.data->>'salary_to' as salary_to,
    rp.data->>'currency' as currency,
    rp.fetched_at
FROM reports rp
JOIN skills s ON s.id = rp.skills_1
JOIN regions r ON r.id = rp.region_id
WHERE s.alias = 'python' 
AND r.alias = 'moscow'
ORDER BY rp.fetched_at DESC
LIMIT 10;

-- Средние зарплаты по регионам
SELECT 
    r.title as region,
    COUNT(*) as total_vacancies,
    ROUND(AVG((rp.data->>'salary_from')::numeric)) as avg_salary_from,
    ROUND(AVG((rp.data->>'salary_to')::numeric)) as avg_salary_to,
    MAX(rp.fetched_at) as last_update
FROM reports rp
JOIN regions r ON r.id = rp.region_id
WHERE rp.data->>'currency' = 'RUB'
AND rp.fetched_at >= NOW() - INTERVAL '30 days'
GROUP BY r.title
ORDER BY avg_salary_from DESC;

-- Топ навыков по количеству вакансий
SELECT 
    s.title as skill,
    COUNT(*) as vacancies_count,
    ROUND(AVG((rp.data->>'salary_from')::numeric)) as avg_salary_from,
    ROUND(AVG((rp.data->>'salary_to')::numeric)) as avg_salary_to
FROM reports rp
JOIN skills s ON s.id = rp.skills_1
WHERE rp.data->>'currency' = 'RUB'
AND rp.fetched_at >= NOW() - INTERVAL '30 days'
GROUP BY s.title
HAVING COUNT(*) > 10
ORDER BY vacancies_count DESC
LIMIT 20;

-- Статистика по специализациям
SELECT 
    sp.title as specialization,
    COUNT(*) as total_vacancies,
    COUNT(DISTINCT rp.company_id) as unique_companies,
    ROUND(AVG((rp.data->>'salary_from')::numeric)) as avg_salary_from,
    ROUND(AVG((rp.data->>'salary_to')::numeric)) as avg_salary_to,
    MAX(rp.fetched_at) as last_update
FROM reports rp
JOIN specializations sp ON sp.id = rp.specialization_id
WHERE rp.data->>'currency' = 'RUB'
AND rp.fetched_at >= NOW() - INTERVAL '30 days'
GROUP BY sp.title
ORDER BY total_vacancies DESC;

-- Динамика зарплат по месяцам
SELECT 
    DATE_TRUNC('month', rp.fetched_at) as month,
    s.title as skill,
    COUNT(*) as vacancies_count,
    ROUND(AVG((rp.data->>'salary_from')::numeric)) as avg_salary_from,
    ROUND(AVG((rp.data->>'salary_to')::numeric)) as avg_salary_to
FROM reports rp
JOIN skills s ON s.id = rp.skills_1
WHERE rp.data->>'currency' = 'RUB'
AND rp.fetched_at >= NOW() - INTERVAL '12 months'
AND s.alias IN ('python', 'java', 'javascript')
GROUP BY month, s.title
ORDER BY month DESC, avg_salary_from DESC;

-- Статистика по успешности скрапинга
SELECT 
    DATE_TRUNC('day', report_date) as day,
    COUNT(*) as total_runs,
    SUM(total_variants) as total_variants,
    SUM(success_count) as success_count,
    ROUND(AVG(duration_seconds)) as avg_duration,
    STRING_AGG(DISTINCT status, ', ') as statuses
FROM report_log
WHERE report_date >= NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day DESC; 