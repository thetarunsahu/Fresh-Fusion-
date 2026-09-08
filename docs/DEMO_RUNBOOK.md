# FreshFusion Demo Runbook

Use this document for the final internal/SIH rehearsal. The demo goal is not to show every feature; it is to prove that FreshFusion collects physical evidence, challenges it, releases or blocks a decision responsibly, and preserves traceability.

## 1. Before leaving for the venue

- Charge laptop, phone, ESP32 power source and backup power bank.
- Carry USB cables, hotspot option and spare fruit samples.
- Confirm `gemma3:4b` appears in `ollama list`.
- Run automated backend/browser tests.
- Back up `freshfusion.db` and important uploads.
- Keep the repository available locally; do not depend on GitHub during the demo.
- Keep one known-good tagged/committed version available.
- Keep screenshots/video of a successful physical run as evidence-only fallback, clearly labelled as a previous run rather than a live result.

## 2. Start sequence

From repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_freshfusion.ps1
```

Confirm the printed lines:

- Laptop dashboard
- Phone camera URL or local-only recovery state
- Backend health
- Ollama health
- ESP32 API

If internet/tunnel is unavailable, use:

```powershell
.\start_freshfusion.ps1 -LocalOnly
```

This keeps the dashboard/backend available. Do not claim the phone camera is live if the secure phone path is unavailable.

## 3. 90-second core demo

### Scene A — Real fruit / sufficient evidence

1. Create a new Apple or Banana inspection.
2. Show that the phone is paired to the current sample ID.
3. Capture changed physical views: Front, Left, Back (and more if time allows).
4. Show fresh ESP32 temperature, humidity and MQ135 raw telemetry.
5. Open Investigation.
6. Point to Vision, Sensor, Reference and Multi-view Analysts.
7. Point to Evidence Agreement and explain that only compatible evidence roles are compared; reference and multi-view are not treated as equivalent freshness votes.
8. Show the Evidence Critic.
9. If the gate releases, show the experimental assessment. If it remains locked, explain exactly which evidence is missing; a safe lock is a valid result.
10. Click **Explain with Gemma** and show the local evidence-grounded explanation.
11. Add human verification/ground truth.
12. Open History/Evidence to show persistence.

### Scene B — Adversarial evidence

Use a fruit image on a laptop/phone screen or repeated unchanged views.

Expected narrative:

> "FreshFusion does not accept every image as physical fruit evidence. The multi-view/critic layer can keep the final decision locked when the presentation looks suspicious or viewpoints are insufficient."

Do not promise guaranteed liveness detection; current monocular verification is probabilistic.

### Scene C — Missing sensor

Disconnect/stop ESP32 telemetry or use a sample with no recent hardware reading.

Expected state:

- Waiting for ESP32 / More Evidence Required
- no released freshness score

Narrative:

> "The system prefers missing-data uncertainty over inventing a complete multimodal result."

## 4. Gemma failure recovery

If Ollama/Gemma fails:

1. Do not restart the entire demo immediately.
2. Show that the deterministic investigation, critic and final gate still work.
3. Explain that Gemma is an optional explanation layer.
4. If needed, verify separately with `ollama list` and the printed Ollama health URL.

Never imply Gemma computed the final freshness score.

## 5. Phone tunnel failure recovery

The launcher now continues even if the Cloudflare phone tunnel cannot be created.

If the phone path fails:

- keep dashboard + backend running;
- use local-only mode if a restart is required;
- show already stored real inspection evidence/history;
- clearly distinguish stored physical evidence from a live capture;
- do not use simulator data to unlock the physical verdict.

## 6. ESP32 failure recovery

If telemetry stops:

- verify the ESP32 endpoint printed by the launcher;
- check Wi-Fi/hotspot and backend port;
- demonstrate the safe `WAITING FOR ESP32` state rather than injecting fake hardware data;
- simulator telemetry may be used only to demonstrate UI plumbing and must remain marked simulator.

## 7. Database safety

Before schema changes or the final event day, keep a timestamped backup of the database.

The launcher applies Alembic migrations before the backend starts. If migration fails, stop and inspect the error; do not delete or replace the live database to make the app start.

Investigation snapshots and validation runs are append-only audit records for the demo workflow.

## 8. Validation slide/demo

The Dataset & Validation page may show:

- `NOT YET VALIDATED` when no comparable conclusive ground-truth samples exist;
- `PRELIMINARY` metrics when real human-labelled inspection snapshots exist.

Do not describe preliminary observational metrics as held-out scientific accuracy.

For the internal round, a smaller real dataset with transparent limitations is stronger than a fabricated 95% accuracy claim.

## 9. Presenter handoff

Recommended short presentation:

**Sajiya**
- problem
- gap in single-source inspection
- FreshFusion solution
- innovation overview

**Tarun**
- hardware
- evidence architecture
- investigation analysts
- Evidence Agreement
- critic/fusion
- live demo
- Gemma role

**Soha / Prerna**
- validation methodology
- feasibility/impact
- future scope

For a very short slot, use Sajiya + Tarun only and keep the rest of the team ready for Q&A.

## 10. Final rehearsal checklist

A serious final rehearsal passes only when the team has physically demonstrated:

```text
real fruit
-> correct active inspection
-> changed physical camera views
-> fresh real ESP32 telemetry
-> analysts populated
-> evidence agreement visible
-> critic explains missing/conflicting evidence
-> deterministic gate responsibly releases OR blocks
-> Gemma explanation works OR fails without breaking core logic
-> human verification persists
-> history/evidence remains accessible
-> validation page remains truthful
-> tunnel/Ollama/ESP32 failure has a known recovery path
```

Record one complete rehearsal on video before the final presentation day.
