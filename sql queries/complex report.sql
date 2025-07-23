SELECT
    r.id,
    COALESCE(s.title, 'any') AS specialization_title,
    COALESCE(s.alias, 'any') AS specialization_alias,
    COALESCE(sk1.title, 'any') AS skill_1_title,
    COALESCE(sk1.alias, 'any') AS skill_1_alias,
    COALESCE(sk2.title, 'any') AS skill_2_title,
    COALESCE(sk2.alias, 'any') AS skill_2_alias,
    COALESCE(sk3.title, 'any') AS skill_3_title,
    COALESCE(sk3.alias, 'any') AS skill_3_alias,
    COALESCE(rg.title, 'any') AS region_title,
    COALESCE(rg.alias, 'any') AS region_alias,
    COALESCE(c.title, 'any') AS company_title,
    COALESCE(c.alias, 'any') AS company_alias,
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
LEFT JOIN specializations s ON r.specialization_id = s.id
LEFT JOIN skills sk1 ON r.skills_1 = sk1.id
LEFT JOIN skills sk2 ON r.skills_2 = sk2.id
LEFT JOIN skills sk3 ON r.skills_3 = sk3.id
LEFT JOIN regions rg ON r.region_id = rg.id
LEFT JOIN companies c ON r.company_id = c.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data
WHERE r.fetched_at = (SELECT MAX(fetched_at) FROM reports)
ORDER BY r.id, group_data->>'name';