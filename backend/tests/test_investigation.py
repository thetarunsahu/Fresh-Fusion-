"""Regression checks use only a temporary SQLite DB and temporary image files.

Run from root: backend/.venv/Scripts/python.exe -m unittest discover -s backend/tests -v
"""
import atexit
from copy import deepcopy
from datetime import datetime, timedelta
from io import BytesIO
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
TEMP = tempfile.TemporaryDirectory(prefix="freshfusion-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(TEMP.name) / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(Path(TEMP.name) / "uploads")
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import FruitImage, FruitSample, SensorReading, FusionResult, HumanVerification
from app.services.sensor_assessment import assess_sensors
from app.services.physical_validation import evaluate_physical_evidence

def cleanup():
    engine.dispose()
    TEMP.cleanup()
atexit.register(cleanup)

class InvestigationTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.client = TestClient(app)
        auth = self.client.post('/api/v1/auth/register', json={
            'email': 'regression@freshfusion.local',
            'password': 'FreshFusionTest123!',
            'full_name': 'FreshFusion Regression',
            'role': 'operator',
        })
        self.assertEqual(auth.status_code, 201, auth.text)
        self.client.headers.update({'Authorization': f"Bearer {auth.json()['access_token']}"})
        sample = self.client.post('/api/v1/samples', json={'fruit_type': 'Apple'})
        self.assertEqual(sample.status_code, 201, sample.text)
        self.sample = sample.json()['sample_id']

    def tearDown(self):
        self.client.close()

    def packet(self, **overrides):
        return {'sample_id': self.sample, 'device_id': 'ESP32_01', 'temperature': 24, 'humidity': 60, 'mq135_raw': 500, **overrides}

    def image_bytes(self):
        image = Image.new('RGB', (400, 300), 'white')
        ImageDraw.Draw(image).ellipse((110, 55, 290, 245), fill=(205, 35, 30))
        data = BytesIO(); image.save(data, format='JPEG')
        return data.getvalue()

    def evidence(self, healthy=90, same_hash=False):
        """Synthetic analysis fixtures test gating, not real CV accuracy."""
        with SessionLocal() as db:
            for index, view in enumerate(['front', 'left', 'back', 'front']):
                fingerprint = '0' * 16 if same_hash else ['0' * 16, 'f' * 16, 'f0' * 8, '0' * 16][index]
                db.add(FruitImage(sample_id=self.sample, angle=f'live-{view}', filename=f'fixture-{index}.jpg', url=f'/uploads/fixture-{index}.jpg',
                    analysis={'quality': {'fruit_present': True}, 'identity': {'fruit': 'Apple', 'confidence': 85},
                              'presentation': {'screen_suspicion_pct': 0, 'fruit_fingerprint': fingerprint},
                              'defects': {'healthy_surface_estimate_pct': healthy}, 'color': {'brown_pct': 0, 'dark_pct': 0},
                              'ai': {'status': 'model_not_trained'}}, uploaded_at=datetime.utcnow() + timedelta(milliseconds=index)))
            db.commit()

    def summary(self):
        response = self.client.get(f'/api/v1/samples/{self.sample}/investigation')
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_empty_and_invalid_telemetry_rejected(self):
        for packet in [{}, self.packet(mq135_raw=None), self.packet(mq135_raw=4096), self.packet(humidity=101), self.packet(temperature=-1)]:
            self.assertEqual(self.client.post('/api/v1/sensors/readings', json=packet).status_code, 422)
        with SessionLocal() as db:
            self.assertEqual(db.query(SensorReading).count(), 0)
        self.assertFalse(self.summary()['decision']['verdict_ready'])

    def test_raw_adc_contributes_without_ppm(self):
        def reading(raw):
            return SensorReading(device_id='ESP32_01', temperature=24, humidity=60, mq135_raw=raw, captured_at=datetime.utcnow())
        low, high = assess_sensors([reading(100)]), assess_sensors([reading(3000)])
        self.assertGreater(low['score'], high['score'])
        self.assertEqual(high['latest']['gas_ppm'], None)
        self.assertAlmostEqual(high['latest']['relative_gas_response'], 3000 / 4095, places=4)
        self.assertIn('not calibrated ppm', high['note'])

    def test_simulator_cannot_unlock_but_hardware_recomputes(self):
        self.evidence()
        r = self.client.post('/api/v1/sensors/readings', json=self.packet(device_id='SIMULATOR', source='hardware'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['source'], 'simulator')
        report = self.summary()
        self.assertFalse(report['decision']['verdict_ready'])
        self.assertIsNone(report['analysts']['sensor']['score'])
        self.assertEqual(report['status'], 'WAITING FOR ESP32')
        self.client.post('/api/v1/sensors/readings', json=self.packet())
        self.assertTrue(self.summary()['decision']['verdict_ready'])
        with SessionLocal() as db:
            self.assertEqual(db.query(FusionResult).count(), 2)
            self.assertTrue(db.query(FusionResult).order_by(FusionResult.id.desc()).first().components['validation']['verdict_ready'])

    def test_read_only_summary_expires_stale_evidence(self):
        self.evidence()
        self.client.post('/api/v1/sensors/readings', json=self.packet())
        self.assertTrue(self.summary()['decision']['verdict_ready'])
        with SessionLocal() as db:
            db.query(SensorReading).update({'captured_at': datetime.utcnow() - timedelta(seconds=60)})
            db.commit(); count = db.query(FusionResult).count()
        report = self.summary()
        self.assertFalse(report['decision']['verdict_ready'])
        self.assertIsNone(report['decision']['freshness_score'])
        with SessionLocal() as db:
            self.assertEqual(count, db.query(FusionResult).count())

    def test_empty_scene_and_old_frames_lock_verdict(self):
        self.evidence()
        self.client.post('/api/v1/sensors/readings', json=self.packet())
        with SessionLocal() as db:
            db.add(FruitImage(sample_id=self.sample, angle='live-front', filename='empty.jpg', url='/uploads/empty.jpg', analysis={'quality': {'fruit_present': False}}, uploaded_at=datetime.utcnow()+timedelta(seconds=1)))
            db.commit()
        self.assertFalse(self.summary()['decision']['verdict_ready'])
        with SessionLocal() as db:
            db.query(FruitImage).update({'uploaded_at': datetime.utcnow()-timedelta(minutes=4)})
            db.commit()
        self.assertEqual(self.summary()['evidence']['physical_validation']['status'], 'no_fruit')

    def test_relabelled_identical_views_do_not_pass(self):
        self.evidence(same_hash=True)
        with SessionLocal() as db:
            row=db.query(FruitImage).order_by(FruitImage.id.desc()).first(); row.angle='live-top'; db.commit()
        self.client.post('/api/v1/sensors/readings', json=self.packet())
        self.assertFalse(self.summary()['decision']['verdict_ready'])

    def test_conflicting_visual_and_sensor_scores_are_locked(self):
        self.evidence(healthy=10)
        self.client.post('/api/v1/sensors/readings', json=self.packet(mq135_raw=0))
        report=self.summary()
        self.assertEqual(report['status'], 'CONFLICTING EVIDENCE')
        self.assertIsNone(report['decision']['freshness_score'])
        self.assertTrue(report['critic']['contradictions'])

    def test_active_target_not_changed_by_history_reads(self):
        newer=self.client.post('/api/v1/samples', json={'fruit_type':'Banana'}).json()['sample_id']
        self.summary()
        self.client.get(f'/api/v1/samples/{self.sample}/bundle')
        self.assertEqual(self.client.get('/api/v1/samples/active').json()['sample_id'], newer)
        self.client.put(f'/api/v1/samples/{self.sample}/active')
        packet=self.packet();packet.pop('sample_id')
        self.assertEqual(self.client.post('/api/v1/sensors/readings',json=packet).json()['sample_id'],self.sample)

    def test_human_truth_is_separate_and_persistent(self):
        self.assertEqual(self.client.post(f'/api/v1/samples/{self.sample}/verification',json={'action':'accept'}).status_code,409)
        self.assertEqual(self.client.post(f'/api/v1/samples/{self.sample}/verification',json={'action':'ground_truth'}).status_code,422)
        response=self.client.post(f'/api/v1/samples/{self.sample}/verification',json={'action':'ground_truth','ground_truth':'ripe','notes':'Independent observation'})
        self.assertEqual(response.status_code,201)
        report=self.summary()
        self.assertEqual(report['human_verifications'][0]['ground_truth'],'ripe')
        self.assertFalse(report['decision']['verdict_ready'])
        stats=self.client.get('/api/v1/datasets/validation').json()
        self.assertEqual(stats['human_labelled_inspections'],1)
        self.assertEqual(stats['labelled_images'],0)
        self.assertTrue(all(metric['value'] is None for metric in stats['metrics'].values()))

    def test_actual_camera_upload_and_websocket_paths(self):
        with self.client.websocket_connect(f'/ws/live/{self.sample}') as socket:
            response=self.client.post('/api/v1/images/stream-frame',data={'sample_id':self.sample,'view':'left','ground_truth':'fresh'},files={'file':('test.jpg',self.image_bytes(),'image/jpeg')})
            self.assertEqual(response.status_code,200,response.text)
            frame=response.json()
            self.assertEqual(frame['angle'],'live-left')
            self.assertTrue(frame['uploaded_at'].endswith('+00:00'))
            self.assertEqual(socket.receive_json()['type'],'vision-frame')
            self.assertEqual(self.client.get(frame['url']).status_code,200)
            for artifact in frame['analysis']['artifacts'].values():
                self.assertEqual(self.client.get(artifact).status_code,200)
        response=self.client.post('/api/v1/images/upload',data={'sample_id':self.sample,'angle':'top'},files={'file':('test.jpg',self.image_bytes(),'image/jpeg')})
        self.assertEqual(response.status_code,200,response.text)
        self.assertGreaterEqual(len(self.summary()['timeline']),3)

    def test_active_stream_mismatch_rejected(self):
        self.client.post('/api/v1/samples',json={'fruit_type':'Banana'})
        response=self.client.post('/api/v1/images/stream-frame',data={'sample_id':self.sample,'view':'front'},files={'file':('test.jpg',self.image_bytes(),'image/jpeg')})
        self.assertEqual(response.status_code,409)

    def test_legacy_empty_reading_is_not_healthy(self):
        with SessionLocal() as db:
            db.add(SensorReading(sample_id=self.sample, device_id='ESP32_01'))
            db.commit()
        self.assertIsNone(self.summary()['analysts']['sensor']['score'])

    def test_accept_snapshots_eligible_assessment(self):
        self.evidence()
        self.client.post('/api/v1/sensors/readings',json=self.packet())
        response=self.client.post(f'/api/v1/samples/{self.sample}/verification',json={'action':'accept'})
        self.assertEqual(response.status_code,201,response.text)
        self.assertTrue(response.json()['assessment']['verdict_ready'])

    def test_missing_reference_is_warning_not_fake_match(self):
        with patch('app.services.datasets.reference_index_status',return_value={'ready':False}):
            report=self.summary()
        self.assertTrue(any('reference index' in item for item in report['critic']['warnings']))
        self.assertFalse(report['decision']['verdict_ready'])

    def test_screen_and_low_identity_are_blocked(self):
        self.evidence()
        self.client.post('/api/v1/sensors/readings',json=self.packet())
        with SessionLocal() as db:
            for row in db.query(FruitImage):
                analysis=deepcopy(row.analysis)
                analysis['presentation']['screen_suspicion_pct']=95
                row.analysis=analysis
            db.commit()
        self.assertEqual(self.summary()['status'],'PHYSICAL FRUIT NOT VERIFIED')
        with SessionLocal() as db:
            for row in db.query(FruitImage):
                analysis=deepcopy(row.analysis)
                analysis['presentation']['screen_suspicion_pct']=0
                analysis['identity']['confidence']=20
                row.analysis=analysis
            db.commit()
        self.assertFalse(self.summary()['decision']['verdict_ready'])

    def test_auto_switch_updates_capture_target_and_notifies_old_channel(self):
        analysis={'quality':{'fruit_present':True},'identity':{'fruit':'Banana','confidence':90},'presentation':{'screen_suspicion_pct':0}}
        with patch('app.api.images.analyze_image',return_value=analysis), self.client.websocket_connect(f'/ws/live/{self.sample}') as socket:
            for index in range(3):
                response=self.client.post('/api/v1/images/stream-frame',data={'sample_id':self.sample,'view':'front'},files={'file':('test.jpg',self.image_bytes(),'image/jpeg')})
                self.assertEqual(response.status_code,200,response.text)
                event=socket.receive_json()
            self.assertTrue(event['data']['auto_detection']['sample_changed'])
            new_id=event['data']['sample_id']
            self.assertNotEqual(new_id,self.sample)
            self.assertEqual(self.client.get('/api/v1/samples/active').json()['sample_id'],new_id)
        self.assertFalse(self.client.get(f'/api/v1/samples/{new_id}/investigation').json()['decision']['verdict_ready'])

    def test_sensor_only_fusion_history_is_bounded(self):
        with patch('app.services.fusion.RESULT_KEEP',3):
            for _ in range(5):
                self.assertEqual(self.client.post('/api/v1/sensors/readings',json=self.packet()).status_code,200)
        with SessionLocal() as db:
            self.assertEqual(db.query(FusionResult).count(),3)
            self.assertEqual(db.query(SensorReading).count(),5)

if __name__ == '__main__':
    unittest.main()
