"""
Fetch and normalize India occupation description pages from NCS.

Inputs:
- india/output/occupations_india.json

Outputs:
- india/output/pages/<slug>.md
- india/output/pages_india.json

The first pass is intentionally conservative:
- fetch raw NCS detail pages by COBID when available
- cache raw detail HTML under india/raw/details/
- extract section text only when obvious section markup is present
- always emit a markdown page with normalized occupation metadata so the
  downstream scoring pipeline has a stable input shape even when NCS detail
  content is thin or client-rendered
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


INDIA_DIR = Path(__file__).resolve().parent
RAW_DIR = INDIA_DIR / "raw"
DETAILS_DIR = RAW_DIR / "details"
OCCUPATIONS_PATH = INDIA_DIR / "output" / "occupations_india.json"
PAGES_DIR = INDIA_DIR / "output" / "pages"
OUTPUT_PATH = INDIA_DIR / "output" / "pages_india.json"
BASE_DETAIL_URL = "https://www.ncs.gov.in/content-repository/Pages/ViewNcoDetails.aspx?COBID={ncs_id}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


def build_detail_url(record: dict[str, object]) -> str:
    ncs_id = str(record.get("ncs_id") or "").strip()
    if not ncs_id:
        return ""
    return BASE_DETAIL_URL.format(ncs_id=ncs_id)


def clean_html_text(text: str) -> str:
    text = TAG_PATTERN.sub(" ", text)
    text = unescape(text)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


class SectionHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sections: list[dict[str, str]] = []
        self._current_id: str | None = None
        self._current_title_parts: list[str] = []
        self._current_body_parts: list[str] = []
        self._div_depth = 0
        self._capture_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if self._current_id is None:
            section_id = attr_map.get("id", "")
            if tag == "div" and section_id and re.fullmatch(r"section\d+", section_id):
                self._current_id = section_id
                self._div_depth = 1
                self._current_title_parts = []
                self._current_body_parts = []
                return
        elif tag == "div":
            self._div_depth += 1

        if self._current_id is not None and tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._capture_heading = True

    def handle_endtag(self, tag: str) -> None:
        if self._current_id is None:
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._capture_heading = False
            return

        if tag == "div":
            self._div_depth -= 1
            if self._div_depth == 0:
                title = clean_html_text("".join(self._current_title_parts))
                body = clean_html_text("".join(self._current_body_parts))
                if title and body:
                    self.sections.append({"title": title, "body": body})
                self._current_id = None
                self._current_title_parts = []
                self._current_body_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_id is None:
            return
        if self._capture_heading:
            self._current_title_parts.append(data)
        else:
            self._current_body_parts.append(data)


def extract_sections(html: str) -> list[dict[str, str]]:
    parser = SectionHTMLParser()
    parser.feed(html)
    return parser.sections


def looks_like_detail_page(html: str) -> bool:
    return "ViewNcoDetails.aspx" in html and "Job Description" in html


def build_markdown(record: dict[str, object], detail_url: str, sections: list[dict[str, str]]) -> str:
    lines = [f"# {record['title']}", ""]
    if detail_url:
        lines.append(f"**Source:** {detail_url}")
        lines.append("")

    lines.append("## Occupation Metadata")
    lines.append("")
    if record.get("nco_code"):
        lines.append(f"- **NCO Code:** {record['nco_code']}")
    if record.get("category"):
        lines.append(f"- **Category:** {record['category']}")
    if record.get("ncs_id"):
        lines.append(f"- **NCS ID:** {record['ncs_id']}")
    source_urls = record.get("source_urls") or []
    if source_urls:
        lines.append(f"- **Sector Sources:** {', '.join(source_urls)}")
    lines.append("")

    if sections:
        for section in sections:
            lines.append(f"## {section['title']}")
            lines.append("")
            lines.append(section["body"])
            lines.append("")
    else:
        lines.append("## Source Notes")
        lines.append("")
        lines.append(
            "Detailed NCS section text was not extracted from the cached detail page. "
            "This page currently preserves normalized occupation metadata and source links "
            "so the downstream pipeline remains stable while richer NCS extraction is improved."
        )
        lines.append("")

    return "\n".join(lines).strip() + "\n"


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


def load_occupations() -> list[dict[str, object]]:
    return json.loads(OCCUPATIONS_PATH.read_text())


def detail_cache_path(record: dict[str, object]) -> Path:
    ncs_id = str(record.get("ncs_id") or "").strip() or str(record["slug"])
    return DETAILS_DIR / f"{ncs_id}.html"


def existing_detail_cache_path(record: dict[str, object]) -> Path | None:
    preferred = detail_cache_path(record)
    if preferred.exists():
        return preferred

    ncs_id = str(record.get("ncs_id") or "").strip()
    if ncs_id:
        legacy = RAW_DIR / f"ncs-detail-{ncs_id}.html"
        if legacy.exists():
            return legacy

    return None


def process_record(record: dict[str, object], force: bool) -> dict[str, object]:
    detail_url = build_detail_url(record)
    cache_path = detail_cache_path(record)
    cache_status = "missing"
    html = ""
    stored_path: Path | None = None
    fetched_live = False

    existing_cache = existing_detail_cache_path(record)
    if existing_cache is not None and not force:
        html = existing_cache.read_text(errors="ignore")
        stored_path = existing_cache
        cache_status = "cached" if looks_like_detail_page(html) else "cached-invalid"
    elif detail_url:
        try:
            fetched_live = True
            candidate_html = download(detail_url)
            if looks_like_detail_page(candidate_html):
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(candidate_html)
                html = candidate_html
                stored_path = cache_path
                cache_status = "fetched"
            else:
                cache_status = "invalid"
        except (HTTPError, URLError, TimeoutError, subprocess.CalledProcessError):
            cache_status = "error"

    sections = extract_sections(html) if html else []
    if cache_status in {"cached", "fetched"} and not sections:
        cache_status = f"{cache_status}-shell"
    markdown = build_markdown(record, detail_url, sections)
    page_path = PAGES_DIR / f"{record['slug']}.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(markdown)

    return {
        "slug": record["slug"],
        "title": record["title"],
        "nco_code": record.get("nco_code"),
        "category": record.get("category"),
        "ncs_id": record.get("ncs_id"),
        "detail_url": detail_url,
        "raw_detail_path": str(stored_path.relative_to(INDIA_DIR)) if stored_path else "",
        "page_path": str(page_path.relative_to(INDIA_DIR)),
        "section_count": len(sections),
        "detail_status": cache_status,
        "fetched_live": fetched_live,
    }


def merge_with_existing_pages(
    pages: list[dict[str, object]],
    all_source_slugs: set[str],
    preserve_unprocessed: bool,
) -> list[dict[str, object]]:
    existing_by_slug: dict[str, dict[str, object]] = {}
    if OUTPUT_PATH.exists():
        try:
            existing = json.loads(OUTPUT_PATH.read_text())
            existing_by_slug = {
                entry["slug"]: entry
                for entry in existing
                if entry.get("slug") in all_source_slugs
            }
        except json.JSONDecodeError:
            existing_by_slug = {}

    if not preserve_unprocessed:
        existing_by_slug = {}

    for page in pages:
        existing_by_slug[page["slug"]] = page

    return [existing_by_slug[slug] for slug in sorted(existing_by_slug)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch NCS occupation descriptions")
    parser.add_argument("--limit", type=int, default=None, help="Limit processed occupations")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between live fetches")
    parser.add_argument("--force", action="store_true", help="Re-fetch cached detail pages")
    args = parser.parse_args()

    all_occupations = load_occupations()
    all_source_slugs = {str(record["slug"]) for record in all_occupations}
    occupations = all_occupations
    if args.limit is not None:
        occupations = occupations[: args.limit]

    pages: list[dict[str, object]] = []
    fetched = 0
    cached = 0
    errors = 0
    with_sections = 0

    for index, record in enumerate(occupations, start=1):
        result = process_record(record, force=args.force)
        pages.append(result)

        if str(result["detail_status"]).startswith("fetched"):
            fetched += 1
        elif str(result["detail_status"]).startswith("cached"):
            cached += 1
        elif result["detail_status"] == "error":
            errors += 1

        if result["section_count"]:
            with_sections += 1

        print(
            f"[{index}/{len(occupations)}] {record['title']} "
            f"status={result['detail_status']} sections={result['section_count']}"
        )

        if result["fetched_live"] and index < len(occupations):
            time.sleep(args.delay)

    merged_pages = merge_with_existing_pages(
        pages,
        all_source_slugs=all_source_slugs,
        preserve_unprocessed=args.limit is not None,
    )
    OUTPUT_PATH.write_text(json.dumps(merged_pages, indent=2))
    print(
        f"Wrote {len(merged_pages)} page records to {OUTPUT_PATH.relative_to(INDIA_DIR.parent)} "
        f"(fetched={fetched}, cached={cached}, errors={errors}, with_sections={with_sections})"
    )


if __name__ == "__main__":
    main()
