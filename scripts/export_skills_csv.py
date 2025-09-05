import os
import sys
import csv
import argparse
import psycopg2


def main() -> int:
    parser = argparse.ArgumentParser(description="Export skill aliases to CSV for scraper config")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=str, default="examples/skills_100.csv")
    parser.add_argument("--host", type=str, default=os.getenv("DATABASE_HOST"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DATABASE_PORT", "5432")))
    parser.add_argument("--dbname", type=str, default=os.getenv("DATABASE_NAME", "postgres"))
    parser.add_argument("--user", type=str, default=os.getenv("DATABASE_USER"))
    parser.add_argument("--password", type=str, default=os.getenv("DATABASE_PASSWORD"))
    args = parser.parse_args()

    if not all([args.host, args.user, args.password]):
        print("Missing DB params; set --host/--user/--password or env vars.", file=sys.stderr)
        return 2

    conn = psycopg2.connect(host=args.host, port=args.port, dbname=args.dbname, user=args.user, password=args.password)
    cur = conn.cursor()
    cur.execute("SELECT alias FROM skills ORDER BY id LIMIT %s", (args.limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["skills"])
        for (alias,) in rows:
            writer.writerow([alias])

    print(f"Wrote {len(rows)} skill aliases to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


