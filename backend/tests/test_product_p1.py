import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from app.api.images import _identity_consensus, _publish_stable_identity
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

    def test_identity_consensus_rejects_apple_banana_flicker(self):
        history = [
            {"fruit": "Apple", "confidence": 84.0},
            {"fruit": "Banana", "confidence": 82.0},
            {"fruit": "Apple", "confidence": 83.0},
            {"fruit": "Banana", "confidence": 81.0},
        ]
        result = _identity_consensus("Apple", 85.0, history, required_frames=3)
        self.assertFalse(result["stable"])

    def test_identity_consensus_accepts_repeated_new_fruit(self):
        history = [
            {"fruit": "Apple", "confidence": 90.0},
            {"fruit": "Apple", "confidence": 88.0},
            {"fruit": "Banana", "confidence": 75.0},
            {"fruit": "Apple", "confidence": 86.0},
        ]
        result = _identity_consensus("Apple", 91.0, history, required_frames=3)
        self.assertTrue(result["stable"])
        self.assertGreaterEqual(result["candidate_frames"], 3)

    def test_stabilized_identity_preserves_raw_frame_diagnostic(self):
        analysis = {
            "identity": {"fruit": "Apple", "confidence": 79.0, "method": "raw"},
            "quality": {"fruit_present": True},
        }
        sample = SimpleNamespace(fruit_type="Banana")
        result = _publish_stable_identity(
            analysis,
            sample,
            {
                "identity_conflict": True,
                "pending_correction": True,
                "identity_consensus": {
                    "average_confidence": 81.0,
                    "candidate_frames": 2,
                    "required_frames": 3,
                },
            },
        )
        self.assertEqual(result["identity"]["fruit"], "Banana")
        self.assertEqual(result["raw_frame_identity"]["fruit"], "Apple")
        self.assertTrue(result["identity_state"]["identity_conflict"])

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
