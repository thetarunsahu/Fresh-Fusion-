# FreshFusion Architecture Documentation

This directory is the engineering map for FreshFusion. The root `README.md` is the project entry point; these files explain how each subsystem is expected to work, what is already implemented, what remains experimental, and which areas are safe for parallel development.

## Documentation map

| Document | Purpose |
| --- | --- |
| [BACKEND.md](BACKEND.md) | FastAPI services, APIs, realtime flow and protected backend boundaries |
| [FRONTEND.md](FRONTEND.md) | React/Vite application structure, state flow, phone capture and feature ownership |
| [UI.md](UI.md) | UI/UX system, page responsibilities, status semantics and final polish rules |
| [DATABASE.md](DATABASE.md) | Current SQLAlchemy schema, persistence rules, migration gap and planned persistence layers |
| [AI.md](AI.md) | Vision, sensor, reference, multi-view, critic, fusion and Ollama/Gemma architecture |
| [HARDWARE.md](HARDWARE.md) | ESP32, DHT11, MQ135, phone camera, pairing and evidence timing |
| [TESTING.md](TESTING.md) | Regression strategy, commands, physical test matrix and release gates |
| [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md) | Ownership, branches, review rules and internal-round responsibilities |
| [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md) | End-to-end engineering checklist so critical subsystems are not forgotten |

## System principle

FreshFusion is not designed as `image -> AI -> answer`. It is an evidence-grounded fruit quality investigation system:

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

## Current prototype boundaries

- Automatic fruit identity is currently focused on Apple and Banana.
- MQ135 raw ADC is relative prototype evidence, not calibrated gas concentration.
- Physical-fruit verification is probabilistic monocular evidence, not a depth/liveness guarantee.
- Public reference similarity is not a learned probability or model accuracy.
- Freshness fusion weights and thresholds are experimental until calibrated and independently validated.
- SQLite is the default local database. PostgreSQL is configurable but is not yet the default verified development path.
- Formal schema migrations remain future work; current additive tables are created with SQLAlchemy metadata startup.

For current implementation details, also read `../INVESTIGATION_FOUNDATION.md` and `../IMPLEMENTATION_REPORT.md`.