"""
Build site/data.json from India occupation stats and India exposure scores.

Inputs:
- india/output/occupations_india.csv
- india/output/scores_india.json (optional)

Output:
- site/data.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


INDIA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = INDIA_DIR / "output"
STATS_PATH = OUTPUT_DIR / "occupations_india.csv"
SCORES_PATH = OUTPUT_DIR / "scores_india.json"
SITE_DATA_PATH = INDIA_DIR.parent / "site" / "data.json"
NCO_DIVISION_NAMES = {
    "1": "Managers",
    "2": "Professionals",
    "3": "Technicians",
    "4": "Clerical Support",
    "5": "Service and Sales",
    "6": "Agriculture and Fishery",
    "7": "Craft and Trades",
    "8": "Plant and Machine Ops",
    "9": "Elementary",
}


def parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def load_stats_rows() -> list[dict[str, str]]:
    with STATS_PATH.open() as handle:
        return list(csv.DictReader(handle))


def load_scores() -> dict[str, dict[str, object]]:
    if not SCORES_PATH.exists():
        return {}
    with SCORES_PATH.open() as handle:
        rows = json.load(handle)
    return {row["slug"]: row for row in rows}


def build_site_rows(
    stats_rows: list[dict[str, str]],
    scores: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    data: list[dict[str, object]] = []
    for row in stats_rows:
        score = scores.get(row["slug"], {})
        data.append(
            {
                "title": row["title"],
                "slug": row["slug"],
                "category": row.get("category", ""),
                "nco_division_code": row.get("pay_division_code", ""),
                "nco_division_name": NCO_DIVISION_NAMES.get(row.get("pay_division_code", ""), ""),
                "pay": parse_int(row.get("pay_annual")),
                "pay_monthly": parse_int(row.get("pay_monthly")),
                "jobs": parse_int(row.get("jobs")),
                "employment_share": parse_float(row.get("employment_share")),
                "education": row.get("education", ""),
                "education_bucket": row.get("education_bucket", ""),
                "education_source_url": row.get("education_source_url", ""),
                "education_source_type": row.get("education_source_type", ""),
                "exposure": score.get("exposure"),
                "exposure_rationale": score.get("rationale"),
                "url": row.get("url", ""),
            }
        )
    return data


def main() -> None:
    stats_rows = load_stats_rows()
    scores = load_scores()
    data = build_site_rows(stats_rows, scores)

    SITE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SITE_DATA_PATH.open("w") as handle:
        json.dump(data, handle)

    score_count = sum(1 for row in data if row["exposure"] is not None)
    print(f"Wrote {len(data)} occupations to {SITE_DATA_PATH.relative_to(INDIA_DIR.parent)}")
    print(f"Rows with exposure scores: {score_count}")


if __name__ == "__main__":
    main()
