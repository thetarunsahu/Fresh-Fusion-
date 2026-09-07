# Testing and Verification Strategy

## Goal

FreshFusion should fail safely and explain why. Testing therefore covers not only successful predictions but also stale evidence, simulator data, wrong sample pairing, camera view switching, missing services and human verification.

## Automated checks currently available

### Backend

```powershell
.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -v
```

The current investigation foundation includes regression coverage for sample/evidence handling, sensor validation, simulator separation, stale/empty evidence, contradictions, human review and fusion-history behavior.

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

## Required physical test matrix

Automated fixtures are not substitutes for real fruit/hardware tests.

| Test | Expected behavior |
| --- | --- |
| Real Apple + fresh ESP32 + multiple views | Investigation progresses; verdict only if gates pass |
| Real Banana + fresh ESP32 + multiple views | Same as above with Banana identity flow |
| No fruit | Waiting / no-fruit state, no final freshness verdict |
| One viewpoint only | More evidence required |
| Same frame relabelled as multiple views | Should not count as convincing physical diversity |
| Fruit photo on laptop/phone screen | Physical verification should warn/block when evidence supports suspicion |
| ESP32 disconnected | WAITING FOR ESP32 / locked verdict |
| Stale ESP32 data | Must not unlock current physical verdict |
| Simulator telemetry | Visible as test data but excluded from physical verdict |
| MQ135 missing/invalid packet | Packet rejected or sensor state incomplete |
| Camera disconnected | Explicit disconnected/waiting state |
| Fruit identity conflict | Critic contradiction / blocked or warning state |
| Reference index missing | Warning; no fabricated reference result |
| Ollama offline | Core investigation still works; explanation unavailable |
| Ollama online | Structured evidence explanation only |
| Human ground truth | Append review without rewriting historical system result |

## Validation testing

Model/fusion validation is a separate activity from software regression tests.

A valid evaluation should:

- use reviewed physical-sample ground truth;
- split by fruit/batch rather than individual frame;
- freeze the test split;
- record model/rule version;
- report sample counts;
- calculate confusion matrix, precision, recall and F1 where statistically meaningful;
- report Apple/Banana and class-level behavior;
- preserve incorrect cases for error analysis.

Do not use a frame-randomized split as evidence of independent generalization when multiple views of the same fruit can leak across sets.

## Demo release gate

Before the internal/SIH demo, all of the following should be checked:

```text
[ ] Fresh clone/setup succeeds
[ ] Backend automated tests pass
[ ] Frontend build passes
[ ] Browser workflow tests pass
[ ] Ollama offline fallback verified
[ ] Ollama/Gemma connection verified on demo laptop
[ ] Phone Front -> Left/Right -> Back/Top capture verified
[ ] ESP32 hardware packet verified
[ ] Active-inspection pairing verified
[ ] Screen/photo negative case tested
[ ] No-fruit negative case tested
[ ] Stale sensor negative case tested
[ ] Human ground-truth save/reload verified
[ ] Database backup created
[ ] Reference index available or missing-state demo prepared
[ ] Demo dataset/history cleaned of misleading fake metrics
[ ] Final presentation claims match actual validation state
```

## Logging during demo

The demo operator should know where frontend/backend/tunnel logs are written by the launcher. If a service fails, the team should be able to identify whether the failure is:

- frontend;
- backend;
- phone tunnel;
- ESP32 networking;
- camera permission;
- Ollama;
- reference data;
- database.

A recoverable degraded state is preferable to an unexplained blank screen.

## Current known verification boundary

Software regressions can be automated, but these must still be physically validated on the target setup:

- actual phone permission/background behavior;
- Wi-Fi/tunnel conditions;
- ESP32 electronics and firmware;
- sensor calibration;
- real-fruit multi-view false accept/reject behavior;
- model accuracy;
- PostgreSQL deployment behavior;
- performance under continuous live capture.