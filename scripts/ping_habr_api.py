import requests
from typing import Dict, Any


URL = "https://career.habr.com/api/frontend_v1/salary_calculator/general_graph"


def call_api(params: Dict[str, Any]) -> int | None:
    try:
        resp = requests.get(URL, params=params, headers={"User-Agent": "scraper-diag/1.0"}, timeout=20, verify=False)
        resp.raise_for_status()
        data = resp.json()
        groups = data.get("groups") or []
        if not groups:
            return None
        return int(groups[0].get("median") or 0)
    except Exception:
        return None


def main() -> int:
    aliases = ["c_678", "c_679", "r_14081"]
    variants = [
        ("region_aliases[]", lambda a: a),
        ("region_aliases", lambda a: [a]),
        ("region_alias", lambda a: a),
    ]

    print("Testing Habr API param mappings for regions:\n")
    for alias in aliases:
        print(f"Alias: {alias}")
        for key, val_fn in variants:
            params = {"employment_type": 0, key: val_fn(alias)}
            median = call_api(params)
            print(f"  {key}: median={median}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
