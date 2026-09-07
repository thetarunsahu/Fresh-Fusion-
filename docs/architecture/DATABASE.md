# Database Architecture

## Purpose

FreshFusion needs an audit trail, not only a latest score. The database must preserve which inspection received which camera/sensor evidence, what the system assessed, what a human later verified, and which evidence was used at each stage.

## Current database layer

- SQLAlchemy ORM
- SQLite by default through `DATABASE_URL`
- PostgreSQL-compatible engine configuration is present, but PostgreSQL is not yet the default physically verified development path
- `SessionLocal` manages request-scoped sessions
- startup currently uses `Base.metadata.create_all`

## Current persistent entities

### `fruit_samples`

One inspection/sample record.

Important fields:

- `sample_id`
- `fruit_type`
- `variety`
- `source`
- `status`
- timestamps

### `sensor_readings`

Time-series ESP32/simulator evidence linked to a sample.

Stores:

- device ID
- temperature
- humidity
- `mq135_raw`
- optional legacy gas/VOC fields
- RSSI / uptime
- extra metrics / provenance
- capture timestamp

### `fruit_images`

Camera evidence linked to a sample.

Stores:

- viewpoint/angle
- file path/URL
- image dimensions
- analysis JSON
- optional ground-truth label
- upload timestamp

### `fusion_results`

Append-only system assessments.

Stores:

- freshness score
- sensor score
- vision score
- system label
- confidence
- risk
- explanation
- components JSON
- timestamp

### `inspection_control`

Single-chamber active capture target. Browsing history must not silently change this target.

### `human_verifications`

Append-only human review/audit records.

Stores:

- action (`accept`, `incorrect`, `ground_truth`)
- FreshFusion ground truth when supplied
- reviewer/notes
- assessment snapshot
- timestamp

## Current relationship model

```text
FruitSample
  |-- SensorReading[]
  |-- FruitImage[]
  |-- FusionResult[]
  `-- HumanVerification[]  (linked by sample_id)

InspectionControl
  `-- active FruitSample
```

## Data integrity rules

1. Public dataset labels and FreshFusion human ground truth are different concepts.
2. System predictions must never overwrite human verification.
3. Human verification must not rewrite historical model/fusion output.
4. Simulator readings may be stored, but cannot unlock a physical verdict.
5. History browsing is read-only with respect to the active capture target.
6. Explicitly labelled/review-referenced evidence should not be deleted by ordinary preview retention.
7. Final UI results should come from current gate semantics, not legacy placeholder scores.

## Migration status

There is currently no formal Alembic migration history. Additive tables are created by SQLAlchemy metadata startup. This works for the current prototype but is not sufficient as the schema becomes more complex.

Before major schema expansion:

1. back up `freshfusion.db`;
2. introduce Alembic;
3. create a baseline migration for the current schema;
4. test migrations against a copy of the existing database;
5. never replace or silently reset live demo data.

## Planned persistence layers

These are **planned**, not currently implemented database tables.

### `device_sessions`

Purpose: bind a phone/ESP32/chamber identity to an inspection and make multi-device expansion explicit.

Possible fields:

- session ID
- sample ID
- device ID/type
- started/ended timestamps
- provenance/auth/pairing metadata

### `evidence_events`

Purpose: persistent event timeline independent of reconstructing everything from raw tables.

Possible events:

- inspection created
- fruit detected
- image accepted/rejected
- sensor packet accepted/rejected
- reference match updated
- physical validation updated
- critic state changed
- fusion computed
- human verification added

### `investigation_runs`

Purpose: preserve analyst/critic/decision snapshots for reproducibility rather than only recomputing current state.

### `validation_runs`

Purpose: record immutable evaluation runs, split manifests, metrics and artifact references.

### `model_versions`

Purpose: track which CV/ML/reference/fusion configuration produced a result.

## Why these planned tables matter

Without explicit version/session/run provenance, a later algorithm update can change how old evidence is interpreted. For SIH this may be acceptable temporarily, but a production or research-grade system must be able to answer:

- Which model/rules generated this assessment?
- Which exact images and readings were used?
- Was the device physical or simulator?
- Was the evidence current at decision time?
- Who supplied the ground truth?
- Which validation split produced a claimed metric?

## Backup/export requirement

Before the final demo, add a simple documented backup/export procedure for:

- database file;
- labelled images;
- public reference index metadata;
- validation manifests/reports;
- model artifacts if any are actually deployed.

The demo should be recoverable without losing collected evidence.