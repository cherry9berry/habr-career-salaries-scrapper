import os
import sys
import csv
import argparse
import psycopg2


def main() -> int:
    parser = argparse.ArgumentParser(description="Export region aliases to CSV for scraper config")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=str, default="examples/regions_from_db.csv")
    parser.add_argument("--host", type=str, default=os.getenv("DATABASE_HOST"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DATABASE_PORT", "5432")))
    parser.add_argument("--dbname", type=str, default=os.getenv("DATABASE_NAME", "postgres"))
    parser.add_argument("--user", type=str, default=os.getenv("DATABASE_USER"))
    parser.add_argument("--password", type=str, default=os.getenv("DATABASE_PASSWORD"))
    args = parser.parse_args()

    host = args.host
    port = args.port
    dbname = args.dbname
    user = args.user
    password = args.password

    if not all([host, user, password]):
        print("Missing env vars: DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD", file=sys.stderr)
        return 2

    conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    cur = conn.cursor()
    cur.execute("SELECT alias FROM regions ORDER BY id LIMIT %s", (args.limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["regions"])
        for (alias,) in rows:
            writer.writerow([alias])

    print(f"Wrote {len(rows)} region aliases to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
