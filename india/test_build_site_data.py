import unittest
import importlib.util
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
MODULE_PATH = THIS_DIR / "build_site_data.py"
SPEC = importlib.util.spec_from_file_location("india_build_site_data", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
build_site_rows = MODULE.build_site_rows


class BuildSiteDataTests(unittest.TestCase):
    def test_build_site_rows_merges_stats_and_scores(self):
        stats_rows = [
            {
                "title": "Agricultural Engineer",
                "slug": "agricultural-engineer",
                "category": "Agriculture",
                "nco_code": "2141.0900",
                "pay_division_code": "2",
                "pay_annual": "429312",
                "pay_monthly": "35776",
                "employment_share": "0.23",
                "education": "Graduate",
                "education_bucket": "Graduate",
                "education_source_url": "https://www.nqr.gov.in/qualifications/123",
                "education_source_type": "NQR eligibility criteria",
                "url": "https://example.com/a",
            }
        ]
        scores = {
            "agricultural-engineer": {
                "slug": "agricultural-engineer",
                "title": "Agricultural Engineer",
                "exposure": 6,
                "rationale": "AI can assist with analysis and planning but field work remains.",
            }
        }

        rows = build_site_rows(stats_rows, scores)

        self.assertEqual(
            rows,
            [
                {
                    "title": "Agricultural Engineer",
                    "slug": "agricultural-engineer",
                    "category": "Agriculture",
                    "nco_division_code": "2",
                    "nco_division_name": "Professionals",
                    "pay": 429312,
                    "pay_monthly": 35776,
                    "jobs": None,
                    "employment_share": 0.23,
                    "education": "Graduate",
                    "education_bucket": "Graduate",
                    "education_source_url": "https://www.nqr.gov.in/qualifications/123",
                    "education_source_type": "NQR eligibility criteria",
                    "exposure": 6,
                    "exposure_rationale": "AI can assist with analysis and planning but field work remains.",
                    "url": "https://example.com/a",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
