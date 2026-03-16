"""
Build a first-pass India occupation list from downloaded NCS source pages.

Inputs:
- india/raw/ncs-browse-by-sectors.html
- any india/raw/ncs-sector-*.html files
- india/output/occupations_nco_master.json (optional)

Output:
- india/output/occupations_india.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urljoin


BASE_URL = "https://www.ncs.gov.in"
INDIA_DIR = Path(__file__).resolve().parent
RAW_DIR = INDIA_DIR / "raw"
OUTPUT_PATH = INDIA_DIR / "output" / "occupations_india.json"
NCO_MASTER_PATH = INDIA_DIR / "output" / "occupations_nco_master.json"
SECTOR_LINK_PATTERN = re.compile(
    r"<a href='([^']*ViewNcos\.aspx[^']*)'[^>]*><img[^>]*alt='([^']+)'",
    re.IGNORECASE,
)
ROW_BLOCK_PATTERN = re.compile(r'"Row"\s*:\s*(\[.*?\])\s*,\s*"FirstRow"', re.DOTALL)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text)
    return ascii_text.strip("-")


def normalize_nco_code(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"[^0-9]+", "", str(value))


def make_occupation_id(title: str, nco_code: object, ncs_id: object) -> str:
    code = normalize_nco_code(nco_code)
    if code:
        return code
    if ncs_id:
        return f"ncs-{ncs_id}"
    return slugify(title)


def parse_sector_links(html: str) -> List[Dict[str, str]]:
    seen = set()
    links: List[Dict[str, str]] = []
    for href, alt in SECTOR_LINK_PATTERN.findall(html):
        category = alt.strip()
        source_url = urljoin(BASE_URL, href.strip())
        key = (category, source_url)
        if key in seen:
            continue
        seen.add(key)
        links.append(
            {
                "category": category,
                "slug": slugify(category),
                "source_url": source_url,
            }
        )
    return links


def parse_sector_rows(html: str, fallback_category: str | None = None) -> List[Dict[str, object]]:
    match = ROW_BLOCK_PATTERN.search(html)
    if not match:
        return []

    rows = json.loads(match.group(1))
    parsed_rows: List[Dict[str, object]] = []
    for row in rows:
        title = (row.get("Title") or "").strip()
        ncs_id = (row.get("ID") or "").strip()
        category = (row.get("Industry_x002f_Sector_x0028_s_x00") or fallback_category or "").strip()
        nco_values = row.get("NCO_x0020_Code") or []
        nco_code = ""
        if isinstance(nco_values, list) and nco_values:
            first_code = nco_values[0] or {}
            if isinstance(first_code, dict):
                nco_code = (first_code.get("lookupValue") or "").strip()
            elif isinstance(first_code, str):
                nco_code = first_code.strip()

        if not title:
            continue

        parsed_rows.append(
            {
                "title": title,
                "slug": slugify(title),
                "nco_code": nco_code,
                "category": category,
                "ncs_id": ncs_id or None,
            }
        )
    return parsed_rows


def build_sector_lookup(sector_links: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {entry["slug"]: entry for entry in sector_links}


def infer_sector_slug(path: Path) -> str:
    name = path.stem
    prefix = "ncs-sector-"
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def looks_like_sector_page(html: str) -> bool:
    return ROW_BLOCK_PATTERN.search(html) is not None and "WPQ2ListData" in html


def normalize_record(
    row: Dict[str, object], sector_info: Dict[str, str] | None, raw_file: Path
) -> Dict[str, object]:
    source_urls = []
    if sector_info and sector_info.get("source_url"):
        source_urls.append(sector_info["source_url"])
    source_urls.append(raw_file.name)

    record = {
        "title": row["title"],
        "slug": row["slug"],
        "occupation_id": make_occupation_id(row["title"], row["nco_code"], row["ncs_id"]),
        "nco_code": normalize_nco_code(row["nco_code"]) or None,
        "category": row["category"] or (sector_info["category"] if sector_info else None),
        "source_urls": source_urls,
        "ncs_id": row["ncs_id"],
    }
    return record


def dedupe_records(records: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    deduped: List[Dict[str, object]] = []
    seen: dict[object, Dict[str, object]] = {}
    seen_codes: dict[str, Dict[str, object]] = {}
    for record in records:
        normalized_code = normalize_nco_code(record.get("nco_code"))
        record["nco_code"] = normalized_code or None
        record["occupation_id"] = make_occupation_id(
            str(record["title"]),
            normalized_code,
            record.get("ncs_id"),
        )
        dedupe_key = record["ncs_id"] or (
            str(record["title"]).lower(),
            normalized_code,
        )
        existing = None
        if normalized_code and normalized_code in seen_codes:
            existing = seen_codes[normalized_code]
        elif dedupe_key in seen:
            existing = seen[dedupe_key]

        if existing is not None:
            existing_urls = list(existing.get("source_urls", []))
            for url in record.get("source_urls", []):
                if url not in existing_urls:
                    existing_urls.append(url)
            existing["source_urls"] = existing_urls

            for field in ("nco_description", "source_type", "ncs_id"):
                if not existing.get(field) and record.get(field):
                    existing[field] = record[field]

            # Prefer the category from the richer NCS record when present.
            if existing.get("ncs_id") and record.get("ncs_id"):
                pass
            elif not existing.get("ncs_id") and record.get("ncs_id"):
                existing["category"] = record.get("category")
            elif not existing.get("category") and record.get("category"):
                existing["category"] = record.get("category")
            continue

        seen[dedupe_key] = record
        if normalized_code:
            seen_codes[normalized_code] = record
        deduped.append(record)
    deduped.sort(key=lambda item: (str(item["category"] or ""), str(item["title"])))
    return deduped


def load_nco_master_records() -> List[Dict[str, object]]:
    if not NCO_MASTER_PATH.exists():
        return []
    rows = json.loads(NCO_MASTER_PATH.read_text())
    normalized: List[Dict[str, object]] = []
    for row in rows:
        normalized.append(
            {
                "title": row["title"],
                "slug": row["slug"],
                "occupation_id": row.get(
                    "occupation_id",
                    make_occupation_id(row["title"], row.get("nco_code"), row.get("ncs_id")),
                ),
                "nco_code": normalize_nco_code(row.get("nco_code")) or None,
                "category": row.get("category"),
                "source_urls": row.get("source_urls", [NCO_MASTER_PATH.name]),
                "ncs_id": row.get("ncs_id"),
                "nco_description": row.get("nco_description", ""),
                "source_type": row.get("source_type", "nco_2015"),
            }
        )
    return normalized


def collect_occupations() -> Dict[str, object]:
    browse_path = RAW_DIR / "ncs-browse-by-sectors.html"
    browse_html = browse_path.read_text(errors="ignore")
    sector_links = parse_sector_links(browse_html)
    sector_lookup = build_sector_lookup(sector_links)

    records: List[Dict[str, object]] = []
    sector_files = sorted(RAW_DIR.glob("ncs-sector-*.html"))
    invalid_sector_pages = 0
    for path in sector_files:
        sector_slug = infer_sector_slug(path)
        sector_info = sector_lookup.get(sector_slug)
        fallback_category = sector_info["category"] if sector_info else sector_slug.replace("-", " ").title()
        html = path.read_text(errors="ignore")
        if not looks_like_sector_page(html):
            invalid_sector_pages += 1
            continue
        rows = parse_sector_rows(html, fallback_category)
        for row in rows:
            records.append(normalize_record(row, sector_info, path))

    nco_master_records = load_nco_master_records()
    records.extend(nco_master_records)
    deduped = dedupe_records(records)
    return {
        "meta": {
            "browse_page": browse_path.name,
            "sector_pages": len(sector_files),
            "invalid_sector_pages": invalid_sector_pages,
            "sector_links": len(sector_links),
            "nco_master_records": len(nco_master_records),
            "occupations": len(deduped),
        },
        "occupations": deduped,
    }


def main() -> None:
    result = collect_occupations()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result["occupations"], indent=2))

    meta = result["meta"]
    print(
        "Wrote {occupations} occupations from {sector_pages} downloaded sector page(s) "
        "({invalid_sector_pages} invalid), {sector_links} sector link(s), and "
        "{nco_master_records} NCO master record(s) to {path}".format(
            occupations=meta["occupations"],
            sector_pages=meta["sector_pages"],
            invalid_sector_pages=meta["invalid_sector_pages"],
            sector_links=meta["sector_links"],
            nco_master_records=meta["nco_master_records"],
            path=OUTPUT_PATH.relative_to(INDIA_DIR.parent),
        )
    )
    if result["occupations"]:
        sample = result["occupations"][0]
        print(
            "Sample: {title} [{nco_code}] ({category})".format(
                title=sample["title"],
                nco_code=sample["nco_code"] or "?",
                category=sample["category"] or "?",
            )
        )


if __name__ == "__main__":
    main()
