-- Читаемый отчет по зарплатам (последние данные)
-- Показывает медианные зарплаты с названиями вместо ID

SELECT 
    -- Основная информация
    COALESCE(
        'Навык: ' || sk.title,
        'Регион: ' || rg.title, 
        'Специализация: ' || s.title,
        'Компания: ' || c.title,
        'Общее'
    ) AS тип_данных,
    
    -- Уровень (All, Senior, Middle, Junior, Lead, Intern)
    group_data->>'name' AS уровень,
    
    -- Полное описание из API
    group_data->>'title' AS описание,
    
    -- Зарплатная статистика (форматированная)
    TO_CHAR((group_data->>'median')::INTEGER, 'FM999,999,999') || ' ₽' AS медиана,
    TO_CHAR((group_data->>'min')::INTEGER, 'FM999,999,999') || ' ₽' AS минимум,
    TO_CHAR((group_data->>'max')::INTEGER, 'FM999,999,999') || ' ₽' AS максимум,
    
    -- Количество вакансий
    (group_data->>'total')::INTEGER AS вакансий,
    
    -- Процентили
    TO_CHAR((group_data->>'p25')::INTEGER, 'FM999,999,999') || ' ₽' AS процентиль_25,
    TO_CHAR((group_data->>'p75')::INTEGER, 'FM999,999,999') || ' ₽' AS процентиль_75,
    
    -- Детали зарплаты
    TO_CHAR((group_data->'salary'->>'value')::INTEGER, 'FM999,999,999') || ' ₽' AS базовая_зарплата,
    TO_CHAR((group_data->'salary'->>'bonus')::INTEGER, 'FM999,999,999') || ' ₽' AS бонус,
    (group_data->'salary'->>'bonusPercent')::INTEGER || '%' AS процент_бонуса,
    
    -- Дата сбора данных
    TO_CHAR(r.fetched_at, 'DD.MM.YYYY HH24:MI') AS дата_сбора
    
FROM reports r
-- Присоединяем справочники
LEFT JOIN specializations s ON r.specialization_id = s.id
LEFT JOIN skills sk ON r.skills_1 = sk.id  
LEFT JOIN regions rg ON r.region_id = rg.id
LEFT JOIN companies c ON r.company_id = c.id

-- Разворачиваем JSON с группами зарплат
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data

-- Только последние данные
WHERE r.fetched_at >= NOW() - INTERVAL '7 days'
  AND (group_data->>'median')::INTEGER > 0  -- Убираем пустые данные

-- Сортировка: сначала по типу данных, потом по медиане (по убыванию)
ORDER BY 
    CASE 
        WHEN sk.title IS NOT NULL THEN 1  -- Навыки
        WHEN s.title IS NOT NULL THEN 2   -- Специализации  
        WHEN rg.title IS NOT NULL THEN 3  -- Регионы
        WHEN c.title IS NOT NULL THEN 4   -- Компании
        ELSE 5 
    END,
    (group_data->>'median')::INTEGER DESC; 