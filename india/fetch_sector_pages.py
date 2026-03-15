"""
Fetch NCS sector pages listed in india/raw/ncs-browse-by-sectors.html.

This helper keeps network access separate from the parser. It uses only the
standard library and stores each downloaded sector page in india/raw/.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

from build_occupations import RAW_DIR, looks_like_sector_page, parse_sector_links


HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.ncs.gov.in"


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch NCS sector pages")
    parser.add_argument("--limit", type=int, default=None, help="Limit sector downloads")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests")
    parser.add_argument("--force", action="store_true", help="Re-download cached sector pages")
    args = parser.parse_args()

    browse_path = RAW_DIR / "ncs-browse-by-sectors.html"
    links = parse_sector_links(browse_path.read_text(errors="ignore"))
    if args.limit is not None:
        links = links[: args.limit]

    fetched = 0
    skipped = 0
    for entry in links:
        filename = RAW_DIR / f"ncs-sector-{entry['slug']}.html"
        if filename.exists() and not args.force:
            skipped += 1
            continue

        try:
            html = download(urljoin(BASE_URL, entry["source_url"]))
        except (HTTPError, URLError, TimeoutError, subprocess.CalledProcessError) as exc:
            print(f"ERROR {entry['category']}: {exc}")
            continue

        if not looks_like_sector_page(html):
            print(f"ERROR {entry['category']}: downloaded HTML did not look like a valid sector page")
            continue

        filename.write_text(html)
        fetched += 1
        print(f"Fetched {entry['category']} -> {filename.name}")
        time.sleep(args.delay)

    print(f"Fetched: {fetched}, Skipped: {skipped}, Total considered: {len(links)}")


if __name__ == "__main__":
    main()
