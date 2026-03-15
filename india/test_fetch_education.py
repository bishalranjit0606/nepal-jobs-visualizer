import json
import sys
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from fetch_education import (
    Qualification,
    build_education_record,
    bucket_for_text,
    choose_education_bucket,
    choose_match,
    extract_eligibility_rows,
    load_qualification_ids,
    load_qualifications,
)


SAMPLE_HTML = """
<h1>Line Patrolling Man (Oil Gas)</h1>
<h3 class="mb-4">Eligibility Criteria</h3>
<table class="elg">
  <tr>
    <th>Criteria 1</th><th>Criteria 2</th><th>Experience</th><th>Training Qualification</th>
  </tr>
  <tr>
    <td>8th</td><td>Passed</td><td>1 year</td><td>None</td>
  </tr>
  <tr>
    <td>5th</td><td>Passed</td><td>4 years</td><td>None</td>
  </tr>
</table>
"""


class FetchEducationTests(unittest.TestCase):
    def test_extract_eligibility_rows_reads_official_table_shape(self):
        self.assertEqual(extract_eligibility_rows(SAMPLE_HTML), ["8th Passed", "5th Passed"])

    def test_bucket_for_text_maps_common_india_education_labels(self):
        self.assertEqual(bucket_for_text("5th Passed"), "Up to middle")
        self.assertEqual(bucket_for_text("10th Passed"), "Secondary (10th)")
        self.assertEqual(bucket_for_text("12th Pass"), "Higher secondary (12th)")
        self.assertEqual(bucket_for_text("Diploma in Mechanical Engineering"), "Diploma / ITI / Certificate")
        self.assertEqual(bucket_for_text("Graduate"), "Graduate")
        self.assertEqual(bucket_for_text("Post Graduate"), "Postgraduate+")

    def test_choose_education_bucket_prefers_lowest_minimum_requirement(self):
        bucket = choose_education_bucket(["12th Passed", "8th Passed", "Diploma in Fashion Design"])
        self.assertEqual(bucket, "Up to middle")

    def test_choose_match_prefers_exact_title_within_sector(self):
        occupation = {"title": "Agricultural Engineer", "category": "Agriculture"}
        qualifications = [
            Qualification("1", "Agricultural Engineer", "A", "Agriculture", "Agricultural Engineer", "u1"),
            Qualification("2", "Automotive Service Technician", "B", "Automotive", "Automotive Service Technician", "u2"),
        ]

        match, match_type = choose_match(occupation, qualifications)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.qualification_id, "1")
        self.assertEqual(match_type, "exact")

    def test_load_qualifications_pairs_hidden_ids_with_export_rows(self):
        qualifications = load_qualifications()
        self.assertGreater(len(load_qualification_ids()), 2000)
        self.assertGreater(len(qualifications), 2000)
        self.assertEqual(qualifications[0].qualification_id, "1284")
        self.assertEqual(qualifications[0].title, "Line Patrolling Man (Oil  Gas)")
        self.assertEqual(qualifications[0].sector_name, "Hydrocarbon")

    def test_build_education_record_returns_blank_for_unmatched_occupation(self):
        occupation = {"slug": "x", "title": "Unknown Occupation"}
        record = build_education_record(occupation, None, "unmatched", force=False, delay=0.0)
        self.assertEqual(
            record,
            {
                "slug": "x",
                "title": "Unknown Occupation",
                "education": "",
                "education_bucket": "",
                "education_source_url": "",
                "education_source_type": "",
                "match_type": "unmatched",
            },
        )


if __name__ == "__main__":
    unittest.main()
