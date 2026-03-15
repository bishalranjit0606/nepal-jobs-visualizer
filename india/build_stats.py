"""
Build normalized India occupation stats from cached PLFS annual report data.

Inputs:
- india/output/occupations_india.json
- india/output/education_india.json (optional)
- india/raw/plfs-annual-2023-24.txt or india/raw/plfs-annual-2023-24.pdf

Output:
- india/output/occupations_india.csv

The current stats layer is intentionally conservative:
- employment is represented as all-India worker share (%) by NCO-2015 3-digit
  occupation group from PLFS 2023-24 Table 25
- pay is represented as average monthly wage/salary by NCO-2015 1-digit
  occupation division from PLFS 2023-24 Table 50, then annualized
- direct occupation counts are not available in this first pass, so `jobs` remains
  blank and the frontend should size by `employment_share`
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path


INDIA_DIR = Path(__file__).resolve().parent
RAW_DIR = INDIA_DIR / "raw"
OUTPUT_DIR = INDIA_DIR / "output"
OCCUPATIONS_PATH = OUTPUT_DIR / "occupations_india.json"
EDUCATION_PATH = OUTPUT_DIR / "education_india.json"
OUTPUT_PATH = OUTPUT_DIR / "occupations_india.csv"
PLFS_TEXT_PATH = RAW_DIR / "plfs-annual-2023-24.txt"
PLFS_PDF_PATH = RAW_DIR / "plfs-annual-2023-24.pdf"
PLFS_SOURCE_URL = (
    "https://www.mospi.gov.in/sites/default/files/publication_reports/"
    "AnnualReport_PLFS2023-24L2.pdf"
)

TABLE25_START = (
    "Table (25): Percentage distribution of workers in usual status (ps+ss) by "
    "occupation group/ sub-division /division"
)
TABLE26_START = (
    "Table (26): Percentage distribution of usually working persons (ps+ss) by "
    "industry of work"
)
TABLE50_START = (
    "Table (50): Average wage/salary earnings (Rs.) during the preceding calendar "
    "month from regular wage/salaried employment among the regular wage salaried "
    "employees in"
)
TABLE51_START = (
    "Table (51): Average wage earnings (Rs.) per day from casual labour work by "
    "industry of work"
)
TABLE25_ROW_PATTERN = re.compile(
    r"^\s*(\d{3})\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+"
    r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*$",
    re.M,
)


def code_to_group_code(nco_code: str | None) -> str | None:
    digits = "".join(ch for ch in str(nco_code or "") if ch.isdigit())
    if len(digits) < 3:
        return None
    return digits[:3]


def code_to_division_code(nco_code: str | None) -> str | None:
    digits = "".join(ch for ch in str(nco_code or "") if ch.isdigit())
    if not digits:
        return None
    return digits[:1]


def extract_table25_group_shares(text: str) -> dict[str, float]:
    start = text.index(TABLE25_START)
    end = text.find(TABLE26_START, start)
    if end == -1:
        end = len(text)
    block = text[start:end]

    shares: dict[str, float] = {}
    for match in TABLE25_ROW_PATTERN.finditer(block):
        code = match.group(1)
        rural_urban_person = float(match.group(10))
        shares[code] = rural_urban_person
    return shares


def extract_table50_division_wages(text: str) -> dict[str, int]:
    start = text.index(TABLE50_START)
    end = text.find(TABLE51_START, start)
    if end == -1:
        end = len(text)
    block = text[start:end]

    marker = "rural+urban                      person"
    marker_index = block.rfind(marker)
    if marker_index == -1:
        raise ValueError("Could not find rural+urban person wage row in PLFS Table 50 block")

    tail = block[marker_index : marker_index + 1000]
    match = re.search(r"Average wage/salary earnings \(Rs\.\)\s+([0-9,\s]+)", tail)
    if not match:
        raise ValueError("Could not parse division wages from PLFS Table 50 block")

    numbers = re.findall(r"\d[\d,]*", match.group(1))
    if len(numbers) < 10:
        raise ValueError(f"Expected 10 wage values in PLFS Table 50 row, found {len(numbers)}")

    values = [int(value.replace(",", "")) for value in numbers[:10]]
    return {str(index): values[index - 1] for index in range(1, 10)}


def load_plfs_text() -> str:
    if PLFS_TEXT_PATH.exists():
        return PLFS_TEXT_PATH.read_text(errors="ignore")

    if not PLFS_PDF_PATH.exists():
        raise FileNotFoundError(
            "Missing cached PLFS source. Expected one of:\n"
            f"- {PLFS_TEXT_PATH}\n"
            f"- {PLFS_PDF_PATH}\n"
            f"Official source: {PLFS_SOURCE_URL}"
        )

    result = subprocess.run(
        ["pdftotext", "-layout", str(PLFS_PDF_PATH), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = result.stdout
    PLFS_TEXT_PATH.write_text(text)
    return text


def load_occupations() -> list[dict[str, object]]:
    return json.loads(OCCUPATIONS_PATH.read_text())


def load_education_by_slug() -> dict[str, dict[str, object]]:
    if not EDUCATION_PATH.exists():
        return {}
    rows = json.loads(EDUCATION_PATH.read_text())
    return {str(row["slug"]): row for row in rows}


def build_stats_rows(
    occupations: list[dict[str, object]],
    group_shares: dict[str, float],
    division_wages: dict[str, int],
    education_by_slug: dict[str, dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    education_by_slug = education_by_slug or {}
    group_counts: dict[str, int] = {}
    for occupation in occupations:
        group_code = code_to_group_code(str(occupation.get("nco_code") or ""))
        if group_code:
            group_counts[group_code] = group_counts.get(group_code, 0) + 1

    rows: list[dict[str, object]] = []
    for occupation in occupations:
        nco_code = occupation.get("nco_code")
        group_code = code_to_group_code(str(nco_code or ""))
        division_code = code_to_division_code(str(nco_code or ""))
        pay_monthly = division_wages.get(division_code or "")
        employment_share_group = group_shares.get(group_code or "")
        education = education_by_slug.get(str(occupation["slug"]), {})
        employment_share = employment_share_group
        if employment_share_group is not None and group_code:
            employment_share = employment_share_group / group_counts[group_code]
        ncs_id = occupation.get("ncs_id")
        url = ""
        if ncs_id:
            url = (
                "https://www.ncs.gov.in/content-repository/Pages/"
                f"ViewNcoDetails.aspx?COBID={ncs_id}"
            )

        rows.append(
            {
                "title": occupation["title"],
                "slug": occupation["slug"],
                "nco_code": nco_code or "",
                "category": occupation.get("category") or "",
                "jobs": "",
                "employment_share": employment_share if employment_share is not None else "",
                "employment_share_group": (
                    employment_share_group if employment_share_group is not None else ""
                ),
                "employment_group_code": group_code or "",
                "pay_monthly": pay_monthly if pay_monthly is not None else "",
                "pay_annual": (pay_monthly * 12) if pay_monthly is not None else "",
                "pay_division_code": division_code or "",
                "education": education.get("education", ""),
                "education_bucket": education.get("education_bucket", ""),
                "education_source_url": education.get("education_source_url", ""),
                "education_source_type": education.get("education_source_type", ""),
                "url": url,
            }
        )

    rows.sort(key=lambda row: (str(row["category"]), str(row["title"])))
    return rows


def main() -> None:
    occupations = load_occupations()
    education_by_slug = load_education_by_slug()
    plfs_text = load_plfs_text()
    group_shares = extract_table25_group_shares(plfs_text)
    division_wages = extract_table50_division_wages(plfs_text)
    rows = build_stats_rows(occupations, group_shares, division_wages, education_by_slug)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "title",
        "slug",
        "nco_code",
        "category",
        "jobs",
        "employment_share",
        "employment_share_group",
        "employment_group_code",
        "pay_monthly",
        "pay_annual",
        "pay_division_code",
        "education",
        "education_bucket",
        "education_source_url",
        "education_source_type",
        "url",
    ]
    with OUTPUT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    matched_shares = sum(1 for row in rows if row["employment_share"] != "")
    matched_pay = sum(1 for row in rows if row["pay_annual"] != "")
    matched_education = sum(1 for row in rows if row["education_bucket"] != "")
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH.relative_to(INDIA_DIR.parent)}")
    print(f"Employment share matched for {matched_shares} occupations")
    print(f"Pay matched for {matched_pay} occupations")
    print(f"Education matched for {matched_education} occupations")


if __name__ == "__main__":
    main()
