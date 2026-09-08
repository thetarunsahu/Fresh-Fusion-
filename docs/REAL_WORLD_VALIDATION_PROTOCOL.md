# FreshFusion Real-World Validation Protocol

This protocol is the bridge between a working software prototype and evidence that the physical system behaves as intended. Software tests, synthetic images and simulator telemetry do **not** count as real fruit validation.

## 1. Test unit

One **physical fruit** is one inspection/sample.

Five camera views of the same fruit are evidence for the same sample; they are not five independent validation samples.

Recommended initial scope:

- Apple: Fresh, Ripe, Overripe, Spoiled
- Banana: Fresh, Ripe, Overripe, Spoiled
- Minimum useful demo dataset: 20 physical inspections
- Better target: 40 physical inspections

Do not force equal labels if the available fruit does not genuinely represent those stages. Record the observation honestly.

## 2. Before every session

1. Start FreshFusion with `./start_freshfusion.ps1`.
2. Confirm backend health.
3. Confirm Ollama health if Gemma will be demonstrated; Gemma is optional for the verdict.
4. Confirm the phone QR opens the inspection-specific camera page.
5. Confirm the ESP32 is posting to the backend endpoint printed by the launcher.
6. Confirm the Dataset & Validation page is not showing invented metrics.
7. Photograph the physical fruit/sample before testing so the manual record can be audited later.

## 3. Capture procedure per fruit

Create a **new inspection** for each physical fruit.

Capture changed physical viewpoints rather than relabelling the same frame:

1. Front
2. Left
3. Right
4. Back
5. Top when practical

Move around the fruit or rotate the fruit while keeping lighting and chamber conditions as consistent as practical.

Wait for a fresh hardware sensor packet. Record:

- sample ID
- fruit type
- date/time
- human freshness stage
- temperature
- humidity
- MQ135 raw ADC
- number of accepted views
- Vision Analyst finding
- Sensor Analyst finding
- Reference Analyst finding
- Multi-view status
- Evidence Critic status
- final system state/label
- deterministic confidence if released
- human ground truth
- correct / incorrect / inconclusive
- notes

## 4. Ground-truth rule

Use FreshFusion's human verification action to record the independent observation:

- `fresh`
- `ripe`
- `overripe`
- `spoiled`

Ground truth must be an observation made by the team/operator, not copied from the system prediction. If the fruit stage is genuinely uncertain, document the uncertainty instead of changing the label to match the model.

## 5. Negative and failure tests

Run these separately from normal accuracy/quality observations:

| Test | Expected safe behaviour |
| --- | --- |
| Empty chamber | No final freshness verdict |
| Fruit photo on laptop screen | Physical verification blocked or suspicious |
| Fruit photo on phone screen | Physical verification blocked or suspicious |
| One camera view only | More evidence required |
| Same image relabelled as multiple views | Multi-view gate should remain blocked |
| ESP32 disconnected | Waiting for ESP32 / locked verdict |
| Stale ESP32 reading | Locked or warning state |
| Simulator telemetry | Visible for testing but cannot unlock physical verdict |
| Wrong fruit identity | Contradiction / confirmation required |
| Reference index unavailable | Warning; no fabricated match |
| Ollama stopped | Core verdict still works; explanation unavailable |
| Phone tunnel failure | Laptop/backend continue in recovery mode |

Record failures as useful evidence. Do not delete inconvenient results.

## 6. Phone and reconnect verification

Physically verify:

- QR opens the correct inspection.
- Front -> Left -> Back changes are stored with the currently selected view.
- Phone background/resume does not silently upload under the wrong view.
- Creating/activating another inspection stops stale phone uploads from entering the wrong sample.
- Camera permission denial produces a recoverable UI state.
- Tunnel loss does not destroy the laptop/backend session.

## 7. ESP32 verification

Physically verify:

- temperature, humidity and MQ135 raw arrive together;
- device ID is visible;
- hardware source is distinct from simulator source;
- missing/invalid packets are rejected;
- stale telemetry cannot unlock a verdict;
- reconnect resumes data without creating fake historical readings;
- data is attached to the intended active inspection.

## 8. Validation metrics

The Dataset & Validation page computes metrics only from human ground-truth records that contain a comparable, previously stored conclusive decision snapshot.

Metrics remain labelled **PRELIMINARY** because observational samples are not automatically a scientifically independent held-out test set.

For stronger validation later:

1. freeze a sample-level manifest;
2. keep physical fruits—not neighbouring frames—exclusive to one split;
3. preserve an untouched test set;
4. report confusion matrix, macro precision, macro recall, macro F1 and per-class support;
5. document lighting, chamber, fruit variety and collection conditions.

## 9. Evidence to retain for SIH

Keep:

- 3-5 clean photos of the physical chamber;
- one short video showing phone + fruit + live dashboard together;
- screenshots of a successful investigation;
- screenshot of Evidence Agreement;
- screenshot of an intentionally blocked screen/photo test;
- screenshot of Ollama/Gemma explanation;
- screenshot of real validation counts/metrics when available;
- raw sample IDs for every result used in the PPT.

Claims in the presentation must match what was actually physically tested.
