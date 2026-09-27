import unittest
from core.scanner import ProfileSnapshot
from core.analyzer import string_similarity, analyze_impersonation

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.original = ProfileSnapshot(
            username="official_brand",
            full_name="Official Brand",
            biography="The only official account.",
            followers=50000,
            following=100,
            is_private=False,
            is_verified=True,
            profile_pic_url="http://example.com/pic1.jpg",
            external_url=None
        )
        
        self.suspect = ProfileSnapshot(
            username="official_brand_support",
            full_name="Official Brand",
            biography="The only official account.",
            followers=12,
            following=400,
            is_private=False,
            is_verified=False,
            profile_pic_url="http://example.com/pic2.jpg",
            external_url=None
        )

    def test_string_similarity(self):
        self.assertEqual(string_similarity("match", "match"), 1.0)
        self.assertTrue(string_similarity("target", "targt") > 0.8)
        self.assertEqual(string_similarity("", ""), 1.0)
        self.assertEqual(string_similarity("something", ""), 0.0)

    def test_analyze_impersonation_critical(self):
        result = analyze_impersonation(self.original, self.suspect)
        
        self.assertEqual(result["risk_level"], "CRITICAL")
        self.assertTrue(result["metrics"]["follower_disparity_flag"])
        self.assertTrue(result["risk_score"] > 80.0)

    def test_analyze_impersonation_low(self):
        innocent_user = ProfileSnapshot(
            username="random_person",
            full_name="John Doe",
            biography="Just a guy.",
            followers=400,
            following=300,
            is_private=True,
            is_verified=False,
            profile_pic_url="",
            external_url=None
        )
        result = analyze_impersonation(self.original, innocent_user)
        self.assertEqual(result["risk_level"], "LOW")
        self.assertFalse(result["metrics"]["follower_disparity_flag"])

if __name__ == "__main__":
    unittest.main()