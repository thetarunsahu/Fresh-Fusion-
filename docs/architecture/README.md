# FreshFusion Architecture Documentation

This directory is the engineering map for FreshFusion. The root `README.md` is the project entry point; these files explain how each subsystem works, what is implemented, what remains experimental, and which claims still require physical validation.

## Documentation map

| Document | Purpose |
| --- | --- |
| [BACKEND.md](BACKEND.md) | FastAPI services, APIs, realtime flow and protected backend boundaries |
| [FRONTEND.md](FRONTEND.md) | React/Vite structure, state flow, phone capture and feature ownership |
| [UI.md](UI.md) | UI/UX system, page responsibilities, status semantics and polish rules |
| [DATABASE.md](DATABASE.md) | SQLAlchemy schema, Alembic migrations, investigation/validation persistence and backup |
| [API.md](API.md) | Current REST/WebSocket contracts and evidence/validation semantics |
| [AI.md](AI.md) | Vision, sensor, reference, multi-view, critic, fusion and Ollama/Gemma architecture |
| [HARDWARE.md](HARDWARE.md) | ESP32, DHT11, MQ135, phone camera, pairing and evidence timing |
| [TESTING.md](TESTING.md) | Regression strategy, commands, physical test matrix and release gates |
| [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md) | Ownership, branches, review rules and collaboration boundaries |
| [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md) | End-to-end engineering checklist so critical subsystems are not forgotten |

Additional operational documents:

| Document | Purpose |
| --- | --- |
| [../REAL_WORLD_VALIDATION_PROTOCOL.md](../REAL_WORLD_VALIDATION_PROTOCOL.md) | Physical phone, ESP32, fruit, negative-test and ground-truth procedure |
| [../MQ135_EXPERIMENT_PROTOCOL.md](../MQ135_EXPERIMENT_PROTOCOL.md) | Relative-response baseline experiment without unsupported ppm claims |
| [../DEMO_RUNBOOK.md](../DEMO_RUNBOOK.md) | SIH demo sequence and degraded-mode recovery |
| [../INVESTIGATION_FOUNDATION.md](../INVESTIGATION_FOUNDATION.md) | Detailed investigation contracts, evidence rules and verification boundaries |
| [../IMPLEMENTATION_REPORT.md](../IMPLEMENTATION_REPORT.md) | Earlier tested foundation implementation report |

## System principle

FreshFusion is not designed as `image -> AI -> answer`. It is an evidence-grounded fruit-quality investigation system:

```text
Physical Fruit
    |
    +-- Phone Camera ----+
    |                    |
    +-- ESP32 Sensors ---+--> Evidence Store
                              |
                              +--> Vision Analyst
                              +--> Sensor Analyst
                              +--> Reference Analyst
                              +--> Multi-view Analyst
                                      |
                                      v
                              Evidence Agreement
                                      |
                                      v
                              Freshness Hypothesis
                                      |
                                      v
                               Evidence Critic
                                      |
                                      v
                         Deterministic Fusion/Confidence
                                      |
                         +------------+-------------+
                         |                          |
                   Final Assessment          More Evidence
                         |
                         v
                 Ollama/Gemma Explanation
                         |
                         v
                  Human Verification
                         |
                         v
                  Validation / History
```

Ollama/Gemma is optional and explanation-oriented. It is not required for a verdict and must never invent sensor readings, calibrated ppm, validation accuracy or food-safety claims.

## Current persistence flow

FreshFusion now preserves more than raw evidence:

```text
FruitSample
  +-- SensorReadings
  +-- FruitImages
  +-- FusionResults
  +-- HumanVerifications
  +-- InvestigationRuns

ValidationRuns
ModelVersions
```

Alembic provides the formal additive migration path, while SQLAlchemy metadata remains a compatibility bootstrap for fresh prototype databases.

## Current prototype boundaries

- Automatic fruit identity is currently focused on Apple and Banana.
- MQ135 raw ADC is relative prototype evidence, not calibrated gas concentration.
- Physical-fruit verification is probabilistic monocular evidence, not a depth/liveness guarantee.
- Public reference similarity is not a learned probability or model accuracy.
- Freshness fusion weights and thresholds are experimental until calibrated and independently validated.
- SQLite is the default local database. PostgreSQL is configurable but is not yet the primary physically verified prototype path.
- Real observational ground-truth metrics can now be calculated, but they remain **PRELIMINARY** until a proper independent sample-level held-out evaluation is performed.
- Real phone reconnect, ESP32 reconnect, fruit-stage testing and MQ135 baseline experiments still require physical execution on the prototype.

## Local finalization tools

From the repository root:

```powershell
.\preflight_freshfusion.ps1
.\backup_freshfusion.ps1 -IncludeUploads
.\start_freshfusion.ps1
```

If the HTTPS phone tunnel is unavailable:

```powershell
.\start_freshfusion.ps1 -LocalOnly
```

The local-only mode keeps the dashboard/backend running; it does not pretend that phone-camera capture remains available.
