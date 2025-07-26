-- Сводный отчет по типам справочников
-- Показывает среднюю медианную зарплату по каждому типу

SELECT 
    'Навыки' AS тип_справочника,
    COUNT(*) AS количество_записей,
    ROUND(AVG((group_data->>'median')::INTEGER)) AS средняя_медиана,
    MIN((group_data->>'median')::INTEGER) AS мин_медиана,
    MAX((group_data->>'median')::INTEGER) AS макс_медиана,
    MAX(r.fetched_at::DATE) AS последнее_обновление
FROM reports r
LEFT JOIN skills sk ON r.skills_1 = sk.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data
WHERE sk.id IS NOT NULL 
  AND (group_data->>'median')::INTEGER > 0
  AND r.fetched_at >= NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'Регионы' AS тип_справочника,
    COUNT(*) AS количество_записей,
    ROUND(AVG((group_data->>'median')::INTEGER)) AS средняя_медиана,
    MIN((group_data->>'median')::INTEGER) AS мин_медиана,
    MAX((group_data->>'median')::INTEGER) AS макс_медиана,
    MAX(r.fetched_at::DATE) AS последнее_обновление
FROM reports r
LEFT JOIN regions rg ON r.region_id = rg.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data
WHERE rg.id IS NOT NULL 
  AND (group_data->>'median')::INTEGER > 0
  AND r.fetched_at >= NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'Специализации' AS тип_справочника,
    COUNT(*) AS количество_записей,
    ROUND(AVG((group_data->>'median')::INTEGER)) AS средняя_медиана,
    MIN((group_data->>'median')::INTEGER) AS мин_медиана,
    MAX((group_data->>'median')::INTEGER) AS макс_медиана,
    MAX(r.fetched_at::DATE) AS последнее_обновление
FROM reports r
LEFT JOIN specializations s ON r.specialization_id = s.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data
WHERE s.id IS NOT NULL 
  AND (group_data->>'median')::INTEGER > 0
  AND r.fetched_at >= NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'Компании' AS тип_справочника,
    COUNT(*) AS количество_записей,
    ROUND(AVG((group_data->>'median')::INTEGER)) AS средняя_медиана,
    MIN((group_data->>'median')::INTEGER) AS мин_медиана,
    MAX((group_data->>'median')::INTEGER) AS макс_медиана,
    MAX(r.fetched_at::DATE) AS последнее_обновление
FROM reports r
LEFT JOIN companies c ON r.company_id = c.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data
WHERE c.id IS NOT NULL 
  AND (group_data->>'median')::INTEGER > 0
  AND r.fetched_at >= NOW() - INTERVAL '7 days'

ORDER BY средняя_медиана DESC; 