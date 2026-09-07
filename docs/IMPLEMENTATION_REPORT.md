# Investigation foundation implementation report

## Delivered

- Six-page investigation workspace; existing live dashboard extracted into its own feature.
- Current camera view/label callbacks, pause/resume and explicit phone re-pairing.
- Protected sample selection, stale-response guards and disposed-WebSocket cleanup.
- Required prototype sensor measurements, declared simulator separation and uncalibrated raw/4095 gas contribution.
- Modular deterministic evidence/analyst/critic/decision response using existing CV, references, physical checks and fusion.
- Additive active-inspection and append-only human-verification tables, separate from public labels.
- Recorded evidence timeline, real dataset/model state, history counts and honest unavailable metrics.
- Production dashboard + phone entries, pinned frontend dependencies, browser regressions and teammate handoff documentation.

## Verification

- 17 backend regression tests passed against temporary SQLite/uploads, including actual OpenCV upload, WebSocket notification, automatic fruit routing, sensor validation, simulator exclusion, stale/empty evidence, contradictions, human review and bounded fusion history.
- 37 Python source files parsed successfully; active FastAPI imports/startup exercised.
- Frontend npm install and production build passed; dist/index.html and dist/phone.html emitted.
- Five browser regressions passed in headless Edge, including virtual-camera view/label switching, background/resume, explicit re-pairing, history selection, late responses and human ground truth.
- A separate real Uvicorn + Vite browser smoke passed: create inspection, send test telemetry, upload a synthetic image through OpenCV, inspect analysts, save human ground truth, inspect timeline/validation/history. No JavaScript page errors.
- Desktop/mobile screenshots inspected; standalone overview remains usable without backend data.
- Existing database copied read-only into a temporary location, then successfully initialized with additive tables; existing sample/readings preserved.
- Original root and backend SQLite files retained their pre-task SHA-256 hashes.

Hardware, actual mobile permission behavior, Wi-Fi/tunnel operation, ESP32 firmware compilation/electronics, sensor calibration, real-fruit anti-spoof performance, model accuracy, PostgreSQL and optional Ollama inference were not physically/integration validated. Browser camera input and backend fixture analyses are explicitly test data, not measured model performance. Existing dependency deprecation notices are non-blocking.

## Preserved boundaries

The launcher, reference setup script, OpenCV analysis algorithm and reference matching implementation remain unchanged. Concurrently committed Ollama work was preserved; only its investigation route import now points to the modular deterministic foundation. No dataset, live database, generated model, credentials, browser artifacts or runtime logs are included in this commit. The previously untracked frontend lockfile was backed up locally before being reconciled with the package manifest.

## Created files

- `backend/app/services/inspection_control.py`
- `backend/app/services/investigation_core/__init__.py`
- `backend/app/services/investigation_core/analysts.py`
- `backend/app/services/investigation_core/confidence.py`
- `backend/app/services/investigation_core/critic.py`
- `backend/app/services/investigation_core/evidence.py`
- `backend/app/services/investigation_core/investigation.py`
- `backend/app/services/sensor_assessment.py`
- `backend/tests/test_investigation.py`
- `docs/IMPLEMENTATION_REPORT.md`
- `docs/INVESTIGATION_FOUNDATION.md`
- `frontend/package-lock.json`
- `frontend/playwright.config.js`
- `frontend/src/features/evidence/EvidenceTimeline.jsx`
- `frontend/src/features/history/History.jsx`
- `frontend/src/features/inspection/LiveInspection.jsx`
- `frontend/src/features/investigation/HumanVerification.jsx`
- `frontend/src/features/investigation/Investigation.jsx`
- `frontend/src/features/overview/Overview.jsx`
- `frontend/src/features/validation/Validation.jsx`
- `frontend/src/hooks/useInspection.js`
- `frontend/src/layout/WorkspaceLayout.jsx`
- `frontend/src/shared/Panel.jsx`
- `frontend/src/shared/format.js`
- `frontend/src/workspace.css`
- `frontend/tests/workflow.spec.js`

## Modified files

- `.gitignore`
- `README.md`
- `backend/app/api/datasets.py`
- `backend/app/api/images.py`
- `backend/app/api/investigation.py`
- `backend/app/api/samples.py`
- `backend/app/api/sensors.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/services/fusion.py`
- `backend/app/services/physical_validation.py`
- `docs/LOCAL_NETWORK.md`
- `esp32/freshfusion_node.ino`
- `frontend/.env.example`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/components/CameraStream.jsx`
- `frontend/src/phone.jsx`
- `frontend/vite.config.js`

## Next teammate tasks

See [team ownership and contracts](INVESTIGATION_FOUNDATION.md): evidence filters/export, dataset review and sample-based split manifests, history search/pagination. The core owner should perform the physical phone/ESP32 scan and calibration experiments. Do not train from the current image-randomized exporter or label heuristic scores as validated accuracy.
