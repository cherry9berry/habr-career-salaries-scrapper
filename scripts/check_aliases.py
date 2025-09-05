import os
import sys
import psycopg2


def main() -> int:
    host = os.getenv("DATABASE_HOST")
    port = int(os.getenv("DATABASE_PORT", "5432"))
    dbname = os.getenv("DATABASE_NAME", "postgres")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")

    if not all([host, user, password]):
        print("Missing required env vars: DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD", file=sys.stderr)
        return 2

    try:
        conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        return 3

    tables = [
        ("specializations", "Специализации"),
        ("skills", "Навыки"),
        ("regions", "Регионы"),
        ("companies", "Компании"),
    ]

    try:
        with conn.cursor() as cur:
            for table, title in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    total = cur.fetchone()[0]
                    cur.execute(f"SELECT title, alias FROM {table} ORDER BY alias LIMIT 20")
                    rows = cur.fetchall()
                    print(f"\n[{title}] {table}: total={total}")
                    for t, a in rows:
                        print(f"  - {a}\t({t})")
                except Exception as te:
                    print(f"\n[{title}] {table}: error: {te}")
        conn.close()
    except Exception as e:
        print(f"Query error: {e}", file=sys.stderr)
        return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())


