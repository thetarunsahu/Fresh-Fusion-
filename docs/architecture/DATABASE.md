# Database Architecture

## Purpose

FreshFusion needs an audit trail, not only a latest score. The database preserves which inspection received which camera/sensor evidence, what the system assessed, what a human later verified, and which investigation/validation snapshot was saved.

## Current database layer

- SQLAlchemy ORM
- SQLite by default through `DATABASE_URL`
- PostgreSQL-compatible engine configuration is present, but PostgreSQL is not yet the physically verified primary prototype path
- `SessionLocal` manages request-scoped sessions
- `Base.metadata.create_all` remains as a compatibility/fresh-database fallback
- Alembic is now the formal migration mechanism used by the launcher before backend startup

## Current persistent entities

### `fruit_samples`

One inspection/sample record.

Important fields: sample ID, fruit type, variety/source, status and timestamps.

### `sensor_readings`

Time-series ESP32/simulator evidence linked to a sample.

Stores device ID, temperature, humidity, `mq135_raw`, optional legacy gas/VOC fields, RSSI/uptime, provenance/extra metrics and timestamp.

### `fruit_images`

Camera evidence linked to a sample.

Stores viewpoint, file URL, image dimensions, analysis JSON, optional ground-truth label and timestamp.

### `fusion_results`

Append-only system assessments containing freshness/sensor/vision scores, system label, confidence, risk, explanation, components JSON and timestamp.

### `inspection_control`

Single-chamber active capture target. Browsing history must not silently change this target.

### `human_verifications`

Append-only human review/audit records containing action, FreshFusion ground truth when supplied, reviewer/notes, assessment snapshot and timestamp.

### `investigation_runs`

Immutable investigation snapshots used for audit/debug/demo reproducibility.

Stores:

- sample ID
- trigger (`manual-ui`, `gemma-explanation`, etc.)
- evidence/analyst/agreement/critic/decision snapshot
- optional Gemma explanation
- timestamp

### `validation_runs`

Frozen validation snapshots derived from comparable human-ground-truth inspections.

Stores:

- run ID/name
- protocol
- comparable sample count
- metrics snapshot
- dataset/record snapshot
- timestamp

### `model_versions`

Model artifact provenance table for future validated ML deployments. Presence in this table must never be interpreted as proof of accuracy.

## Current relationship model

```text
FruitSample
  |-- SensorReading[]
  |-- FruitImage[]
  |-- FusionResult[]
  |-- InvestigationRun[]
  `-- HumanVerification[]  (linked by sample_id)

InspectionControl
  `-- active FruitSample

ValidationRun[]
  `-- frozen evaluation snapshots

ModelVersion[]
  `-- artifact provenance
```

## Data integrity rules

1. Public dataset labels and FreshFusion human ground truth are different concepts.
2. System predictions never overwrite human verification.
3. Human verification never rewrites historical model/fusion output.
4. Simulator readings may be stored but cannot unlock a physical verdict.
5. History browsing is read-only with respect to the active capture target.
6. Explicitly labelled/review-referenced evidence should not be deleted by ordinary preview retention.
7. Final UI results come from current gate semantics, not legacy placeholder scores.
8. Validation metrics are computed only from human ground-truth records that include a comparable conclusive decision snapshot.
9. Multiple camera views of one physical fruit are one validation sample, not independent samples.
10. Investigation/validation snapshots are audit records and should be treated as append-only.

## Alembic migration status

Alembic configuration now lives in:

```text
backend/alembic.ini
backend/alembic/env.py
backend/alembic/versions/
```

The first hardening migration adds:

- `investigation_runs`
- `validation_runs`
- `model_versions`

The launcher runs:

```text
python -m alembic -c backend/alembic.ini upgrade head
```

before starting FastAPI.

The baseline migration is intentionally additive and safe for the existing prototype database. Fresh databases still use SQLAlchemy metadata as a compatibility bootstrap after the migration stamp.

Before future schema changes:

1. run `backup_freshfusion.ps1`;
2. create a new Alembic revision;
3. never rewrite an already-applied migration;
4. test against a copy of the real database;
5. never delete/reset live demo data to solve a migration problem.

## Validation persistence

The live validation service compares the latest human ground-truth review per inspection with the decision snapshot stored at review time.

It can calculate real observational:

- confusion matrix
- accuracy
- macro precision
- macro recall
- macro F1
- per-class support/metrics

When comparable records exist these results remain labelled **PRELIMINARY**, because ordinary collected observations are not automatically an independent held-out scientific test set.

`POST /api/v1/datasets/validation-runs` freezes the current evaluation into `validation_runs` for later comparison.

## Investigation persistence

The normal investigation GET remains read-only and re-evaluates time-dependent gates.

Explicit snapshots can be saved through:

```text
POST /api/v1/samples/{sample_id}/investigation/snapshot
GET  /api/v1/samples/{sample_id}/investigation/snapshots
```

Gemma explanations also save an investigation snapshot automatically so the language explanation remains tied to the deterministic evidence/critic/decision state it summarized.

## Still planned / future scaling

### `device_sessions`

A future multi-device version should bind phone/ESP32/chamber identity to an inspection explicitly. The current single-chamber prototype uses `inspection_control` and inspection-specific phone pairing.

### `evidence_events`

The current Evidence Timeline can be reconstructed from stored image/sensor/fusion/review timestamps. A dedicated event table should be added only when reconstruction becomes insufficient or stronger event provenance is required.

## Backup/export

Use:

```powershell
.\backup_freshfusion.ps1
```

For a database + uploads backup:

```powershell
.\backup_freshfusion.ps1 -IncludeUploads
```

Backups are written under `.runtime/backups/`, which is ignored by Git.

Before the final demo, keep at least one offline copy of the database and important evidence outside the working repository directory.
