from __future__ import annotations

import unittest

from india.build_nco_master import parse_occupation_entries


class BuildNcoMasterTest(unittest.TestCase):
    def test_parse_occupation_entries_extracts_code_and_title(self) -> None:
        text = """
6111.0101
Paddy Farmer

Paddy Farmer cultivates paddy as per the package.

Qualification Pack Details:
QP NOS Reference AGR/Q0101

6111.0201
Wheat Cultivator
"""
        records = parse_occupation_entries(text, "sample.pdf")
        self.assertEqual(
            records,
            [
                {
                    "title": "Paddy Farmer",
                    "slug": "paddy-farmer",
                    "occupation_id": "61110101",
                    "nco_code": "61110101",
                    "category": "Agriculture and Fishery",
                    "source_urls": ["sample.pdf"],
                    "ncs_id": None,
                    "source_type": "nco_2015",
                    "nco_description": "Paddy Farmer cultivates paddy as per the package",
                },
                {
                    "title": "Wheat Cultivator",
                    "slug": "wheat-cultivator",
                    "occupation_id": "61110201",
                    "nco_code": "61110201",
                    "category": "Agriculture and Fishery",
                    "source_urls": ["sample.pdf"],
                    "ncs_id": None,
                    "source_type": "nco_2015",
                    "nco_description": "",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
