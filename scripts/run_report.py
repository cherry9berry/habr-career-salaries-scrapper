import os
import sys
from datetime import datetime
import psycopg2


SQL_REPORT = """
SELECT
    rg.title AS "Регион",
    sk.title AS "Навык",
    group_data->>'name'  AS "Уровень",
    group_data->>'title' AS "Описание",
    (group_data->>'total')::INTEGER  AS "Всего вакансий",
    (group_data->>'median')::INTEGER AS "Медианная зарплата",
    (group_data->>'min')::INTEGER    AS "Мин зарплата",
    (group_data->>'max')::INTEGER    AS "Макс зарплата",
    (group_data->'salary'->>'value')::INTEGER AS "Базовая зарплата",
    (group_data->'salary'->>'bonus')::INTEGER AS "Бонус",
    r.fetched_at                      AS "Собрано в",

    FIRST_VALUE((group_data->>'median')::INTEGER) OVER (
        PARTITION BY group_data->>'name'
        ORDER BY CASE WHEN rg.title = 'Москва' THEN 0 ELSE 1 END
        ROWS UNBOUNDED PRECEDING
    ) AS "Медиана в Москве",

    CASE
        WHEN rg.title != 'Москва' THEN
            ROUND(
                (((group_data->>'median')::INTEGER - 
                  FIRST_VALUE((group_data->>'median')::INTEGER) OVER (
                      PARTITION BY group_data->>'name'
                      ORDER BY CASE WHEN rg.title = 'Москва' THEN 0 ELSE 1 END
                      ROWS UNBOUNDED PRECEDING
                  )) * 100.0 /
                  FIRST_VALUE((group_data->>'median')::INTEGER) OVER (
                      PARTITION BY group_data->>'name'
                      ORDER BY CASE WHEN rg.title = 'Москва' THEN 0 ELSE 1 END
                      ROWS UNBOUNDED PRECEDING
                  )), 1
            )
        ELSE 0
    END AS "Разница с Москвой (%)"

FROM reports r
JOIN regions rg ON r.region_id = rg.id
LEFT JOIN skills  sk ON r.skills_1 = sk.id
CROSS JOIN jsonb_array_elements(r.data->'groups') AS group_data
WHERE r.region_id IS NOT NULL
  AND r.fetched_at >= %(start_ts)s
  AND r.fetched_at <  %(end_ts)s
  AND (group_data->>'total')::INTEGER > 0
ORDER BY
    group_data->>'name',
    CASE WHEN rg.title = 'Москва' THEN 0 ELSE 1 END,
    (group_data->>'median')::INTEGER DESC
LIMIT 200;
"""


def main() -> int:
    # Expect start and end as 'YYYY-MM-DD HH:MM:SS'
    if len(sys.argv) != 3:
        print("Usage: python scripts/run_report.py 'YYYY-MM-DD HH:MM:SS' 'YYYY-MM-DD HH:MM:SS'", file=sys.stderr)
        return 2

    start_raw = sys.argv[1]
    end_raw = sys.argv[2]

    try:
        # Validate format
        datetime.strptime(start_raw, "%Y-%m-%d %H:%M:%S")
        datetime.strptime(end_raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print("Invalid datetime format. Use YYYY-MM-DD HH:MM:SS", file=sys.stderr)
        return 2

    host = os.getenv("DATABASE_HOST")
    port = int(os.getenv("DATABASE_PORT", "5432"))
    dbname = os.getenv("DATABASE_NAME", "postgres")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")

    if not all([host, user, password]):
        print("Missing env vars: DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD", file=sys.stderr)
        return 2

    conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    cur = conn.cursor()

    # Diagnostics
    cur.execute("SELECT current_setting('TimeZone'), NOW()::timestamp, MIN(fetched_at), MAX(fetched_at) FROM reports")
    tz, now_ts, min_ts, max_ts = cur.fetchone()
    print(f"TimeZone={tz}, now={now_ts}, reports range=[{min_ts} .. {max_ts}]\n")

    params = {"start_ts": start_raw, "end_ts": end_raw}
    cur.execute(SQL_REPORT, params)
    rows = cur.fetchall()

    if not rows:
        print("No rows in interval. Try widening the time window or adjust for server timezone.")
    else:
        # Print header
        cols = [d[0] for d in cur.description]
        print("\t".join(cols))
        for row in rows[:50]:
            print("\t".join(str(x) if x is not None else '' for x in row))

    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
