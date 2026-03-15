import unittest
from pathlib import Path
import sys


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from build_occupations import (
    dedupe_records,
    looks_like_sector_page,
    parse_sector_links,
    parse_sector_rows,
    slugify,
)


RAW_DIR = THIS_DIR / "raw"


class BuildOccupationsTests(unittest.TestCase):
    def test_parse_sector_links_finds_agriculture_and_it(self):
        html = (RAW_DIR / "ncs-browse-by-sectors.html").read_text(errors="ignore")

        links = parse_sector_links(html)
        by_name = {entry["category"]: entry for entry in links}

        self.assertIn("Agriculture", by_name)
        self.assertIn("IT-ITeS", by_name)
        self.assertTrue(
            by_name["Agriculture"]["source_url"].endswith("FilterValue1=Agriculture")
        )

    def test_parse_sector_rows_extracts_title_id_and_nco_code(self):
        html = (RAW_DIR / "ncs-sector-agriculture.html").read_text(errors="ignore")

        rows = parse_sector_rows(html, "Agriculture")
        first = rows[0]

        self.assertEqual(first["title"], "Agricultural Engineer")
        self.assertEqual(first["ncs_id"], "3295")
        self.assertEqual(first["nco_code"], "2141.0900")
        self.assertEqual(first["category"], "Agriculture")

    def test_slugify_normalizes_titles(self):
        self.assertEqual(slugify("IT-ITeS Specialist"), "it-ites-specialist")

    def test_parse_sector_rows_handles_missing_row_block(self):
        self.assertEqual(parse_sector_rows("<html><body>404</body></html>", "Agriculture"), [])
        self.assertFalse(looks_like_sector_page("<html><body>404</body></html>"))

    def test_parse_sector_rows_handles_string_nco_values(self):
        html = """
        <script>
        var WPQ2ListData = {
          "Row": [
            {
              "ID": "1",
              "Title": "Test Occupation",
              "Industry_x002f_Sector_x0028_s_x00": "Test Sector",
              "NCO_x0020_Code": ["1234.0000"]
            }
          ],
          "FirstRow": 1
        };
        </script>
        """
        rows = parse_sector_rows(html, "Fallback")
        self.assertEqual(rows[0]["nco_code"], "1234.0000")

    def test_dedupe_records_prefers_unique_ncs_id(self):
        records = [
            {
                "title": "Occupation A",
                "slug": "occupation-a",
                "nco_code": "1111.0000",
                "category": "One",
                "source_urls": ["a"],
                "ncs_id": "1",
            },
            {
                "title": "Occupation A",
                "slug": "occupation-a",
                "nco_code": "1111.0000",
                "category": "One",
                "source_urls": ["b"],
                "ncs_id": "1",
            },
            {
                "title": "Occupation B",
                "slug": "occupation-b",
                "nco_code": "2222.0000",
                "category": "Two",
                "source_urls": ["c"],
                "ncs_id": None,
            },
            {
                "title": "Occupation B",
                "slug": "occupation-b",
                "nco_code": "2222.0000",
                "category": "Two",
                "source_urls": ["d"],
                "ncs_id": None,
            },
        ]
        deduped = dedupe_records(records)
        self.assertEqual(len(deduped), 2)


if __name__ == "__main__":
    unittest.main()
