"""
Fetch and normalize India occupation education data from official NQR sources.

Inputs:
- india/output/occupations_india.json
- india/raw/nqr-search.html
- india/raw/nqr-qualificationids.txt
- india/raw/nqr-summary-full.xlsx

Outputs:
- india/output/education_india.json
- india/raw/nqr-qualifications/<qualification_id>.html

The matching strategy is intentionally conservative:
- limit matches to the mapped NQR sector for each NCS occupation
- prefer exact normalized title matches against qualification title or proposed occupation
- allow only very high-similarity fuzzy matches as a fallback
- leave education blank when no strong official match exists
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile


INDIA_DIR = Path(__file__).resolve().parent
RAW_DIR = INDIA_DIR / "raw"
OUTPUT_DIR = INDIA_DIR / "output"
OCCUPATIONS_PATH = OUTPUT_DIR / "occupations_india.json"
NQR_SEARCH_PATH = RAW_DIR / "nqr-search.html"
NQR_IDS_PATH = RAW_DIR / "nqr-qualificationids.txt"
NQR_SUMMARY_PATH = RAW_DIR / "nqr-summary-full.xlsx"
NQR_PAGES_DIR = RAW_DIR / "nqr-qualifications"
OUTPUT_PATH = OUTPUT_DIR / "education_india.json"
QUALIFICATION_URL = "https://www.nqr.gov.in/qualifications/{qualification_id}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

WHITESPACE_PATTERN = re.compile(r"\s+")
TAG_PATTERN = re.compile(r"<[^>]+>")
TITLE_PATTERN = re.compile(r"<h1>(.*?)</h1>", re.S | re.I)
ELIGIBILITY_TABLE_PATTERN = re.compile(
    r"<h3[^>]*>\s*Eligibility Criteria\s*</h3>.*?<table[^>]*class=\"elg\"[^>]*>(.*?)</table>",
    re.S | re.I,
)
ROW_PATTERN = re.compile(r"<tr>(.*?)</tr>", re.S | re.I)
CELL_PATTERN = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

NCS_TO_NQR_SECTOR = {
    "Agriculture": "Agriculture",
    "Apparel": "Apparel",
    "Automotive": "Automotive",
    "BFSI": "BFSI",
    "Beauty and Wellness": "Beauty & Wellness",
    "Electronics and HW": "Electronics & HW",
    "Healthcare": "Healthcare",
    "Leather": "Leather",
    "Organised Retail": "Retail",
    "Plumbing": "Plumbing",
}

EDUCATION_BUCKETS = [
    "Up to middle",
    "Secondary (10th)",
    "Higher secondary (12th)",
    "Diploma / ITI / Certificate",
    "Graduate",
    "Postgraduate+",
]


@dataclass(frozen=True)
class Qualification:
    qualification_id: str
    title: str
    code: str
    sector_name: str
    proposed_occupation: str
    page_url: str


def clean_text(text: str) -> str:
    text = TAG_PATTERN.sub(" ", text)
    text = unescape(text)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def normalize_label(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", unescape(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().replace("&", " and ")
    ascii_text = re.sub(r"[^a-z0-9]+", " ", ascii_text)
    return WHITESPACE_PATTERN.sub(" ", ascii_text).strip()


def load_occupations() -> list[dict[str, object]]:
    return json.loads(OCCUPATIONS_PATH.read_text())


def load_qualification_ids() -> list[str]:
    if NQR_IDS_PATH.exists():
        return [item for item in NQR_IDS_PATH.read_text().strip().split(",") if item]

    html = NQR_SEARCH_PATH.read_text(errors="ignore")
    match = re.search(
        r'name="qualificationids"\s+class="qualificationids"\s+value="([^"]+)"',
        html,
    )
    if not match:
        raise ValueError(f"Could not find qualification ids in {NQR_SEARCH_PATH}")
    ids = [item for item in match.group(1).split(",") if item]
    NQR_IDS_PATH.write_text(",".join(ids))
    return ids


def _shared_strings(zip_file: ZipFile) -> list[str]:
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root:
        strings.append("".join(node.text or "" for node in item.iter(f"{{{NS['a']}}}t")))
    return strings


def _row_values(row: ET.Element, shared_strings: list[str]) -> list[str]:
    values: list[str] = []
    for cell in row.findall("a:c", NS):
        cell_type = cell.get("t")
        value = cell.find("a:v", NS)
        if value is None or value.text is None:
            values.append("")
        elif cell_type == "s":
            values.append(shared_strings[int(value.text)])
        else:
            values.append(value.text)
    return values


def load_summary_rows(summary_path: Path = NQR_SUMMARY_PATH) -> list[dict[str, str]]:
    with ZipFile(summary_path) as zip_file:
        shared_strings = _shared_strings(zip_file)
        sheet = ET.fromstring(zip_file.read("xl/worksheets/sheet1.xml"))
    rows = sheet.findall(".//a:sheetData/a:row", NS)
    headers = _row_values(rows[1], shared_strings)
    parsed: list[dict[str, str]] = []
    for row in rows[2:]:
        values = _row_values(row, shared_strings)
        parsed.append(dict(zip(headers, values)))
    return parsed


def load_qualifications() -> list[Qualification]:
    qualification_ids = load_qualification_ids()
    summary_rows = load_summary_rows()
    if len(qualification_ids) != len(summary_rows):
        raise ValueError(
            "NQR qualification ids do not align with summary rows: "
            f"{len(qualification_ids)} ids vs {len(summary_rows)} rows"
        )

    qualifications: list[Qualification] = []
    for qualification_id, row in zip(qualification_ids, summary_rows):
        qualifications.append(
            Qualification(
                qualification_id=qualification_id,
                title=(row.get("Title") or "").strip(),
                code=(row.get("Code") or "").strip(),
                sector_name=(row.get("Sector Name") or "").strip(),
                proposed_occupation=(row.get("Proposed Occupation") or "").strip(),
                page_url=QUALIFICATION_URL.format(qualification_id=qualification_id),
            )
        )
    return qualifications


def match_score(occupation_title: str, candidate: Qualification) -> tuple[int, float]:
    target = normalize_label(occupation_title)
    values = [
        normalize_label(candidate.title),
        normalize_label(candidate.proposed_occupation),
    ]
    values = [value for value in values if value and value != "n a"]
    if not values:
        return (0, 0.0)

    if target in values:
        return (3, 1.0)

    best_ratio = 0.0
    for value in values:
        if not value:
            continue
        if target in value or value in target:
            overlap = min(len(target), len(value)) / max(len(target), len(value))
            best_ratio = max(best_ratio, overlap)
        else:
            target_tokens = set(target.split())
            value_tokens = set(value.split())
            if target_tokens and value_tokens:
                overlap = len(target_tokens & value_tokens) / len(target_tokens | value_tokens)
                best_ratio = max(best_ratio, overlap)

    if best_ratio >= 0.92:
        return (2, best_ratio)
    if best_ratio >= 0.75:
        return (1, best_ratio)
    return (0, best_ratio)


def choose_match(
    occupation: dict[str, object],
    qualifications: Iterable[Qualification],
) -> tuple[Qualification | None, str]:
    sector = NCS_TO_NQR_SECTOR.get(str(occupation.get("category") or "").strip(), "")
    candidates = [item for item in qualifications if item.sector_name == sector] if sector else []

    best: Qualification | None = None
    best_rank = (0, 0.0)
    for candidate in candidates:
        rank = match_score(str(occupation.get("title") or ""), candidate)
        if rank > best_rank:
            best_rank = rank
            best = candidate

    if best is None:
        return None, "no-sector-match"
    if best_rank[0] == 3:
        return best, "exact"
    if best_rank[0] == 2:
        return best, "high-similarity"
    return None, "unmatched"


def cache_path_for_qualification(qualification_id: str) -> Path:
    return NQR_PAGES_DIR / f"{qualification_id}.html"


def download(url: str) -> str:
    normalized_url = quote(url, safe=":/?&=%")
    curl_path = shutil.which("curl")
    if curl_path:
        result = subprocess.run(
            [curl_path, "--http1.1", "-A", HEADERS["User-Agent"], "-L", normalized_url],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    request = Request(normalized_url, headers=HEADERS)
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def load_or_fetch_qualification_page(
    qualification: Qualification,
    force: bool = False,
    delay: float = 0.0,
) -> str:
    cache_path = cache_path_for_qualification(qualification.qualification_id)
    if cache_path.exists() and not force:
        return cache_path.read_text(errors="ignore")

    html = download(qualification.page_url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html)
    if delay > 0:
        time.sleep(delay)
    return html


def extract_page_title(html: str) -> str:
    match = TITLE_PATTERN.search(html)
    return clean_text(match.group(1)) if match else ""


def extract_eligibility_rows(html: str) -> list[str]:
    match = ELIGIBILITY_TABLE_PATTERN.search(html)
    if not match:
        return []

    results: list[str] = []
    for row_html in ROW_PATTERN.findall(match.group(1)):
        cells = [clean_text(cell) for cell in CELL_PATTERN.findall(row_html)]
        if len(cells) < 2 or cells[0].lower().startswith("criteria 1"):
            continue
        criteria = " ".join(part for part in cells[:2] if part and part.lower() != "none").strip()
        if criteria:
            results.append(criteria)
    deduped: list[str] = []
    seen = set()
    for item in results:
        key = normalize_label(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def bucket_for_text(text: str) -> str:
    normalized = normalize_label(text)
    if re.search(
        r"\b(post graduate|postgraduate|master|mba|mtech|msc|mcom|phd|doctorate|doctor)\b",
        normalized,
    ):
        return "Postgraduate+"
    if re.search(
        r"\b(graduate|bachelor|b tech|btech|bsc|b com|bcom|bbm|bba|mbbs|llb)\b",
        normalized,
    ):
        return "Graduate"
    if any(token in normalized for token in ["diploma", "iti", "certificate", "polytechnic"]):
        return "Diploma / ITI / Certificate"
    if any(
        token in normalized
        for token in ["12th", "xii", "higher secondary", "senior secondary", "intermediate", "puc"]
    ):
        return "Higher secondary (12th)"
    if any(token in normalized for token in ["10th", "matric", "secondary", "ssc"]):
        return "Secondary (10th)"
    if any(token in normalized for token in ["8th", "5th", "primary", "middle", "literate"]):
        return "Up to middle"
    return ""


def choose_education_bucket(eligibility_rows: list[str]) -> str:
    found = [bucket_for_text(row) for row in eligibility_rows]
    found = [bucket for bucket in found if bucket]
    if not found:
        return ""
    return min(found, key=EDUCATION_BUCKETS.index)


def build_education_record(
    occupation: dict[str, object],
    qualification: Qualification | None,
    match_type: str,
    force: bool,
    delay: float,
) -> dict[str, object]:
    if qualification is None:
        return {
            "slug": occupation["slug"],
            "title": occupation["title"],
            "education": "",
            "education_bucket": "",
            "education_source_url": "",
            "education_source_type": "",
            "match_type": match_type,
        }

    html = load_or_fetch_qualification_page(qualification, force=force, delay=delay)
    page_title = extract_page_title(html)
    if page_title and normalize_label(page_title) != normalize_label(qualification.title):
        raise ValueError(
            f"NQR qualification id {qualification.qualification_id} did not match summary title "
            f"'{qualification.title}'"
        )

    eligibility_rows = extract_eligibility_rows(html)
    return {
        "slug": occupation["slug"],
        "title": occupation["title"],
        "education": " or ".join(eligibility_rows),
        "education_bucket": choose_education_bucket(eligibility_rows),
        "education_source_url": qualification.page_url,
        "education_source_type": "NQR eligibility criteria",
        "match_type": match_type,
        "nqr_qualification_id": qualification.qualification_id,
        "nqr_title": qualification.title,
        "nqr_code": qualification.code,
        "nqr_sector_name": qualification.sector_name,
    }


def build_education_rows(
    occupations: list[dict[str, object]],
    qualifications: list[Qualification],
    force: bool = False,
    delay: float = 0.0,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for occupation in occupations:
        qualification, match_type = choose_match(occupation, qualifications)
        rows.append(build_education_record(occupation, qualification, match_type, force, delay))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="refetch cached NQR qualification pages")
    parser.add_argument("--delay", type=float, default=0.0, help="delay between live fetches")
    args = parser.parse_args()

    occupations = load_occupations()
    qualifications = load_qualifications()
    rows = build_education_rows(occupations, qualifications, force=args.force, delay=args.delay)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(rows, indent=2))

    matched = sum(1 for row in rows if row["education"])
    bucketed = sum(1 for row in rows if row["education_bucket"])
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH.relative_to(INDIA_DIR.parent)}")
    print(f"Matched education for {matched} occupations")
    print(f"Bucketed education for {bucketed} occupations")


if __name__ == "__main__":
    main()
