-- ТОП-20 самых высоких медианных зарплат
-- Простой и понятный отчет

SELECT 
    -- Что именно (навык, регион, специализация, компания)
    COALESCE(
        'Навык: ' || sk.title,
        'Регион: ' || rg.title, 
        'Специализация: ' || s.title,
        'Компания: ' || c.title,
        'Общее'
    ) AS категория,
    
    -- Зарплатная вилка
    FORMAT('%s - %s руб', 
        TO_CHAR((group_data->>'min')::INTEGER, 'FM999,999,999'),
        TO_CHAR((group_data->>'max')::INTEGER, 'FM999,999,999')
    ) AS вилка,
    
    -- Медианная зарплата (основной показатель)
    TO_CHAR((group_data->>'median')::INTEGER, 'FM999,999,999') || ' руб' AS медиана,
    
    -- Количество вакансий
    (group_data->>'total')::INTEGER AS вакансий,
    
    -- Когда собрано
    TO_CHAR(r.fetched_at, 'DD.MM.YYYY HH24:MI') AS собрано
    
FROM reports r
LEFT JOIN skills sk ON r.skills_1 = sk.id
LEFT JOIN regions rg ON r.region_id = rg.id  
LEFT JOIN specializations s ON r.specialization_id = s.id
LEFT JOIN companies c ON r.company_id = c.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data

-- Фильтры
WHERE (group_data->>'median')::INTEGER > 50000  -- Минимум 50к руб
  AND (group_data->>'total')::INTEGER >= 5      -- Минимум 5 вакансий
  AND r.fetched_at >= NOW() - INTERVAL '7 days'  -- За последнюю неделю

-- Сортировка по медиане (самые высокие сверху)
ORDER BY (group_data->>'median')::INTEGER DESC

-- Только топ-20
LIMIT 20; 