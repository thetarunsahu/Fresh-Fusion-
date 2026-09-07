# Frontend Architecture

## Purpose

The frontend presents FreshFusion as an investigation workspace, not a single dashboard. It must show what evidence exists, what the system believes, what is missing, why a verdict is locked or released, and what a human reviewer can do next.

## Technology

- React 19
- Vite
- Recharts
- Lucide React
- QR code support
- Playwright regression tests

## Application structure

```text
frontend/src/
|-- App.jsx
|-- api.js
|-- main.jsx
|-- phone.jsx
|-- layout/
|   `-- WorkspaceLayout.jsx
|-- hooks/
|   `-- useInspection.js
|-- shared/
|   |-- Panel.jsx
|   `-- format.js
|-- features/
|   |-- overview/
|   |-- inspection/
|   |-- investigation/
|   |-- evidence/
|   |-- validation/
|   `-- history/
`-- components/
    `-- CameraStream.jsx
```

## Main pages

### Overview

Explains the complete system and the truthful current capabilities. It should still be useful when the backend is offline.

### Live Inspection

The real-time operational page. It shows active inspection state, camera pairing/capture, sensor evidence, reference state and final gate status.

### Investigation

The main reasoning workspace. It presents:

- Vision Analyst
- Sensor Analyst
- Reference Analyst
- Multi-view Analyst
- Evidence Critic
- final decision state
- human verification
- optional Gemma explanation

### Evidence

Chronological evidence timeline built from persisted timestamps and provenance. This page should support filtering and later inspection export.

### Dataset & Validation

Shows public dataset metadata, FreshFusion-collected labels, reference/model state and only real validation metrics. If no evaluation exists, the UI must display `NOT YET VALIDATED`.

### History

Lets users inspect previous samples without silently changing the active chamber capture target.

## Data flow

```text
FastAPI REST + WebSocket
          |
          v
       api.js
          |
          v
  useInspection hook
          |
          +--> active inspection state
          +--> selected history sample
          +--> stale-response protection
          +--> socket lifecycle
          |
          v
      Feature pages
```

API calls should remain centralized. Feature components should not duplicate fetch logic or invent response shapes.

## Desktop vs phone entry

`main.jsx` renders the desktop investigation workspace.

`phone.jsx` is a dedicated capture experience. The phone pairs to an explicit inspection ID and uploads labelled viewpoints. If the active target changes, capture should stop and request explicit re-pairing rather than silently writing to another sample.

## Camera responsibilities

`CameraStream.jsx` is a protected integration component because it controls view labels, timers, pause/resume and camera capture. Changes must be regression-tested for view switching and background/resume behavior.

## State rules

1. Browsing history must never activate that sample for hardware capture.
2. Late API responses must not overwrite a newer selected sample.
3. Old WebSockets must be disposed when selection changes.
4. Simulator evidence must be visually distinguishable from physical hardware evidence.
5. Locked verdicts must show the reason, not a placeholder score.
6. Missing backend/Ollama/reference services must produce explicit degraded states, not fake values.

## Safe parallel development areas

Soham can own the evidence/history investigation experience as isolated feature work. Nayan can own dataset/validation workflows. They may add feature-specific service helpers, but core camera, fusion, sensor ingestion and investigation contracts must not be changed independently.

## Frontend gaps / next work

- Final design-system cleanup after functionality stabilizes.
- Evidence filtering, previews and export.
- History search/pagination/review badges.
- Validation workflow with sample-based split manifests and real evaluation reports.
- Investigation report generation.
- Better responsive/mobile dashboard behavior.
- Accessibility and keyboard/state polish.
- Final UI consistency pass across old and new components.