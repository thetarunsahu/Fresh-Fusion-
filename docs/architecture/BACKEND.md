# Backend Architecture

## Purpose

The backend is the orchestration and evidence layer of FreshFusion. It receives camera and sensor evidence, stores it against an inspection, runs deterministic analysis modules, exposes investigation state to the frontend, publishes realtime updates, and keeps optional Ollama/Gemma explanation separate from the core verdict path.

## Technology

- FastAPI
- SQLAlchemy
- Pydantic
- OpenCV / NumPy
- SQLite by default
- WebSockets for realtime updates
- HTTPX for optional Ollama communication

## High-level flow

```text
Phone / ESP32
     |
     v
FastAPI ingestion
     |
     +--> validation / provenance
     +--> database persistence
     +--> OpenCV / sensor assessment
     +--> reference comparison
     +--> physical multi-view validation
     +--> fusion
     +--> investigation_core
              |
              +--> analysts
              +--> critic
              +--> confidence / decision contract
     |
     +--> WebSocket update
     +--> optional Ollama/Gemma explanation
```

## Main backend areas

```text
backend/app/
|-- main.py
|-- config.py
|-- database.py
|-- models.py
|-- schemas.py
|-- realtime.py
|-- api/
|   |-- samples.py
|   |-- sensors.py
|   |-- images.py
|   |-- investigation.py
|   |-- datasets.py
|   `-- external.py
`-- services/
    |-- image_analysis.py
    |-- sensor_assessment.py
    |-- reference_match.py
    |-- physical_validation.py
    |-- fusion.py
    |-- inspection_control.py
    |-- ollama_client.py
    `-- investigation_core/
        |-- evidence.py
        |-- analysts.py
        |-- critic.py
        |-- confidence.py
        `-- investigation.py
```

## API responsibilities

| Endpoint family | Responsibility |
| --- | --- |
| `/api/v1/samples` | Create, list, activate and inspect fruit samples |
| `/api/v1/sensors/readings` | Validate and ingest ESP32/simulator telemetry |
| `/api/v1/images/*` | Receive camera evidence and run image processing |
| `/api/v1/samples/{id}/investigation` | Return the evidence-grounded investigation contract |
| `/api/v1/samples/{id}/verification` | Append human acceptance, correction or ground truth |
| `/api/v1/datasets/*` | Expose reference/dataset/model/validation state |
| `/api/v1/ai/ollama/*` | Optional local LLM health and explanation |
| `/ws/live/{sample_id}` | Push inspection updates to the dashboard |

## Core analysis boundaries

### Image analysis

`image_analysis.py` extracts fruit presence, identity-supporting features, color/texture/defect evidence and presentation artifacts. Changes here can alter downstream physical validation and fusion, so regression tests are required.

### Sensor assessment

`sensor_assessment.py` handles temperature, humidity, sensor provenance, staleness and the experimental relative MQ135 signal. `mq135_raw` must not be presented as calibrated ppm unless a separate calibration process is implemented and validated.

### Reference analysis

`reference_match.py` compares handcrafted features against the local public reference index. Similarity is supporting evidence, not probability or accuracy.

### Physical validation

`physical_validation.py` checks changed viewpoints, screen/flat-reference suspicion, identity consistency and recent physical telemetry. It is a probabilistic monocular gate, not a guaranteed liveness/depth system.

### Fusion

`fusion.py` combines eligible sensor and visual evidence using prototype rules. Final outputs must remain locked when evidence gates fail.

### Investigation core

`investigation_core/` adapts the existing evidence into a stable product contract:

```text
Evidence
  -> Vision Analyst
  -> Sensor Analyst
  -> Reference Analyst
  -> Multi-view Analyst
  -> Critic
  -> Decision / Confidence
```

These analysts are software modules, not independent LLM agents.

## Optional Ollama/Gemma layer

`ollama_client.py` connects to local Ollama. Gemma is used for structured evidence explanation and summary only. The system must continue to inspect fruit when Ollama is offline.

Required LLM behavior:

- use only supplied evidence;
- never fabricate readings or metrics;
- never replace deterministic freshness scoring;
- return a stable structured response;
- fail gracefully.

## Realtime design

Each inspection can have a WebSocket subscriber channel. Image/sensor changes trigger updates. Frontend code must discard stale responses and dispose old sockets when the selected sample changes.

## Protected backend files

Coordinate changes to these files with the core owner:

- `services/image_analysis.py`
- `services/sensor_assessment.py`
- `services/physical_validation.py`
- `services/fusion.py`
- `api/images.py`
- `api/sensors.py`
- `services/inspection_control.py`

## Backend gaps / next work

1. Formal Alembic migration system.
2. Explicit multi-device/chamber session model.
3. Persistent investigation/evidence event snapshots where required.
4. Model/version provenance per generated assessment.
5. Better structured logging and demo diagnostics.
6. Authentication/pairing before any public deployment.
7. Performance isolation for CPU-heavy OpenCV work.
8. Calibration and held-out validation before scientific claims.