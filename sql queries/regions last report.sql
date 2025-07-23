SELECT
    rg.title AS region_title,
    rg.alias AS region_alias,
    group_data->>'name' AS group_name,
    group_data->>'title' AS group_title,
    (group_data->>'total')::INTEGER AS total,
    (group_data->>'median')::INTEGER AS median,
    (group_data->>'min')::INTEGER AS min,
    (group_data->>'max')::INTEGER AS max,
    (group_data->>'p25')::INTEGER AS p25,
    (group_data->>'p75')::INTEGER AS p75,
    (group_data->'salary'->>'bonus')::INTEGER AS salary_bonus,
    (group_data->'salary'->>'total')::INTEGER AS salary_total,
    (group_data->'salary'->>'value')::INTEGER AS salary_value,
    (group_data->'salary'->>'bonusPercent')::INTEGER AS bonus_percent,
    r.fetched_at
FROM reports r
JOIN regions rg ON r.region_id = rg.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data
WHERE r.region_id IS NOT NULL
  AND r.fetched_at = (SELECT MAX(fetched_at) FROM reports WHERE region_id IS NOT NULL)
ORDER BY rg.id, r.fetched_at DESC, group_data->>'name';