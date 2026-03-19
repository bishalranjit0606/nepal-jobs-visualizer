"""
Build nepal/site/data.json from the Nepal occupations dataset.

Input:  data/occupations_data.json   (NSCO-based, AI exposure scored)
Output: nepal/site/data.json          (visualizer-ready schema)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "occupations_data.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "site" / "data.json"

# Map NSCO first digit → sector label (mirrors India's NCO division approach)
NSCO_SECTOR_MAP = {
    "0": "Armed Forces",
    "1": "Managers",
    "2": "Professionals",
    "3": "Technicians and Associates",
    "4": "Clerical Support",
    "5": "Service and Sales",
    "6": "Skilled Agricultural",
    "7": "Craft and Trades",
    "8": "Plant and Machine Operators",
    "9": "Elementary Occupations",
}

# Nepal education bucket mapping (aligned with NLFS/Census categories)
edu_bucket_map: dict[str, str] = {
    "None": "No formal education",
    "Basic Training": "No formal education",
    "Training": "Vocational / Training",
    "Vocational Training": "Vocational / Training",
    "Traditional Training": "Vocational / Training",
    "Apprenticeship": "Vocational / Training",
    "Professional License": "Vocational / Training",
    "SEE": "SEE (Grade 10)",
    "SEE / Training": "SEE (Grade 10)",
    "SEE / +2": "SEE (Grade 10)",
    "+2 (Proficiency Level)": "+2 / Proficiency",
    "+2 in Education": "+2 / Proficiency",
    "Diploma": "Diploma",
    "Diploma in IT": "Diploma",
    "Diploma in Health Science": "Diploma",
    "Diploma / +2": "Diploma",
    "Technical Training": "Diploma",
    "Bachelor's Degree": "Bachelor's Degree",
    "Bachelor's Degree / Talent": "Bachelor's Degree",
    "Bachelor of Laws (LLB)": "Bachelor's Degree",
    "Bachelor's in Nursing": "Bachelor's Degree",
    "MBBS": "Bachelor's Degree",
    "Master's Degree": "Master's Degree or above",
}


def get_category(nsco_code: str, sector: str) -> str:
    """Return the broad category for the treemap grouping."""
    first = nsco_code[0] if nsco_code else "9"
    return NSCO_SECTOR_MAP.get(first, sector)


def main() -> None:
    with INPUT_PATH.open() as fh:
        rows = json.load(fh)

    site_rows = []
    for idx, row in enumerate(rows, start=1):
        nsco_code = str(row.get("nsco_code", ""))
        edu_raw = row.get("min_education", "")
        edu_bucket = edu_bucket_map.get(edu_raw, edu_raw)

        # AI exposure score is 0.0-1.0; visualizer uses 0-10 integer scale
        raw_score = row.get("ai_exposure_score")
        exposure_int = round(raw_score * 10) if raw_score is not None else None

        monthly = row.get("avg_salary_npr", 0)
        annual = monthly * 12 if monthly else None

        site_rows.append(
            {
                "occupation_id": str(idx),
                "title": row["title"],
                "slug": row["title"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-"),
                "category": get_category(nsco_code, row.get("sector", "")),
                "nsco_division_code": nsco_code[0] if nsco_code else "",
                "nsco_division_name": NSCO_SECTOR_MAP.get(nsco_code[0], "") if nsco_code else "",
                "nsco_code": nsco_code,
                "pay": annual,
                "pay_monthly": monthly,
                "jobs": row.get("workforce_size"),
                "employment_share": None,
                "education": edu_raw,
                "education_bucket": edu_bucket,
                "sector": row.get("sector", ""),
                "exposure": exposure_int,
                "exposure_raw": raw_score,
                "exposure_rationale": row.get("rationale", ""),
                "url": "",  # Future: link to Shramsansar or NSCO page
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(site_rows, fh, ensure_ascii=False, indent=2)

    score_count = sum(1 for r in site_rows if r["exposure"] is not None)
    print(f"Wrote {len(site_rows)} occupations → {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"  With AI exposure scores: {score_count}")
    print(f"  Education buckets: {sorted(set(r['education_bucket'] for r in site_rows))}")


if __name__ == "__main__":
    main()
