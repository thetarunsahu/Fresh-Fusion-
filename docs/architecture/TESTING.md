# Testing and Verification Strategy

## Goal

FreshFusion should fail safely and explain why. Testing covers not only successful assessments but also stale evidence, simulator data, wrong sample pairing, camera view switching, validation integrity, migration/backup safety, optional Ollama failure and human verification.

## Preflight

Before a serious test or demo run:

```powershell
.\preflight_freshfusion.ps1
```

The preflight checker reports local availability for Git, Node/npm, backend environment/imports, Alembic, frontend packages, database, reference index, Ollama, `gemma3:4b` and the Ollama API.

A `[CHECK]` result is not always fatal: reference data and Gemma are optional for the deterministic verdict.

## Automated checks

### Backend

```powershell
.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -v
```

Coverage includes:

- sample/evidence handling
- sensor input validation
- simulator exclusion
- stale/empty evidence
- contradictions and safe locked states
- human review snapshots
- bounded fusion history
- camera/WebSocket paths
- validation metric computation from human-ground-truth snapshots
- exclusion of locked decisions from validation
- Evidence Agreement role semantics
- ValidationRun persistence

### Frontend production build

```powershell
cd frontend
npm install
npm run build
```

### Browser workflow tests

```powershell
cd frontend
npx playwright install chromium
npm test
```

On Windows, an installed Edge channel can also be used where configured.

## Database migration / backup test

Before the final event, perform this against a **copy** of the real prototype data first:

```powershell
.\backup_freshfusion.ps1 -IncludeUploads
.\start_freshfusion.ps1 -LocalOnly
```

The launcher applies Alembic migrations before FastAPI startup.

Verify that:

- existing fruit samples remain available;
- existing images/sensor/fusion/human reviews remain available;
- `investigation_runs`, `validation_runs` and `model_versions` exist;
- saving an investigation snapshot works;
- saving a validation snapshot works;
- restarting the application does not duplicate/delete historical evidence.

Never delete/reset the real database to make a migration test pass.

## Required physical test matrix

Automated fixtures are not substitutes for real fruit/hardware tests.

| Test | Expected behavior |
| --- | --- |
| Real Apple + fresh ESP32 + multiple views | Investigation progresses; verdict only if gates pass |
| Real Banana + fresh ESP32 + multiple views | Same as above with Banana identity flow |
| No fruit | Waiting/no-fruit state, no final freshness verdict |
| One viewpoint only | More evidence required |
| Same frame relabelled as multiple views | Should not satisfy convincing physical diversity |
| Fruit photo on laptop/phone screen | Physical verification should warn/block when evidence supports suspicion |
| ESP32 disconnected | WAITING FOR ESP32 / locked verdict |
| Stale ESP32 data | Must not unlock current physical verdict |
| Simulator telemetry | Visible as test data but excluded from physical verdict |
| MQ135 missing/invalid packet | Packet rejected or sensor state incomplete |
| Camera disconnected | Explicit disconnected/waiting state |
| Fruit identity conflict | Critic contradiction / blocked or warning state |
| Reference index missing | Warning; no fabricated reference result |
| Ollama offline | Core investigation still works; explanation unavailable |
| Ollama online | Structured evidence explanation only; snapshot saved |
| Human ground truth | Append review without rewriting historical system result |
| Validation page | Uses only comparable conclusive review snapshots; no invented values |
| Phone tunnel failure | Dashboard/backend stay available in recovery mode |

Use `docs/REAL_WORLD_VALIDATION_PROTOCOL.md` for the exact physical procedure.

## MQ135 testing

Follow `docs/MQ135_EXPERIMENT_PROTOCOL.md`.

The objective is to evaluate repeatable relative electrical behaviour against an empty-chamber baseline. Do not convert raw ADC response into ppm/ethylene concentration without a real calibration methodology.

## Validation testing

Software can now calculate observational metrics from real human-labelled review snapshots, but that is separate from scientific model/fusion validation.

A stronger evaluation should:

- use reviewed physical-sample ground truth;
- count one physical fruit as one sample;
- split by fruit/batch rather than individual frame;
- freeze the test split;
- record model/rule version;
- report sample counts;
- calculate confusion matrix, precision, recall and F1;
- report per-class behaviour;
- preserve incorrect cases for error analysis.

Do not use a frame-randomized split as evidence of independent generalization when multiple views of the same fruit can leak across sets.

## Gemma end-to-end verification

After starting FreshFusion and selecting an inspection:

1. open Investigation;
2. confirm `LOCAL MODEL READY`;
3. click **Explain with Gemma**;
4. confirm summary/supporting/contradiction/missing/next-step fields render;
5. confirm a saved snapshot ID is shown;
6. stop Ollama and confirm deterministic investigation still works while explanation becomes unavailable.

Gemma output must never change `decision.verdict_ready`, freshness score, or deterministic critic state.

## Demo release gate

```text
[ ] Preflight reviewed
[ ] Database/evidence backup created
[ ] Alembic migration tested against real-data copy
[ ] Backend automated tests pass
[ ] Frontend build passes
[ ] Browser workflow tests pass
[ ] Ollama offline fallback verified
[ ] Gemma explanation click verified on demo laptop
[ ] Phone Front -> Left/Right -> Back/Top capture physically verified
[ ] Phone background/re-pairing physically verified
[ ] ESP32 hardware packet + reconnect verified
[ ] Active-inspection pairing verified
[ ] Screen/photo negative case tested
[ ] No-fruit negative case tested
[ ] Stale sensor negative case tested
[ ] Human ground-truth save/reload verified
[ ] Investigation snapshot save/reload verified
[ ] Validation snapshot save/reload verified
[ ] MQ135 baseline experiment started/documented
[ ] Real fruit observations collected
[ ] Reference index available or missing-state demo prepared
[ ] Full demo recovery sequence rehearsed
[ ] Final presentation claims match actual validation state
```

## Logging and recovery

Runtime logs are kept under `.runtime/`. The operator should be able to distinguish failures in:

- frontend
- backend
- phone tunnel
- ESP32 networking
- camera permission
- Ollama
- reference data
- database/migration

Use `docs/DEMO_RUNBOOK.md` for the exact degraded-mode response.

## Current verification boundary

The branch contains software mechanisms and regression coverage, but these still require the actual target prototype:

- phone permission/background behaviour
- Wi-Fi/tunnel conditions
- ESP32 electronics/firmware reconnect behaviour
- MQ135 baseline/calibration experiments
- real-fruit multi-view false accept/reject behaviour
- enough physical ground truth for meaningful metrics
- independent held-out evaluation
- final performance/latency measurement
- PostgreSQL deployment behaviour if production migration is attempted
