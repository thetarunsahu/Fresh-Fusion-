# FreshFusion Investigation Foundation

## Scope

FreshFusion reuses one authoritative FastAPI/OpenCV/reference/physical-validation/fusion path. The analysts are deterministic adapters over existing evidence; they are not all LLM agents. Ollama/Gemma is optional, explanation-only, and never required to unlock a verdict.

No model accuracy, calibrated MQ135 gas concentration, guaranteed monocular liveness, or food-safety certification is implied by this architecture.

## Investigation flow

```text
Physical Fruit
   |
   +-- Phone Camera
   +-- ESP32 Sensors
          |
          v
     Evidence Store
          |
   +------+-------+---------+
   |              |         |
 Vision         Sensor   Reference
 Analyst        Analyst   Analyst
   \              |         /
    +------ Multi-view ----+
               |
               v
       Evidence Agreement
               |
               v
      Freshness Hypothesis
               |
               v
        Evidence Critic
               |
               v
 Deterministic Fusion/Confidence
               |
      +--------+---------+
      |                  |
 Assessment          More Evidence
      |
      v
 Optional Gemma Explanation
      |
      v
 Human Verification / Validation
```

## Current frontend responsibilities

| Area | Files | Responsibility |
| --- | --- | --- |
| Workspace/navigation | `frontend/src/App.jsx`, `layout/WorkspaceLayout.jsx` | Compose features; keep algorithms outside the shell |
| Overview | `features/overview/Overview.jsx` | Explain workflow and truthful availability |
| Live Inspection | `features/inspection/LiveInspection.jsx` | Camera/sensor evidence and capture controls |
| Investigation | `features/investigation/` | Analysts, Evidence Agreement, critic, final assessment, Gemma and human review |
| Evidence | `features/evidence/EvidenceTimeline.jsx` | Chronological stored/reconstructed evidence |
| Dataset & Validation | `features/validation/Validation.jsx` | Human-labelled counts, preliminary metrics and frozen validation runs |
| History | `features/history/History.jsx` | Browse prior inspections without changing hardware capture target |
| Shared state/API | `src/api.js`, `hooks/useInspection.js`, `shared/` | API contracts, stale-response protection and formatting |

Protected integration boundaries remain camera upload, sensor ingestion, `image_analysis.py`, `physical_validation.py`, `sensor_assessment.py`, `fusion.py`, and inspection routing.

## Investigation API contract

### Read current state

`GET /api/v1/samples/{id}/investigation`

Response sections:

```text
inspection_id, sample, status
evidence: camera, sensors, reference, physical_validation
analysts: vision, sensor, reference, multiview
agreement: status, freshness_relationship, matrix, note
critic: status, blocking, supporting_evidence, missing_evidence, contradictions, warnings
decision: status, verdict_ready, label, freshness_score, confidence, risk, reason, confidence_method
timeline, timeline_note, human_verifications
```

Unavailable final label, score and confidence are `null`.

Critic states include:

- `PASSED`
- `WARNING`
- `BLOCKED`
- `NEEDS MORE DATA`

Decision states include:

- `INCONCLUSIVE`
- `MORE EVIDENCE REQUIRED`
- `PHYSICAL FRUIT NOT VERIFIED`
- `WAITING FOR ESP32`
- `CONFLICTING EVIDENCE`
- `AWAITING HUMAN VERIFICATION`

The legacy bundle may retain a database-compatible non-null placeholder score when locked; the investigation contract never exposes that placeholder as a final assessment.

### Save deterministic snapshot

`POST /api/v1/samples/{id}/investigation/snapshot?trigger=manual-ui`

Stores an append-only `InvestigationRun` containing the deterministic evidence/analyst/agreement/critic/decision state.

`GET /api/v1/samples/{id}/investigation/snapshots`

Lists saved snapshots.

### Explain with local Gemma

`POST /api/v1/samples/{id}/investigation/explain`

Gemma receives only already-computed sample, analyst, agreement, critic and decision evidence. It may summarize evidence, contradictions, missing evidence and a next step. It must not manufacture a freshness score or override the deterministic gate.

A successful explanation is persisted with the investigation snapshot that it summarized.

## Evidence Agreement semantics

The matrix deliberately does **not** pretend that every module casts an equivalent freshness vote.

- Vision: freshness-bearing experimental score band
- Sensor: freshness-bearing experimental score band
- Reference: contextual published-label/similarity evidence
- Multi-view: physical-evidence gate

Only Vision and Sensor are compared as freshness-bearing score bands. Reference similarity remains contextual and Multi-view remains a physical gate.

This preserves the meaning of each evidence source instead of creating a misleading `3/4 agents agree` statistic.

## Human verification

`POST /api/v1/samples/{id}/verification`

Example:

```json
{
  "action":"ground_truth",
  "ground_truth":"ripe",
  "reviewer":"TS",
  "notes":"Independent physical observation"
}
```

Actions:

- `accept`
- `incorrect`
- `ground_truth`

FreshFusion ground-truth labels:

- `fresh`
- `ripe`
- `overripe`
- `spoiled`

Human reviews are append-only and remain separate from public dataset labels and model/system predictions. `accept` is rejected while the current verdict is locked.

## Database and migrations

Current persistent entities include:

```text
FruitSample
SensorReading
FruitImage
FusionResult
InspectionControl
HumanVerification
InvestigationRun
ValidationRun
ModelVersion
```

Formal migrations now use Alembic:

```text
backend/alembic.ini
backend/alembic/env.py
backend/alembic/versions/
```

`start_freshfusion.ps1` applies `alembic upgrade head` before starting FastAPI. `Base.metadata.create_all` remains a compatibility bootstrap for a fresh prototype database.

Before future schema changes or the final event day, back up the database:

```powershell
.\backup_freshfusion.ps1 -IncludeUploads
```

Never delete/reset a live database merely to make a migration succeed.

## Sensor semantics

Current hardware packets require finite:

- temperature: 0-50 °C prototype input range
- humidity: 0-100% RH
- `mq135_raw`: 0-4095 12-bit ADC range

These bounds are data-validation constraints, not sensor-accuracy claims.

`source` is declared as `hardware` or `simulator`. Device IDs beginning with SIM/TEST and explicitly tagged simulator packets are treated as simulator evidence. This provenance is not cryptographic authentication.

Simulator readings may be displayed but cannot unlock a physical verdict.

Current experimental gas feature:

```text
relative_gas_response = mq135_raw / 4095
```

The existing fusion still uses an experimental raw-response penalty. This value is not ppm, ethylene concentration, clean-air calibration or food-safety evidence.

Use `docs/MQ135_EXPERIMENT_PROTOCOL.md` for empty-chamber baseline experiments before changing the signal direction/weight.

## Evidence-age and physical rules

Current prototype operational gates include:

- fresh eligible hardware sensor evidence within 45 seconds
- decision camera evidence within 180 seconds
- camera connection badge uses a shorter recent-frame window
- latest empty scene invalidates older positive evidence
- changed appearance is required; relabelling an identical image as multiple views does not satisfy physical evidence
- suspected screen/flat-reference evidence can block the verdict

These are operational prototype limits, not shelf-life thresholds.

Monocular verification is probabilistic and is not equivalent to depth sensing or guaranteed liveness.

## Pairing and history

- New inspection sets the active capture target.
- Desktop history selection and active hardware capture target are separate concepts.
- QR links include an inspection `sample_id`.
- A phone stays paired to that inspection until explicitly re-paired.
- Stale/mismatched stream uploads can be rejected.
- Firmware may omit `sample_id` and use the single-chamber active target.
- Independent multi-chamber/device-session authorization is future work.

## Validation metrics

`GET /api/v1/datasets/validation` now exposes two layers:

1. legacy-compatible metric fields for existing clients/tests;
2. an `evaluation` object derived from real human-ground-truth review snapshots.

When comparable records exist, FreshFusion can calculate:

- confusion matrix
- accuracy
- macro precision
- macro recall
- macro F1
- per-class precision/recall/F1/support

A record is comparable only when human ground truth was stored with a conclusive decision snapshot.

Results remain **PRELIMINARY** until an independent sample-level held-out test protocol is completed. One physical fruit is one validation sample; its multiple camera frames are not independent samples.

`POST /api/v1/datasets/validation-runs` freezes the current observational evaluation into a `ValidationRun`.

## Verification commands

```powershell
.\preflight_freshfusion.ps1
.\backup_freshfusion.ps1 -IncludeUploads

.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -v

cd frontend
npm install
npm run build
npx playwright install chromium
npm test
```

Automated fixtures validate software contracts; they do not prove real fruit accuracy, phone permissions, Wi-Fi behaviour, electronics, MQ135 calibration or false-accept/false-reject rates.

Physical verification must follow:

- `docs/REAL_WORLD_VALIDATION_PROTOCOL.md`
- `docs/MQ135_EXPERIMENT_PROTOCOL.md`
- `docs/DEMO_RUNBOOK.md`

## Remaining physical/research work

The software hardening branch provides the mechanisms for final validation, but the following cannot be marked complete without the actual prototype:

- real phone background/reconnect test
- real ESP32 reconnect/network test
- real Apple/Banana repeated inspections
- screen/photo false-accept/false-reject observation
- MQ135 empty-chamber baseline experiments
- enough human-labelled physical fruits to populate useful metrics
- independent sample-level held-out evaluation
- final full SIH rehearsal

Do not convert software readiness into a scientific-validation claim.
