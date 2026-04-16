import unittest

import pandas as pd

from jv_mill_finder.cross_referencer import cross_reference
from jv_mill_finder.scorer import calculate_jv_score
from jv_mill_finder.utils import normalize_company_name


class CoreLogicTests(unittest.TestCase):
    def test_normalize_company_name(self):
        self.assertEqual(normalize_company_name("ABC Agro Pvt Ltd"), "ABC")

    def test_cross_reference_exact_match(self):
        google_df = pd.DataFrame(
            [
                {
                    "place_id": "1",
                    "name": "Sharma Rice Industries Pvt Ltd",
                    "formatted_address": "Karnal, Haryana 132001",
                    "city": "Karnal",
                    "state": "Haryana",
                }
            ]
        )
        apeda_df = pd.DataFrame(
            [
                {
                    "Exporter Name": "Sharma Rice Industries",
                    "Address": "Karnal, Haryana 132001",
                    "short_name": "SHARMA RICE",
                    "pincode": "132001",
                }
            ]
        )

        out = cross_reference(google_df, apeda_df)
        self.assertEqual(out.iloc[0]["classification"], "ALREADY EXPORTING - SKIP")

    def test_score_calculation(self):
        row = pd.Series(
            {
                "phone_number": "+91 9876543210",
                "website": "https://example.com",
                "rating": 4.2,
                "user_ratings_total": 25,
                "city": "Karnal",
                "types": ["food_producer"],
                "opening_hours": True,
            }
        )
        self.assertGreaterEqual(calculate_jv_score(row), 90)

    def test_score_calculation_low_signal(self):
        row = pd.Series(
            {
                "phone_number": "",
                "website": "",
                "rating": 3.2,
                "user_ratings_total": 8,
                "city": "Meerut",
                "types": ["point_of_interest"],
                "opening_hours": False,
            }
        )
        self.assertEqual(calculate_jv_score(row), 5)


if __name__ == "__main__":
    unittest.main()
