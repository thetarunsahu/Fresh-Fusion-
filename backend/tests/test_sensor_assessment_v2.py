"""Focused unit checks for FreshFusion V2 sensor evidence semantics."""
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.sensor_assessment import assess_sensors, eligible_sensors


def row(raw, *, seconds_ago=0, phase="fruit", uptime_ms=180000, device="ESP32_01"):
    return SimpleNamespace(
        id=int(raw),
        sample_id="TEST-01",
        device_id=device,
        temperature=24.0,
        humidity=60.0,
        mq135_raw=float(raw),
        gas_ppm=None,
        voc_index=None,
        rssi=-55.0,
        uptime_ms=uptime_ms,
        extra_metrics={"source": "hardware", "measurement_phase": phase},
        captured_at=datetime.utcnow() - timedelta(seconds=seconds_ago),
    )


class SensorAssessmentV2Tests(unittest.TestCase):
    def test_baseline_is_not_fruit_evidence_and_delta_is_reported(self):
        rows = [
            row(820, seconds_ago=0),
            row(610, seconds_ago=4, phase="baseline"),
            row(600, seconds_ago=8, phase="baseline"),
            row(605, seconds_ago=12, phase="baseline"),
        ]
        report = assess_sensors(rows)
        self.assertEqual(report["baseline"]["count"], 3)
        self.assertTrue(report["baseline"]["stable"])
        self.assertAlmostEqual(report["baseline"]["mq135_raw_mean"], 605.0)
        self.assertAlmostEqual(report["baseline_delta_raw"], 215.0)
        self.assertEqual(len(eligible_sensors(rows)), 1)
        self.assertEqual(report["health"]["evidence_quality"]["level"], "strong")

    def test_warming_sensor_does_not_unlock_hardware_evidence(self):
        warming = row(700, uptime_ms=30000)
        report = assess_sensors([warming])
        self.assertEqual(report["warmup"]["state"], "warming")
        self.assertFalse(report["physical_present"])
        self.assertEqual(report["health"]["evidence_quality"]["level"], "weak")

    def test_recent_sequence_exposes_direction_not_concentration(self):
        rows = [
            row(900, seconds_ago=0),
            row(820, seconds_ago=20),
            row(740, seconds_ago=40),
        ]
        report = assess_sensors(rows)
        self.assertTrue(report["trend"]["available"])
        self.assertEqual(report["trend"]["direction"], "rising")
        self.assertGreater(report["trend"]["raw_per_minute"], 0)
        self.assertIsNone(report["latest"]["gas_ppm"])


if __name__ == "__main__":
    unittest.main()
