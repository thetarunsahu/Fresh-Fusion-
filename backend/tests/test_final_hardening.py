import sys
from datetime import datetime
from pathlib import Path
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import Base
from app.models import FruitSample, HumanVerification, ValidationRun
from app.services.investigation_core.agreement import build_agreement
from app.services.validation import current_validation_snapshot, persist_validation_run


class FinalHardeningTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            db.add(FruitSample(sample_id="APP-TEST01", fruit_type="Apple"))
            db.commit()

    def tearDown(self):
        self.engine.dispose()

    def test_validation_uses_review_snapshot_and_real_ground_truth(self):
        with self.Session() as db:
            db.add(
                HumanVerification(
                    sample_id="APP-TEST01",
                    action="ground_truth",
                    ground_truth="ripe",
                    assessment={
                        "verdict_ready": True,
                        "label": "ripe",
                        "confidence": 80,
                        "freshness_score": 70,
                    },
                    created_at=datetime.utcnow(),
                )
            )
            db.commit()
            result = current_validation_snapshot(db)
            self.assertEqual(result["status"], "PRELIMINARY")
            self.assertEqual(result["sample_count"], 1)
            self.assertEqual(result["accuracy"], 100.0)
            self.assertEqual(result["confusion_matrix"]["rows"][1][1], 1)

            run = persist_validation_run(db, name="unit-test")
            self.assertEqual(run.sample_count, 1)
            self.assertEqual(db.query(ValidationRun).count(), 1)

    def test_locked_review_is_excluded_from_metrics(self):
        with self.Session() as db:
            db.add(
                HumanVerification(
                    sample_id="APP-TEST01",
                    action="ground_truth",
                    ground_truth="fresh",
                    assessment={"verdict_ready": False, "label": None},
                )
            )
            db.commit()
            result = current_validation_snapshot(db)
            self.assertEqual(result["status"], "NOT YET VALIDATED")
            self.assertEqual(result["sample_count"], 0)
            self.assertEqual(len(result["excluded"]), 1)

    def test_agreement_does_not_count_reference_or_multiview_as_freshness_votes(self):
        analysts = {
            "vision": {"provisional_score": 84},
            "sensor": {"score": 79},
            "reference": {"match": {"status": "ready", "match": "fresh_apple"}},
            "multiview": {"status": "physical_likely"},
        }
        result = build_agreement(
            analysts,
            {"contradictions": [], "missing_evidence": []},
            {"verdict_ready": True},
        )
        self.assertEqual(result["counted_sources"], 2)
        self.assertEqual(result["freshness_relationship"], "NEARBY")
        self.assertEqual(result["status"], "PARTIAL")
        self.assertIn("not", result["note"].lower())


if __name__ == "__main__":
    unittest.main()
