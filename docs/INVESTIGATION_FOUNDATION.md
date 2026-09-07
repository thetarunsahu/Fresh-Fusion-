# FreshFusion investigation foundation

## Scope and ownership

This layer reuses the existing FastAPI/OpenCV/reference/physical-validation/fusion pipeline. Analysts are deterministic adapters, not LLM agents. The optional Ollama work is separate and is not required for a verdict. No training, cloud deployment, authentication system or calibrated model was introduced by this foundation.

| Area | Files | Contributor responsibility |
| --- | --- | --- |
| Workspace/navigation | `frontend/src/App.jsx`, `layout/WorkspaceLayout.jsx` | Compose features; keep algorithms out of the shell |
| Overview | `features/overview/Overview.jsx` | Explain workflow and truthful availability |
| Live inspection | `features/inspection/LiveInspection.jsx` | Existing evidence dashboard and capture controls |
| Investigation | `features/investigation/` | Analyst/critic presentation and human verification |
| Evidence timeline | `features/evidence/EvidenceTimeline.jsx` | Safe independent teammate task |
| Dataset & validation | `features/validation/Validation.jsx` | Safe independent teammate task; real metrics only |
| History | `features/history/History.jsx` | Safe independent teammate task; browsing must not activate capture |
| Shared data | `src/api.js`, `hooks/useInspection.js`, `shared/` | API contracts, stale-response guards, formatting |
| Investigation backend | `backend/app/services/investigation_core/` | Evidence adapters, critic and decision presentation |
| Core algorithms | `image_analysis.py`, `physical_validation.py`, `fusion.py`, `sensor_assessment.py` | Coordinate changes with the core owner and run regression checks |
| Camera/hardware | `CameraStream.jsx`, `api/images.py`, `api/sensors.py`, `esp32/` | Protected integration boundaries; validate with physical hardware |

The package is named `investigation_core` to coexist with the previously committed `services/investigation.py` and optional Ollama integration. The investigation API now uses the modular package. The prior service remains preserved for comparison; do not build a second verdict path around it.

## API contract

Existing `/api/v1/samples`, `/sensors/readings`, `/images/upload`, `/images/stream-frame`, `/datasets/registry`, `/external/context`, `/ws/live/{sample_id}` and upload URLs remain available.

| Endpoint | Behavior |
| --- | --- |
| `GET /api/v1/samples/{id}/investigation` | Read-only current evidence, analysts, critic, decision, timeline, human reviews |
| `GET /api/v1/samples/active` | Explicit chamber capture target; newest-sample fallback only for older databases without a target |
| `PUT /api/v1/samples/{id}/active` | Explicitly switch the chamber target; no change on history reads |
| `POST /api/v1/samples/{id}/verification` | Append a human observation with an assessment snapshot |
| `GET /api/v1/datasets/validation` | Real reference counts, labelled-image/review counts, model artifact state, unavailable validation metrics |

Investigation response:

```text
inspection_id, sample, status
evidence: camera, sensors, reference, physical_validation
analysts: vision, sensor, reference, multiview
critic: status, blocking, supporting_evidence, missing_evidence, contradictions, warnings
decision: status, verdict_ready, label, freshness_score, confidence, risk, reason, confidence_method
timeline, timeline_note, human_verifications
```

Unavailable final label, score and confidence are `null`. Critic states are `PASSED`, `WARNING`, `BLOCKED`, `NEEDS MORE DATA`. Prototype calibration warnings remain visible even when an assessment is eligible. Decision states include `INCONCLUSIVE`, `MORE EVIDENCE REQUIRED`, `PHYSICAL FRUIT NOT VERIFIED`, `WAITING FOR ESP32`, `CONFLICTING EVIDENCE`, and `AWAITING HUMAN VERIFICATION`.

The legacy bundle retains its non-null score convention (50 when locked); clients must use `components.validation.verdict_ready`. The investigation contract never exposes that placeholder as a real final score. GET requests re-evaluate time-dependent gates without inserting fusion results. Sensor arrivals now recompute and broadcast, as image arrivals already did.

### Human verification

```json
{"action":"ground_truth","ground_truth":"ripe","reviewer":"team initials","notes":"Independent observation"}
```

Actions: `accept`, `incorrect`, `ground_truth`. Human labels: `fresh`, `ripe`, `overripe`, `spoiled`. `accept` is rejected with HTTP 409 if the current verdict is locked. `ground_truth` requires a label. Each record stores the current assessment and latest evidence IDs. Reviews do not overwrite system results, public labels, or all frame labels. Repeated reviews remain an audit trail, not multiple independent validation samples.

## Additive database change

Two new tables are created by the existing startup `Base.metadata.create_all` mechanism:

- `inspection_control`: one active sample ID for this single-chamber prototype.
- `human_verifications`: append-only review records and decision snapshots.

No existing columns are removed or changed, and no database is replaced. No external migration tool is required for this additive change. The DB user needs CREATE TABLE permission. Back up the database before first running any new version. A formal migration system remains future work.

Use `DATABASE_URL` to explicitly select the database. Default: repository-root `freshfusion.db`, not `backend/freshfusion.db`. Existing legacy classifications remain historical records, not proof that the current gate passed.

## Sensor semantics

Current prototype packets require finite `temperature` (0–50 °C, DHT11 operating range), `humidity` (0–100% RH), and `mq135_raw` (0–4095, 12-bit ADC range). These input bounds reject impossible/missing prototype measurements; they are not accuracy claims. Zero and saturation readings are allowed electrical endpoints, not proof of valid calibration.

`source` is `hardware` or `simulator` (default `hardware` for existing firmware). Device IDs starting `SIM` or `TEST`, and explicitly simulator-tagged packets, are classified as simulator regardless of a conflicting hardware declaration. This is declared provenance, **not authentication**. Simulator readings may be displayed but never contribute to a physical verdict. The UI's simulator button sends a fixed, explicitly labelled test packet; it generates no ppm/VOC values.

```text
relative_gas_response = mq135_raw / (2^12 - 1)
experimental gas penalty = relative_gas_response × 42
```

4095 is the electrical ADC range; firmware explicitly sets 12-bit resolution. 42 is the **existing experimental gas penalty cap**, reused as an unvalidated model weight, not a new calibration constant. This signal is not ppm, a clean-air baseline, an ethylene-specific measurement, or a calibrated biological response. A higher ADC fraction is provisionally assigned a larger penalty; that direction and weight require chamber experiments. Temperature/humidity penalties and the 48% sensor / 52% vision fusion weights are also uncalibrated existing prototype rules. Incoming optional ppm/VOC fields remain stored for compatibility but are not substituted for a validated gas model.

Only complete, declared hardware readings received within 45 seconds are eligible. Images used by the current decision must be within 180 seconds; the camera connection badge uses 20 seconds. These are explicit operational evidence-age limits, not shelf-life thresholds. The latest empty scene invalidates older positive evidence. Physical checks require changed appearance; four relabelled identical views do not bypass that requirement. A fruit/image mask is resized into alignment before planar comparison.

## Pairing and history

- New inspection sets the active capture target.
- Desktop selection and chamber activation are separate. History never redirects an ESP32.
- QR links include `?sample_id=...`. A phone stays paired to that inspection.
- If the capture target changes, the phone stops capture and offers explicit re-pairing. Stale stream uploads receive HTTP 409.
- The existing stable Apple/Banana auto-switch creates a new inspection and updates the active target when appropriate; the old WebSocket channel receives the routing event too.
- The firmware may omit `sample_id` and use the active chamber target. Multiple independent chambers/device binding are future work.

## Evidence retention and validation

Unlabelled live preview frames retain the existing rolling limit. Explicitly labelled frames and frames referenced by human reviews are protected from preview deletion. Human labels do not silently propagate to all earlier images. Timeline events come from stored sample/image/sensor/fusion/review timestamps; identity and reference events use the frame's timestamp and say so. Old preview frames may no longer exist.

The cached public index is optional. Missing it generates a warning, not fabricated reference data. Reference similarity is a handcrafted-feature comparison, not a learned probability or held-out accuracy. A missing trained model is reported as not deployed. Artifact presence is labelled unverified until inference and evaluation are actually demonstrated.

The existing `ai/export_dataset.py` is still experimental: it splits frames rather than physical fruit samples and can retain prior split files. **Do not use its validation accuracy as SIH evidence.** Tomorrow's validation task should add a sample-based immutable split manifest, preserve a held-out test set, and review labels before training. No model training is part of this foundation.

## Verification

```powershell
# Isolated temporary DB/uploads; does not open the live database for writing
.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -v

cd frontend
npm install
npm run build
npx playwright install chromium
npm test
```

On Windows with Edge already installed, `$env:PLAYWRIGHT_CHANNEL='msedge'; npm test` is an alternative to downloading Chromium. Browser tests use isolated API contract fixtures and a virtual camera; these are test inputs, not demonstration results. They check workflow navigation, stale responses/WebSocket disposal, human review and current view/label uploads after background/resume. Physical phone permission behavior, Wi-Fi, ESP32 electronics, actual gas response and multi-view false-accept/reject rates still require hardware tests.

## Tomorrow's teammate tasks

1. Evidence teammate: filtering, image previews and inspection exports in `features/evidence/`.
2. Dataset teammate: human-label review, sample-based train/validation/test manifests, real evaluation report ingestion in `features/validation/`.
3. History teammate: search/filter/pagination and review badges in `features/history/`.
4. Core owner: physical Front/Left/Back capture, reconnect/target-change tests, raw-sensor response experiments and calibrated fusion research. Avoid independent edits to camera/fusion contracts until coordinated.
