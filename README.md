<div align="center">

# 🍎 FreshFusion

### Evidence-Grounded Multimodal Fruit Quality Investigation System

**Computer Vision • Environmental Sensing • Gas Response • Multi-View Verification • Evidence Critic • Local AI**

FreshFusion is an experimental fruit-quality investigation platform designed to **collect, analyze, challenge, verify, and explain evidence** before releasing a freshness assessment.

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![ESP32](https://img.shields.io/badge/ESP32-IoT-E7352C?style=for-the-badge&logo=espressif&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-000000?style=for-the-badge)
![Gemma](https://img.shields.io/badge/Gemma-Reasoning_Layer-4285F4?style=for-the-badge)

<br>

### Inspect. Challenge. Verify. Explain.

</div>

---

# Overview

Most fruit freshness systems are built around a simple pipeline:

```text
Image
  ↓
AI Model
  ↓
Fresh / Rotten
```

FreshFusion takes a different approach.

Instead of asking only:

> **“What class does this image belong to?”**

FreshFusion asks:

> **“What evidence do we have, does that evidence agree, is anything missing, and is the result strong enough to trust?”**

Every fruit is treated as an **inspection case**.

An inspection may contain:

- multiple camera viewpoints,
- temperature measurements,
- humidity measurements,
- MQ135 raw gas-response readings,
- visual surface characteristics,
- fruit identity evidence,
- public reference comparisons,
- physical multi-view verification,
- freshness hypothesis,
- evidence contradictions,
- confidence and fusion results,
- local AI explanation,
- and human ground truth.

FreshFusion is intentionally designed to support outcomes such as:

```text
MORE EVIDENCE REQUIRED

WAITING FOR ESP32

PHYSICAL FRUIT NOT VERIFIED

CONFLICTING EVIDENCE

INCONCLUSIVE
```

The system does not need to force a freshness answer when evidence is incomplete.

---

# Core Philosophy

FreshFusion is not designed as:

```text
Fruit
  ↓
Single AI Model
  ↓
Prediction
```

It is designed as:

```text
Physical Fruit
      ↓
Evidence Collection
      ↓
Independent Analysis
      ↓
Freshness Hypothesis
      ↓
Evidence Critic
      ↓
Confidence + Fusion
      ↓
Conclusive / Inconclusive
      ↓
Local AI Explanation
      ↓
Human Verification
```

The core principle is:

> **A trustworthy system should not only produce an answer. It should be able to show what supports that answer, what contradicts it, what is missing, and when it does not know enough.**

---

# High-Level System Architecture

```text
                            ┌────────────────────┐
                            │   PHYSICAL FRUIT   │
                            └─────────┬──────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 │                                         │
                 ▼                                         ▼
        ┌──────────────────┐                     ┌──────────────────┐
        │   PHONE CAMERA   │                     │      ESP32       │
        │                  │                     │                  │
        │ Front            │                     │ DHT11            │
        │ Left             │                     │ Temperature      │
        │ Right            │                     │ Humidity         │
        │ Back             │                     │ MQ135 Raw ADC    │
        │ Top              │                     │ Device Metadata  │
        └────────┬─────────┘                     └────────┬─────────┘
                 │                                        │
                 └──────────────────┬─────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   FASTAPI BACKEND    │
                         │                      │
                         │ Inspection Control   │
                         │ Evidence Storage     │
                         │ REST APIs            │
                         │ WebSocket Updates    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                  ┌────────────────────────────────┐
                  │     INVESTIGATION ENGINE       │
                  └────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼

 ┌─────────────────┐      ┌─────────────────┐      ┌───────────────────┐
 │ VISION ANALYST  │      │ SENSOR ANALYST  │      │ REFERENCE ANALYST │
 │                 │      │                 │      │                   │
 │ Fruit presence  │      │ Temperature     │      │ Public datasets   │
 │ Fruit identity  │      │ Humidity        │      │ Similar classes   │
 │ Color           │      │ MQ135 response  │      │ Feature similarity│
 │ Texture         │      │ Sensor freshness│      │ Reference evidence│
 │ Surface damage  │      │ Device source   │      │                   │
 └────────┬────────┘      └────────┬────────┘      └─────────┬─────────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ MULTI-VIEW ANALYST   │
                         │                      │
                         │ View diversity       │
                         │ Same-fruit checks    │
                         │ Screen suspicion     │
                         │ Physical evidence    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ FRESHNESS HYPOTHESIS │
                         │ ENGINE               │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   EVIDENCE CRITIC    │
                         │                      │
                         │ Missing evidence?    │
                         │ Conflicts?           │
                         │ Stale sensors?       │
                         │ Identity mismatch?   │
                         │ Screen / photo?      │
                         └──────────┬───────────┘
                                    │
                          ┌─────────┴─────────┐
                          │                   │
                          ▼                   ▼

                 ┌────────────────┐   ┌────────────────────┐
                 │ EVIDENCE READY │   │ MORE EVIDENCE      │
                 │                │   │ REQUIRED            │
                 └───────┬────────┘   └────────────────────┘
                         │
                         ▼
                ┌──────────────────────┐
                │ DETERMINISTIC        │
                │ CONFIDENCE + FUSION  │
                └──────────┬───────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ EXPERIMENTAL       │
                 │ FRESHNESS RESULT   │
                 └─────────┬──────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
     ┌─────────────────┐        ┌────────────────────┐
     │ OLLAMA + GEMMA  │        │ HUMAN VERIFICATION │
     │                 │        │                    │
     │ Explanation     │        │ Accept             │
     │ Contradictions  │        │ Mark Incorrect     │
     │ Next Step       │        │ Add Ground Truth   │
     └────────┬────────┘        └──────────┬─────────┘
              │                           │
              └──────────────┬────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ FRESHFUSION DATA │
                    │                  │
                    │ Images           │
                    │ Sensors          │
                    │ Predictions      │
                    │ Ground Truth     │
                    └────────┬─────────┘
                             │
                             ▼
                    VALIDATION + FUTURE ML
```

---

# Investigation Modules

FreshFusion uses a **hybrid multi-agent investigation architecture**.

Not every module is an LLM agent.

Some modules are deterministic, some use computer vision, some use reference evidence, and Gemma is reserved for human-readable reasoning and explanation.

| Module | Responsibility | Technology |
| --- | --- | --- |
| Intake / Triage | Inspection creation, fruit presence, capture routing | FastAPI + rules |
| Vision Analyst | Fruit identity, color, texture, defects | OpenCV |
| Sensor Analyst | Temperature, humidity, MQ135 raw response | Deterministic analysis |
| Reference Analyst | Compare evidence with public reference data | Feature similarity |
| Multi-View Analyst | Physical-view consistency and screen/photo checks | OpenCV |
| Freshness Hypothesis | Build provisional freshness interpretation | Evidence synthesis |
| Evidence Critic | Detect missing, weak or contradictory evidence | Rule-based critic |
| Confidence / Fusion | Decide whether assessment can be released | Deterministic engine |
| Explanation Agent | Generate grounded natural-language explanations | Ollama + Gemma |
| Human Verification | Accept, reject or label result | Database workflow |

---

# 1. Intake / Triage

The Intake / Triage layer manages the beginning of every FreshFusion inspection.

Responsibilities include:

- creating an inspection,
- assigning a sample ID,
- determining whether usable fruit evidence is present,
- associating camera frames with the active inspection,
- associating ESP32 telemetry with the active inspection,
- checking evidence freshness,
- and preventing stale evidence from silently becoming part of a new assessment.

The inspection itself acts as the central unit around which all evidence is organized.

---

# 2. Vision Analyst

The Vision Analyst evaluates visual evidence captured from the fruit.

Current and planned analysis includes:

```text
Fruit Presence
Fruit Identity
Color Distribution
Brown Surface Percentage
Dark Surface Percentage
Healthy Surface Estimate
Texture Characteristics
Edge Density
Surface Irregularity
Visible Defects
Reference Features
Optional ML Prediction
```

Current visual processing relies primarily on **OpenCV-based analysis**.

The system also contains experimental infrastructure for future transfer-learning models.

A future freshness classifier may use:

```text
MobileNetV3-Small
        ↓
Transfer Learning
        ↓
Fresh
Ripe
Overripe
Spoiled
```

FreshFusion does not claim trained-model accuracy unless a validated model artifact and evaluation actually exist.

---

# 3. Sensor Analyst

The Sensor Analyst evaluates environmental and gas-related evidence from the ESP32.

Current signals include:

```text
Temperature
Humidity
MQ135 Raw ADC Response
RSSI
Device Uptime
Timestamp
Device Identity
Evidence Source
```

The Sensor Analyst also checks whether:

- the packet is complete,
- the reading is recent,
- the source is hardware or simulator,
- values are within expected electrical/input ranges,
- and the evidence is eligible for fusion.

---

# MQ135 Scientific Boundary

FreshFusion stores and analyzes `mq135_raw`.

This value represents the electrical ADC response from the MQ135 sensor.

It is currently treated as:

> **Relative experimental gas-response evidence**

It is not automatically treated as:

```text
ppm
ethylene concentration
VOC concentration
spoilage concentration
food safety measurement
```

unless a proper calibration experiment has been performed.

Current gas contribution is therefore explicitly experimental.

---

# 4. Reference Analyst

FreshFusion can compare fruit characteristics with a locally indexed public dataset.

The Reference Analyst may provide:

```text
Reference Dataset
Closest Class
Similarity
Reference Count
Feature Distance
Source Information
```

Reference similarity is supporting evidence.

It is **not equivalent to**:

- model probability,
- validation accuracy,
- freshness confidence,
- or ground truth.

Public dataset labels are also kept separate from FreshFusion human ground-truth labels.

---

# 5. Multi-View Analyst

FreshFusion should not unlock a freshness result simply because one image appears to contain a fruit.

The system therefore collects multiple viewpoints such as:

```text
Front
Left
Right
Back
Top
```

The Multi-View Analyst examines signals including:

- number of distinct views,
- appearance diversity,
- fruit fingerprint differences,
- fruit identity consistency,
- planar homography consistency,
- screen/display suspicion,
- repeated flat-image suspicion,
- and physical-fruit likelihood.

Example:

```text
Front captured     ✓
Left captured      ✓
Back captured      ✓

Identity stable    ✓
Appearance changed ✓
Screen suspicion   Low

Physical fruit likely
```

This verification is probabilistic.

A monocular phone camera cannot provide the same guarantees as dedicated depth, stereo, NIR, or structured-light hardware.

---

# 6. Freshness Hypothesis Engine

The Freshness Hypothesis Engine combines findings from multiple analysts into a provisional interpretation.

Example:

```text
VISION
Surface browning increased
Healthy surface reduced
Texture degradation detected

SENSOR
Temperature acceptable
Humidity moderately high
MQ135 relative response elevated

REFERENCE
Closest visual class resembles overripe reference

MULTI-VIEW
Physical fruit likely

────────────────────────────────────

PROVISIONAL HYPOTHESIS

Likely Overripe
```

This is not yet the final result.

The hypothesis must first pass through the Evidence Critic.

---

# 7. Evidence Critic

The Evidence Critic is one of the core differentiators of FreshFusion.

Instead of trusting the first prediction, FreshFusion actively challenges its own evidence.

The critic checks questions such as:

```text
Is a fruit actually visible?

Are enough viewpoints available?

Do the views appear to belong to the same fruit?

Is ESP32 telemetry recent?

Is the sensor packet complete?

Is the sensor source real hardware or simulator?

Does fruit identity match the active inspection?

Is a laptop screen or phone display suspected?

Does the evidence appear planar?

Is reference data available?

Do visual and sensor findings disagree?

Is any required evidence stale?

Is the final assessment sufficiently supported?
```

Possible critic states include:

```text
PASSED

WARNING

NEEDS MORE DATA

BLOCKED
```

Possible decision states include:

```text
CONCLUSIVE

MORE EVIDENCE REQUIRED

WAITING FOR ESP32

PHYSICAL FRUIT NOT VERIFIED

CONFLICTING EVIDENCE

INCONCLUSIVE
```

---

# Evidence Agreement

FreshFusion is designed to expose agreement and disagreement between evidence sources.

Example:

```text
VISION ANALYST
Likely Overripe

SENSOR ANALYST
Moderate deterioration signal

REFERENCE ANALYST
Closest class: Normal / Ripe

MULTI-VIEW ANALYST
Physical fruit likely

──────────────────────────────

EVIDENCE AGREEMENT

3 / 4 signals broadly aligned

CONFLICT

Reference evidence is less degraded than visual evidence.

ACTION

Confidence reduced.
Additional rear view recommended.
```

The objective is not to hide everything behind a single number.

The system should show **why** confidence rises or falls.

---

# 8. Deterministic Confidence + Fusion

Only evidence that passes the required gates becomes eligible for final fusion.

The fusion system may combine:

```text
Vision Evidence
Sensor Evidence
Physical Verification
View Coverage
Evidence Freshness
Critic State
Reference Support
```

Current fusion weights and thresholds are experimental.

They must be calibrated using real FreshFusion ground truth before being presented as scientifically validated.

FreshFusion therefore distinguishes between:

```text
Experimental Confidence

and

Validated Accuracy
```

These are not the same thing.

---

# 9. Local AI with Ollama + Gemma

FreshFusion runs Gemma locally through Ollama.

```text
FreshFusion Evidence
        ↓
      Ollama
        ↓
      Gemma
        ↓
Structured Explanation
```

Gemma's role is to:

- summarize evidence,
- explain the assessment,
- describe supporting evidence,
- identify contradictions,
- identify missing evidence,
- recommend the next inspection step,
- and generate human-readable reports.

Example output:

```json
{
  "summary": "Visual evidence suggests advanced ripening.",
  "supporting_evidence": [
    "Brown surface percentage increased",
    "Healthy surface estimate decreased"
  ],
  "contradictions": [
    "Reference evidence appears less degraded"
  ],
  "missing_evidence": [
    "Rear viewpoint"
  ],
  "recommended_next_step": "Capture the rear view of the fruit."
}
```

Gemma does **not** control the core numerical verdict.

It cannot be used to invent:

```text
Sensor values
Freshness scores
ppm values
Accuracy
Validation metrics
Food-safety claims
```

If Ollama is unavailable, the deterministic FreshFusion inspection pipeline should continue to operate.

---

# 10. Human-in-the-Loop Verification

FreshFusion does not treat its own prediction as ground truth.

After an assessment, a reviewer can:

```text
Accept System Assessment

Mark Assessment Incorrect

Add Ground Truth
```

Ground-truth categories are:

```text
Fresh
Ripe
Overripe
Spoiled
```

Human verification is stored separately from:

- public dataset labels,
- reference classifications,
- model predictions,
- heuristic results,
- and fusion outputs.

This creates an auditable feedback loop.

```text
Inspection
    ↓
System Assessment
    ↓
Human Observation
    ↓
Ground Truth
    ↓
Validation Dataset
    ↓
Model Improvement
```

---

# Database Architecture

FreshFusion currently uses **SQLAlchemy**.

SQLite is used for local prototype development.

The architecture can support another relational database through `DATABASE_URL`.

Current important entities include:

```text
FruitSample
│
├── SensorReading[]
├── FruitImage[]
├── FusionResult[]
└── HumanVerification[]

InspectionControl
```

Conceptually, the long-term database architecture is:

```text
Inspection
│
├── Device Session
│   ├── Phone
│   └── ESP32
│
├── Sensor Readings
│
├── Images
│   ├── Front
│   ├── Left
│   ├── Right
│   ├── Back
│   └── Top
│
├── Evidence Events
│
├── Investigation Runs
│   ├── Vision Analyst Output
│   ├── Sensor Analyst Output
│   ├── Reference Analyst Output
│   ├── Multi-View Output
│   ├── Critic Output
│   └── Confidence / Fusion
│
├── Model Version
│
├── LLM Explanation
│
├── Human Verification
│   └── Ground Truth
│
└── Validation Record
```

Future database engineering work includes:

```text
Formal Migrations
Investigation Snapshots
Evidence Event Persistence
Model Version Tracking
Device Session Tracking
Validation Runs
Export / Backup
Dataset Versioning
```

---

# Frontend Workspace

The FreshFusion interface is organized into six primary areas.

```text
Overview
   ↓
Live Inspection
   ↓
Investigation
   ↓
Evidence
   ↓
Dataset & Validation
   ↓
History
```

## Overview

Provides:

- system architecture,
- hardware status,
- supported fruit information,
- investigation workflow,
- and current system availability.

## Live Inspection

Provides:

- active inspection,
- camera feed,
- QR phone pairing,
- multi-view capture,
- sensor readings,
- current evidence,
- physical verification,
- and live status.

## Investigation

The main intelligence workspace.

Displays:

```text
Vision Analyst
Sensor Analyst
Reference Analyst
Multi-View Analyst
Freshness Hypothesis
Evidence Critic
Decision State
Gemma Explanation
Human Verification
```

## Evidence

Displays the chronological inspection record.

Possible evidence events include:

```text
Inspection created
Fruit detected
Image accepted
Image rejected
Sensor reading received
Reference match produced
Physical verification updated
Critic state changed
Fusion recomputed
Human verification added
```

## Dataset & Validation

Responsible for:

- public dataset metadata,
- source licenses,
- class counts,
- FreshFusion-collected samples,
- human labels,
- train/validation/test manifests,
- validation runs,
- confusion matrix,
- precision,
- recall,
- F1 score,
- and per-fruit performance.

No validation percentage should be displayed unless it comes from a real evaluation.

Until then:

```text
NOT YET VALIDATED
```

## History

Allows previous inspections to be reviewed without silently changing the active hardware capture target.

---

# Current Hardware Prototype

```text
                ┌─────────────┐
                │    ESP32    │
                └──────┬──────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
   ┌───────────┐               ┌───────────┐
   │   DHT11   │               │   MQ135   │
   │           │               │           │
   │ Temp      │               │ Raw ADC   │
   │ Humidity  │               │ Response  │
   └───────────┘               └───────────┘


                 PHONE CAMERA
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     Front          Left           Right
       │              │              │
       └──────────────┼──────────────┘
                      │
                    Back
                      │
                     Top
```

Current hardware includes:

| Component | Responsibility |
| --- | --- |
| ESP32 | Sensor acquisition and backend communication |
| DHT11 | Temperature and humidity |
| MQ135 | Raw relative gas-response signal |
| Phone Camera | Multi-view visual evidence |
| Laptop | Backend, database, computer vision, frontend and local AI |

---

# Realtime Communication

FreshFusion uses:

```text
Phone Camera
      ↓
HTTP Image Upload
      ↓
FastAPI
      ↓
Database + Analysis
      ↓
WebSocket
      ↓
React Dashboard
```

ESP32 communication:

```text
ESP32
  ↓
Wi-Fi
  ↓
HTTP Sensor Packet
  ↓
FastAPI
  ↓
Validation
  ↓
Database
  ↓
Fusion / Investigation
  ↓
Realtime UI Update
```

---

# Project Structure

```text
Fresh-Fusion-/
│
├── README.md
├── start_freshfusion.ps1
├── setup_ollama.ps1
├── setup_reference_data.ps1
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   │   ├── investigation_core/
│   │   │   ├── image_analysis.py
│   │   │   ├── physical_validation.py
│   │   │   ├── sensor_assessment.py
│   │   │   ├── reference_match.py
│   │   │   ├── fusion.py
│   │   │   └── ollama_client.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── main.py
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── overview/
│   │   │   ├── inspection/
│   │   │   ├── investigation/
│   │   │   ├── evidence/
│   │   │   ├── validation/
│   │   │   └── history/
│   │   │
│   │   ├── hooks/
│   │   ├── layout/
│   │   ├── shared/
│   │   ├── components/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   └── phone.jsx
│   │
│   ├── tests/
│   └── package.json
│
├── esp32/
│   └── freshfusion_node.ino
│
├── ai/
│   ├── train.py
│   ├── export_dataset.py
│   ├── sync_public_reference.py
│   └── requirements.txt
│
└── docs/
    │
    ├── INVESTIGATION_FOUNDATION.md
    ├── IMPLEMENTATION_REPORT.md
    ├── LOCAL_NETWORK.md
    ├── PHYSICAL_VALIDATION.md
    │
    └── architecture/
        ├── README.md
        ├── BACKEND.md
        ├── FRONTEND.md
        ├── DATABASE.md
        ├── AI.md
        ├── HARDWARE.md
        ├── UI.md
        ├── TESTING.md
        ├── TEAM_WORKFLOW.md
        └── MASTER_CHECKLIST.md
```

---

# Quick Start

Clone the repository:

```bash
git clone https://github.com/thetarunsahu/Fresh-Fusion-.git
cd Fresh-Fusion-
```

On Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_freshfusion.ps1
```

The launcher starts:

```text
React / Vite Dashboard
FastAPI Backend
Phone Camera HTTPS Tunnel
FreshFusion Runtime Services
```

---

# Ollama + Gemma Setup

FreshFusion uses Ollama for local Gemma inference.

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_ollama.ps1
```

Default configuration:

```text
Ollama URL
http://127.0.0.1:11434

Model
gemma3:4b
```

Health endpoint:

```text
GET /api/v1/ai/ollama/health
```

Investigation explanation endpoint:

```text
POST /api/v1/samples/{sample_id}/investigation/explain
```

---

# Backend Development

Create the environment:

```powershell
python -m venv backend/.venv
```

Install dependencies:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Run FastAPI:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Default API:

```text
http://localhost:8000
```

---

# Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Production build:

```bash
npm run build
```

---

# Testing

Backend tests:

```powershell
.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -v
```

Frontend build:

```bash
cd frontend
npm run build
```

Browser tests:

```bash
npx playwright install chromium
npm test
```

Automated tests do not replace:

```text
Real Fruit Testing
Phone Permission Testing
ESP32 Testing
Sensor Calibration
Physical Multi-View Testing
Ollama Integration Testing
Real Network Testing
```

---

# Evidence Lifecycle

```text
DATA ACQUISITION
       ↓
DATA VALIDATION
       ↓
DATA STORAGE
       ↓
EVIDENCE PROCESSING
       ↓
ANALYST OUTPUTS
       ↓
FRESHNESS HYPOTHESIS
       ↓
EVIDENCE CRITIC
       ↓
CONFIDENCE / FUSION
       ↓
FINAL OR INCONCLUSIVE RESULT
       ↓
GEMMA EXPLANATION
       ↓
HUMAN VALIDATION
       ↓
GROUND TRUTH
       ↓
VALIDATION DATASET
       ↓
FUTURE MODEL IMPROVEMENT
```

---

# Engineering Priorities

```text
1. Reliable Evidence Acquisition
          ↓
2. Stable Database Architecture
          ↓
3. Explicit Inspection / Device Pairing
          ↓
4. Vision Intelligence
          ↓
5. Sensor Intelligence
          ↓
6. Reference Analysis
          ↓
7. Multi-View Verification
          ↓
8. Investigation Analysts
          ↓
9. Freshness Hypothesis
          ↓
10. Evidence Critic
          ↓
11. Confidence / Fusion
          ↓
12. Ollama + Gemma Explanation
          ↓
13. Human Ground Truth
          ↓
14. Dataset Validation
          ↓
15. UI / UX Refinement
          ↓
16. Demo Reliability
```

---

# Scientific Guardrails

FreshFusion is an experimental engineering prototype.

The project intentionally avoids unsupported claims.

## MQ135

Raw MQ135 values are treated as relative electrical measurements.

Do not claim calibrated ppm without proper calibration.

## Reference Similarity

Reference similarity is not model accuracy.

## Model Accuracy

Do not claim trained-model accuracy unless:

```text
Model artifact exists
        +
Independent test set exists
        +
Evaluation has been completed
```

## Physical Verification

Phone-based physical verification is probabilistic.

It is not guaranteed liveness detection.

## Freshness Score

Fusion weights and thresholds remain experimental until calibrated.

## Food Safety

FreshFusion is not a food-safety certification system.

---

# Documentation

Detailed engineering documentation is available under:

```text
docs/architecture/
```

Recommended reading order:

```text
README.md
    ↓
MASTER_CHECKLIST.md
    ↓
BACKEND.md
    ↓
FRONTEND.md
    ↓
DATABASE.md
    ↓
AI.md
    ↓
HARDWARE.md
    ↓
UI.md
    ↓
TESTING.md
    ↓
TEAM_WORKFLOW.md
```

Additional technical documentation:

```text
docs/INVESTIGATION_FOUNDATION.md
docs/IMPLEMENTATION_REPORT.md
docs/LOCAL_NETWORK.md
docs/PHYSICAL_VALIDATION.md
```

---

# Current Development Status

FreshFusion currently includes working foundations for:

- FastAPI backend
- React/Vite frontend
- ESP32 telemetry ingestion
- phone-camera capture
- sample-based inspection workflow
- OpenCV fruit analysis
- Apple/Banana identity support
- reference dataset indexing
- reference similarity analysis
- sensor evidence processing
- MQ135 relative response handling
- multi-view physical verification
- evidence critic
- deterministic decision logic
- human verification
- evidence timeline
- inspection history
- dataset/validation workspace
- WebSocket updates
- Ollama/Gemma integration foundation
- automated backend tests
- browser regression tests

Still requiring substantial work:

- real sensor calibration
- reliable device-session binding
- formal database migrations
- persistent investigation snapshots
- validation-run storage
- model-version tracking
- real ground-truth collection
- sample-level dataset splitting
- trained freshness model validation
- final UI redesign
- full real-hardware testing
- demo recovery workflow
- report generation
- security hardening

---

# What Makes FreshFusion Different?

FreshFusion is not built around the question:

> **“Can AI classify this fruit?”**

It is built around:

> **“Can the available evidence justify this assessment?”**

That difference changes the entire system.

FreshFusion is designed to:

- combine multiple sensing modalities,
- inspect visual and environmental evidence independently,
- verify physical multi-view consistency,
- challenge its own hypothesis,
- detect missing evidence,
- detect contradictions,
- reject stale or simulated evidence,
- separate prediction from ground truth,
- explain assessments locally,
- preserve an auditable inspection history,
- and improve through human-labelled validation.

---

# Vision

The long-term goal of FreshFusion is to evolve from a prototype freshness detector into a reliable fruit-quality investigation platform capable of supporting:

```text
Warehouses
Retail Procurement
Cold Storage
Fruit Sorting
Quality Inspection
Post-Harvest Monitoring
Research Experiments
Supply Chain Quality Control
```

Future research directions may include:

```text
MobileNetV3 Freshness Classification
DINOv2 / CLIP Embeddings
FAISS Reference Retrieval
Model Registry
Dataset Versioning
Calibration Experiments
Depth / Stereo Vision
Better Gas Sensors
Controlled Multi-View Capture
Edge Deployment
Multi-Fruit Expansion
Longitudinal Freshness Tracking
```

---

<div align="center">

# FreshFusion

### Inspect. Challenge. Verify. Explain.

**An evidence-grounded multimodal fruit-quality investigation platform built for traceable decisions, not just predictions.**

</div>
