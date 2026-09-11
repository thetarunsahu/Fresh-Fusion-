import unittest

from app.services.product_rules import recommendation, score_breakdown


class ProductP0Tests(unittest.TestCase):
    def test_unsupported_fruit_is_not_forced(self):
        result = recommendation("Mango", "fresh", verdict_ready=True)
        self.assertFalse(result["supported"])
        self.assertEqual(result["risk"], "unverified")

    def test_damage_is_separate_from_freshness(self):
        result = recommendation("Apple", "fresh", verdict_ready=True, visible_damage_pct=18)
        self.assertTrue(result["supported"])
        self.assertEqual(result["action"], "Normal sale / storage")
        self.assertIn("damage alone is not treated as spoilage", result["damage_note"])

    def test_score_breakdown_is_traceable(self):
        fusion = {
            "freshness_score": 80,
            "sensor_score": 75,
            "vision_score": 85,
            "components": {"validation": {"verdict_ready": True, "status": "physical_fruit_likely", "views_count": 3, "required_views": 3, "confidence": 88}},
        }
        result = score_breakdown(fusion)
        self.assertTrue(result["released"])
        self.assertAlmostEqual(result["sensor"]["contribution"], 36.0)
        self.assertAlmostEqual(result["vision"]["contribution"], 44.2)
        self.assertIn("0.48", result["formula"])

    def test_locked_score_has_no_fake_contribution(self):
        fusion = {
            "freshness_score": 50,
            "sensor_score": None,
            "vision_score": None,
            "components": {"validation": {"verdict_ready": False}},
        }
        result = score_breakdown(fusion)
        self.assertFalse(result["released"])
        self.assertIsNone(result["final_score"])
        self.assertIsNone(result["sensor"]["contribution"])


if __name__ == "__main__":
    unittest.main()
