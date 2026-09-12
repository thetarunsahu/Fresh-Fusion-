import unittest

from pydantic import ValidationError

from app.schemas import VerificationIn
from app.services.fruit_identity_extension import enhance_identity
from app.services.validation_metrics import split_for_key


class ProductP1Tests(unittest.TestCase):
    def tomato_analysis(self):
        return {
            "quality": {"fruit_present": True},
            "identity": {
                "fruit": "Unknown",
                "confidence": 20.0,
                "shape": {
                    "circularity": 0.78,
                    "aspect_ratio": 1.12,
                    "solidity": 0.91,
                },
                "supported": ["Apple", "Banana"],
            },
            "color": {
                "red_pct": 46.0,
                "green_pct": 5.0,
                "yellow_pct": 4.0,
                "brown_pct": 1.0,
            },
        }

    def test_operator_selected_tomato_gets_visual_compatibility_support(self):
        result = enhance_identity(self.tomato_analysis(), "Tomato")
        identity = result["identity"]
        self.assertEqual(identity["fruit"], "Tomato")
        self.assertIn("Tomato", identity["supported"])
        self.assertGreaterEqual(identity["confidence"], 60.0)
        self.assertIn("tomato_candidate", identity)

    def test_tomato_support_does_not_claim_trained_classifier(self):
        result = enhance_identity(self.tomato_analysis(), "Tomato")
        self.assertIn("not a trained Tomato classifier", result["identity"]["note"])

    def test_validation_split_is_deterministic_per_specimen(self):
        first = split_for_key("APPLE-01")
        second = split_for_key("APPLE-01")
        self.assertEqual(first, second)
        self.assertIn(first, {"train", "validation", "test"})

    def test_override_requires_label_and_reason(self):
        with self.assertRaises(ValidationError):
            VerificationIn(action="override", ground_truth=None, notes="because")
        with self.assertRaises(ValidationError):
            VerificationIn(action="override", ground_truth="ripe", notes="")
        value = VerificationIn(action="override", ground_truth="ripe", notes="Visual inspection disagrees")
        self.assertEqual(value.action, "override")


if __name__ == "__main__":
    unittest.main()
