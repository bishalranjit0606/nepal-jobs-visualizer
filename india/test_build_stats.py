import sys
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from build_stats import (
    build_stats_rows,
    code_to_division_code,
    code_to_group_code,
    extract_table25_group_shares,
    extract_table50_division_wages,
)


TABLE25_SNIPPET = """
Table (25): Percentage distribution of workers in usual status (ps+ss) by occupation group/ sub-division /division
as per National Classification of Occupation (NCO) 2015

all-India
111                                          0.05           0.06          0.05            0.11        0.09      0.10          0.07           0.07          0.07
112                                          1.13           0.25          0.79            5.57        2.07      4.66          2.43           0.60          1.79
214                                          0.09           0.01          0.06            0.92        0.16      0.72          0.33           0.04          0.23
611                                         32.80          30.87         32.07            2.71        3.52      2.92         23.95          25.56         24.51
952                                          0.26           0.09          0.20            0.48        0.31      0.44          0.33           0.13          0.26
"""


TABLE50_SNIPPET = """
Table (50): Average wage/salary earnings (Rs.) during the preceding calendar month from regular wage/salaried employment among the regular wage salaried employees in
CWS by occupation Divisions (1- digit code of NCO-2015)

all India
                                                                                  rural+urban                      person
Average wage/salary earnings (Rs.)                 42,993          35,776           24,199         23,616          14,628           11,319       15,350       15,906       10,667                21,047
sample no. of regular wage/salaried
employee*                                           1,797              8,888         3,746          4,908              9,810              423     4,779        4,920        7,023                46,294
"""


class BuildStatsTests(unittest.TestCase):
    def test_code_helpers_extract_group_and_division(self):
        self.assertEqual(code_to_group_code("2141.0900"), "214")
        self.assertEqual(code_to_group_code("6116.0101"), "611")
        self.assertEqual(code_to_division_code("2141.0900"), "2")
        self.assertEqual(code_to_division_code("6116.0101"), "6")

    def test_extract_table25_group_shares_uses_all_india_person_column(self):
        shares = extract_table25_group_shares(TABLE25_SNIPPET)

        self.assertEqual(shares["111"], 0.07)
        self.assertEqual(shares["214"], 0.23)
        self.assertEqual(shares["611"], 24.51)
        self.assertEqual(shares["952"], 0.26)

    def test_extract_table50_division_wages_uses_rural_urban_person_row(self):
        wages = extract_table50_division_wages(TABLE50_SNIPPET)

        self.assertEqual(wages["1"], 42993)
        self.assertEqual(wages["2"], 35776)
        self.assertEqual(wages["6"], 11319)
        self.assertEqual(wages["9"], 10667)

    def test_build_stats_rows_maps_nco_codes_to_group_shares_and_division_pay(self):
        occupations = [
            {
                "title": "Agricultural Engineer",
                "slug": "agricultural-engineer",
                "nco_code": "2141.0900",
                "category": "Agriculture",
                "ncs_id": "3295",
            },
            {
                "title": "Agriculture Extension Executive",
                "slug": "agriculture-extension-executive",
                "nco_code": "6116.0101",
                "category": "Agriculture",
                "ncs_id": "3301",
            },
        ]

        rows = build_stats_rows(
            occupations,
            group_shares={"214": 0.23, "611": 24.51},
            division_wages={"2": 35776, "6": 11319},
            education_by_slug={
                "agricultural-engineer": {
                    "education": "Graduate",
                    "education_bucket": "Graduate",
                    "education_source_url": "https://www.nqr.gov.in/qualifications/123",
                    "education_source_type": "NQR eligibility criteria",
                }
            },
        )

        first = rows[0]
        second = rows[1]

        self.assertEqual(first["employment_share"], 0.23)
        self.assertEqual(first["pay_monthly"], 35776)
        self.assertEqual(first["pay_annual"], 429312)
        self.assertEqual(first["education"], "Graduate")
        self.assertEqual(first["education_bucket"], "Graduate")
        self.assertEqual(second["employment_share"], 24.51)
        self.assertEqual(second["pay_monthly"], 11319)
        self.assertEqual(second["pay_annual"], 135828)
        self.assertEqual(second["education"], "")
        self.assertEqual(second["education_bucket"], "")

    def test_build_stats_rows_apportions_group_share_across_same_group(self):
        occupations = [
            {
                "title": "One",
                "slug": "one",
                "nco_code": "6116.0101",
                "category": "Agriculture",
                "ncs_id": "1",
            },
            {
                "title": "Two",
                "slug": "two",
                "nco_code": "6116.0102",
                "category": "Agriculture",
                "ncs_id": "2",
            },
        ]

        rows = build_stats_rows(
            occupations,
            group_shares={"611": 24.51},
            division_wages={"6": 11319},
        )

        self.assertEqual(rows[0]["employment_share_group"], 24.51)
        self.assertEqual(rows[1]["employment_share_group"], 24.51)
        self.assertEqual(rows[0]["employment_share"], 12.255)
        self.assertEqual(rows[1]["employment_share"], 12.255)


if __name__ == "__main__":
    unittest.main()
