-- Простой отчет по зарплатам (только основные данные)
-- Показывает все уровни для каждого параметра

SELECT 
    -- Что анализировали
    COALESCE(sk.title, rg.title, s.title, c.title, 'Общее') AS параметр,
    
    -- Уровень специалиста
    group_data->>'name' AS уровень,
    
    -- Медианная зарплата
    TO_CHAR((group_data->>'median')::INTEGER, 'FM999,999,999') AS медиана_руб,
    
    -- Вилка зарплат  
    TO_CHAR((group_data->>'min')::INTEGER, 'FM999,999,999') || ' - ' || 
    TO_CHAR((group_data->>'max')::INTEGER, 'FM999,999,999') AS вилка_руб,
    
    -- Количество вакансий
    (group_data->>'total')::INTEGER AS вакансий,
    
    -- Когда собрано
    r.fetched_at::DATE AS дата
    
FROM reports r
LEFT JOIN skills sk ON r.skills_1 = sk.id  
LEFT JOIN regions rg ON r.region_id = rg.id
LEFT JOIN specializations s ON r.specialization_id = s.id
LEFT JOIN companies c ON r.company_id = c.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data

WHERE r.fetched_at >= NOW() - INTERVAL '7 days'
  AND (group_data->>'total')::INTEGER > 0

ORDER BY 
    параметр,
    CASE group_data->>'name'
        WHEN 'Lead' THEN 1
        WHEN 'Senior' THEN 2  
        WHEN 'Middle' THEN 3
        WHEN 'Junior' THEN 4
        WHEN 'Intern' THEN 5
        WHEN 'All' THEN 6
        ELSE 7
    END; 