# FreshFusion API Reference

Base prefix: `/api/v1`

This document describes the current prototype API contracts. It is not a public-production API specification. Authentication, rate limiting and multi-device authorization remain future deployment work.

## Health

### `GET /health`

Returns backend status, runtime ports, phone-camera mode, ESP32 endpoint and currently supported automatic fruit identities.

### `GET /ai/ollama/health`

Checks the optional local Ollama service and configured Gemma model.

The LLM is not required for a deterministic verdict.

---

## Samples / inspections

### `POST /samples`

Creates a new inspection and makes it the active single-chamber capture target.

Example body:

```json
{"fruit_type":"Apple"}
```

Supported prototype choices include `Auto`, `Apple` and `Banana`.

### `GET /samples?limit=200`

Lists recent inspections with evidence counts and latest recorded gate state.

### `GET /samples/active`

Returns the current chamber capture target.

### `PUT /samples/{sample_id}/active`

Explicitly changes the chamber capture target.

History browsing alone never changes this value.

### `GET /samples/{sample_id}/bundle`

Returns the sample, stored sensor series, images and current read-only fusion evaluation.

### `POST /samples/{sample_id}/fusion`

Recomputes and persists a FusionResult using the current deterministic evidence path.

### `POST /samples/{sample_id}/verification`

Stores an append-only human review.

Example ground-truth body:

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

FreshFusion human labels:

- `fresh`
- `ripe`
- `overripe`
- `spoiled`

An `accept` action is rejected while the deterministic verdict is locked.

---

## Sensor ingestion

### `POST /sensors/readings`

Accepts current ESP32/simulator telemetry.

Prototype-required fields:

```json
{
  "sample_id":"APP-ABC123",
  "device_id":"ESP32_01",
  "source":"hardware",
  "temperature":24.0,
  "humidity":60.0,
  "mq135_raw":500
}
```

`source` is provenance metadata, not cryptographic device authentication.

`mq135_raw` is a 12-bit raw/relative electrical signal. It must not be described as calibrated ppm unless a separate calibration methodology has actually been completed.

When `sample_id` is omitted, the current single-chamber active inspection may be used by the firmware flow.

Simulator/test readings can be stored/displayed but cannot unlock a physical verdict.

---

## Image evidence

### `POST /images/upload`

Multipart upload for labelled/manual image evidence.

Important fields:

- `sample_id`
- `angle`
- optional `ground_truth`
- `file`

### `POST /images/stream-frame`

Multipart phone-camera frame upload.

Important fields:

- `sample_id`
- `view`
- optional `ground_truth`
- `file`

A stale/mismatched phone session can be rejected when its paired inspection is no longer the active target.

---

## Investigation

### `GET /samples/{sample_id}/investigation`

Read-only current investigation. Time-dependent gates are re-evaluated instead of trusting a historical stored verdict.

Important response sections:

```text
inspection_id
sample
status
evidence
analysts
agreement
critic
decision
timeline
human_verifications
```

`analysts` contains:

- Vision Analyst
- Sensor Analyst
- Reference Analyst
- Multi-view Analyst

`agreement` compares only compatible evidence roles. Vision and Sensor may contribute freshness-bearing score bands; Reference remains contextual and Multi-view remains a physical gate.

`critic` exposes:

- supporting evidence
- missing evidence
- contradictions
- warnings

Final label/score/confidence are `null` while the verdict is locked.

### `POST /samples/{sample_id}/investigation/snapshot?trigger=manual-ui`

Persists the current deterministic investigation state into `investigation_runs`.

### `GET /samples/{sample_id}/investigation/snapshots?limit=20`

Returns saved investigation audit snapshots.

### `POST /samples/{sample_id}/investigation/explain`

Runs optional local Gemma against already-computed evidence.

Gemma receives:

- sample metadata
- analyst summaries
- Evidence Agreement
- critic output
- deterministic decision

It is explicitly instructed not to invent sensor values, calibration, accuracy or food-safety claims.

A successful call also saves an InvestigationRun containing the deterministic snapshot plus the LLM explanation.

The response includes `required_for_verdict: false`.

---

## Dataset / reference state

### `GET /datasets/registry?fruit_type=Apple`

Returns public dataset/source metadata used for reference/training research.

### `GET /datasets/reference-status`

Returns local compact reference-index state.

Reference similarity is a handcrafted-feature comparison, not model probability or measured accuracy.

---

## Validation

### `GET /datasets/validation`

Returns:

- public dataset metadata
- reference index state
- labelled image/review counts
- model artifact presence state
- legacy-compatible metric fields
- current observational `evaluation`
- latest saved validation run

The `evaluation` object contains real metrics only when comparable ground-truth review snapshots exist:

```text
status
sample_count
represented_classes
accuracy
precision
recall
f1
confusion_matrix
per_class
records
excluded
protocol
```

Status is:

- `NOT YET VALIDATED` when no comparable records exist
- `PRELIMINARY` when observational metrics can be computed

The API deliberately does not upgrade small observational metrics into a claim of held-out scientific validation.

### `POST /datasets/validation-runs?name=manual-ui`

Freezes the current evaluation into `validation_runs`.

### `GET /datasets/validation-runs?limit=20`

Lists recent frozen validation snapshots.

---

## Realtime

### `WS /ws/live/{sample_id}`

Per-inspection WebSocket used by the frontend for current image/sensor/fusion routing notifications.

Clients must still protect against stale responses when inspection selection changes.

---

## Static evidence

### `/uploads/...`

Serves stored image/evidence artifacts used by the local dashboard.

Do not expose an unauthenticated prototype upload/static-evidence service directly to the public internet as a production deployment.

---

## Current safety boundaries

- No public-production authentication yet.
- No guaranteed multi-device authorization yet.
- No calibrated MQ135 gas concentration.
- No validated deep freshness model unless a model artifact and independent evaluation are explicitly demonstrated.
- Reference similarity is not probability.
- Monocular physical verification is probabilistic.
- Ollama/Gemma is explanation-only.
- Fusion/confidence remains experimental until calibrated against adequate physical ground truth.
