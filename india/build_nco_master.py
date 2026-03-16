"""
Build a normalized full NCO 2015 occupation master list from Vol II PDFs.

Inputs:
- india/raw/nco-2015-vol-2a.pdf
- india/raw/nco-2015-vol-2b.pdf

Output:
- india/output/occupations_nco_master.json
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path


INDIA_DIR = Path(__file__).resolve().parent
RAW_DIR = INDIA_DIR / "raw"
OUTPUT_PATH = INDIA_DIR / "output" / "occupations_nco_master.json"
VOL_2A_PATH = RAW_DIR / "nco-2015-vol-2a.pdf"
VOL_2B_PATH = RAW_DIR / "nco-2015-vol-2b.pdf"

DIVISION_NAMES = {
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

CODE_PATTERN = re.compile(r"^\d{4}\.\d{4}$")
HEADER_PREFIXES = (
    "National Classification of Occupations",
    "VOLUME II",
    "ISCO 08 Unit Group Details:",
    "Qualification Pack Details:",
)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text)
    return ascii_text.strip("-")


def make_occupation_id(title: str, nco_code: str | None, ncs_id: str | None = None) -> str:
    digits = re.sub(r"[^0-9]+", "", str(nco_code or ""))
    if digits:
        return digits
    if ncs_id:
        return f"ncs-{ncs_id}"
    return slugify(title)


def pdf_to_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-raw", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def clean_title(line: str) -> str:
    line = " ".join(line.strip().split())
    line = line.rstrip(" .")
    return line


def looks_like_title(line: str) -> bool:
    if not line or line.isdigit():
        return False
    if line.startswith(HEADER_PREFIXES):
        return False
    if re.match(r"^(Code|Title|NSQF Level|QP NOS Name|QP NOS Reference)\b", line):
        return False
    if re.match(r"^(Group|Family|Sub Division|Division)\b", line):
        return False
    if line.startswith("ISCO 08"):
        return False
    if line in DIVISION_NAMES.values():
        return False
    return True


def should_stop_description(line: str) -> bool:
    if not line:
        return False
    if CODE_PATTERN.fullmatch(line):
        return True
    if re.match(r"^(ISCO 08 Unit Group Details:|Qualification Pack Details:|QP NOS Reference|QP NOS Name|NSQF Level|Code\s+\d{4}|Title\s+)", line):
        return True
    if re.match(r"^(Group|Family|Sub Division|Division)\b", line):
        return True
    if line.startswith("VOLUME II") or line.startswith("National Classification of Occupations"):
        return True
    return False


def parse_occupation_entries(text: str, source_name: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    records: list[dict[str, object]] = []
    seen_codes: set[str] = set()

    for index, raw_line in enumerate(lines[:-1]):
        line = raw_line.strip()
        if not CODE_PATTERN.fullmatch(line):
            continue

        title = ""
        title_index = None
        for look_ahead in range(index + 1, min(index + 8, len(lines))):
            candidate = clean_title(lines[look_ahead])
            if looks_like_title(candidate):
                title = candidate
                title_index = look_ahead
                break

        if not title or title_index is None:
            continue

        description_parts: list[str] = []
        for look_ahead in range(title_index + 1, len(lines)):
            candidate = clean_title(lines[look_ahead])
            if should_stop_description(candidate):
                break
            if candidate:
                description_parts.append(candidate)
        description = " ".join(description_parts).strip()

        code_digits = line.replace(".", "")
        if code_digits in seen_codes:
            continue
        seen_codes.add(code_digits)
        division_code = code_digits[:1]

        records.append(
            {
                "title": title,
                "slug": slugify(title),
                "occupation_id": make_occupation_id(title, code_digits),
                "nco_code": code_digits,
                "category": DIVISION_NAMES.get(division_code, f"NCO Division {division_code}"),
                "source_urls": [source_name],
                "ncs_id": None,
                "source_type": "nco_2015",
                "nco_description": description,
            }
        )

    return records


def dedupe_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen_codes: set[str] = set()
    seen_titles: set[tuple[str, str]] = set()

    for record in records:
        code = str(record.get("nco_code") or "")
        title_key = (str(record["title"]).lower(), code[:4])
        if code and code in seen_codes:
            continue
        if title_key in seen_titles:
            continue
        if code:
            seen_codes.add(code)
        seen_titles.add(title_key)
        deduped.append(record)

    deduped.sort(key=lambda item: (str(item["category"]), str(item["title"])))
    return deduped


def build_master_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in (VOL_2A_PATH, VOL_2B_PATH):
        text = pdf_to_text(path)
        records.extend(parse_occupation_entries(text, path.name))
    return dedupe_records(records)


def main() -> None:
    records = build_master_records()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(records, indent=2))
    print(f"Wrote {len(records)} NCO occupations to {OUTPUT_PATH.relative_to(INDIA_DIR.parent)}")
    if records:
        sample = records[0]
        print(f"Sample: {sample['title']} [{sample['nco_code']}] ({sample['category']})")


if __name__ == "__main__":
    main()
