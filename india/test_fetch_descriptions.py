import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from fetch_descriptions import (
    build_markdown,
    build_detail_url,
    existing_detail_cache_path,
    extract_sections,
    looks_like_detail_page,
    merge_with_existing_pages,
)


class FetchDescriptionsTests(unittest.TestCase):
    def test_build_detail_url_uses_cobid(self):
        record = {"ncs_id": "3295"}
        self.assertEqual(
            build_detail_url(record),
            "https://www.ncs.gov.in/content-repository/Pages/ViewNcoDetails.aspx?COBID=3295",
        )

    def test_extract_sections_returns_empty_for_shell_html(self):
        html = (THIS_DIR / "raw" / "ncs-detail-3295.html").read_text(errors="ignore")
        self.assertEqual(extract_sections(html), [])

    def test_extract_sections_parses_simple_section_markup(self):
        html = """
        <div id="section3"><h2>Job Description</h2><p>Builds systems.</p></div>
        <div id="section4"><h2>Work Environment</h2><p>Field and office work.</p></div>
        """
        sections = extract_sections(html)
        self.assertEqual(
            sections,
            [
                {"title": "Job Description", "body": "Builds systems."},
                {"title": "Work Environment", "body": "Field and office work."},
            ],
        )

    def test_extract_sections_handles_nested_div_content(self):
        html = """
        <div id="section3">
          <h2>Job Description</h2>
          <div><p>Builds systems.</p><div>Works with teams.</div></div>
        </div>
        """
        sections = extract_sections(html)
        self.assertEqual(len(sections), 1)
        self.assertIn("Builds systems.", sections[0]["body"])
        self.assertIn("Works with teams.", sections[0]["body"])

    def test_build_markdown_includes_fallback_metadata(self):
        record = {
            "title": "Agricultural Engineer",
            "slug": "agricultural-engineer",
            "nco_code": "2141.0900",
            "category": "Agriculture",
            "source_urls": ["https://example.com/sector"],
            "ncs_id": "3295",
        }
        markdown = build_markdown(
            record,
            "https://www.ncs.gov.in/content-repository/Pages/ViewNcoDetails.aspx?COBID=3295",
            [],
        )
        self.assertIn("# Agricultural Engineer", markdown)
        self.assertIn("- **NCO Code:** 2141.0900", markdown)
        self.assertIn("- **Category:** Agriculture", markdown)
        self.assertIn("- **NCS ID:** 3295", markdown)
        self.assertIn("Detailed NCS section text was not extracted", markdown)

    def test_existing_detail_cache_path_finds_legacy_cached_detail_page(self):
        record = {"ncs_id": "3295", "slug": "agricultural-engineer"}
        path = existing_detail_cache_path(record)
        self.assertIsNotNone(path)
        self.assertTrue(path.name.endswith("3295.html"))

    def test_looks_like_detail_page_detects_known_shell(self):
        html = (THIS_DIR / "raw" / "ncs-detail-3295.html").read_text(errors="ignore")
        self.assertTrue(looks_like_detail_page(html))

    def test_merge_with_existing_pages_preserves_subset_only_in_limited_runs(self):
        existing = [
            {"slug": "a", "detail_status": "cached"},
            {"slug": "b", "detail_status": "cached"},
            {"slug": "stale", "detail_status": "cached"},
        ]
        pages = [{"slug": "a", "detail_status": "error"}]

        with patch("fetch_descriptions.OUTPUT_PATH") as output_path:
            output_path.exists.return_value = True
            output_path.read_text.return_value = json.dumps(existing)

            merged_partial = merge_with_existing_pages(
                pages,
                all_source_slugs={"a", "b"},
                preserve_unprocessed=True,
            )
            merged_full = merge_with_existing_pages(
                pages,
                all_source_slugs={"a", "b"},
                preserve_unprocessed=False,
            )

        self.assertEqual([row["slug"] for row in merged_partial], ["a", "b"])
        self.assertEqual([row["slug"] for row in merged_full], ["a"])


if __name__ == "__main__":
    unittest.main()
