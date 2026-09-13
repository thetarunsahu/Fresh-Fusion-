# 🍎 FreshFusion

### Evidence-Grounded Multimodal Fruit Quality Investigation System

> **Inspect. Challenge. Verify. Explain.**

FreshFusion is not just another fruit-classification dashboard.

It is a **multimodal fruit quality investigation platform** that combines:

- Smartphone vision
- ESP32 sensor telemetry
- Multi-view inspection
- Surface analysis
- MQ135 relative gas-response tracking
- Evidence criticism
- Deterministic fusion
- Human verification
- Local AI explanation using Gemma via Ollama

The goal is simple:

> **Do not force a freshness verdict when the evidence is weak.**

---

## 🌱 Why FreshFusion Exists

Most freshness systems rely on a single image, a single sensor, or a black-box prediction.

FreshFusion follows a different philosophy.

```text
INPUT
  ↓
EVIDENCE
  ↓
INDEPENDENT ANALYSIS
  ↓
EVIDENCE CRITIC
  ↓
DECISION
  ↓
EXPLANATION
  ↓
HUMAN VERIFICATION
```

Instead of asking:

> “What class does the AI predict?”

FreshFusion asks:

> “What evidence supports this result, what conflicts with it, and is there enough evidence to trust it?”

---

# ⚡ Core Idea

FreshFusion investigates fruit quality using multiple evidence sources:

```text
                    ┌─────────────────────┐
                    │   Physical Fruit    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
        Smartphone Camera                 ESP32 Node
                │                             │
        Visual Evidence                 Sensor Evidence
                │                             │
        ┌───────┴────────┐          ┌─────────┴─────────┐
        │                │          │                   │
 Fruit Identity     Surface Analysis   Temperature     Humidity
        │                │                   │
        │                │               MQ135 Raw
        │                │                   │
        └──────────┬─────┴──────────────┬────┘
                   │                    │
                   ▼                    ▼
             Evidence Analysts
                   │
                   ▼
             Evidence Critic
                   │
         ┌─────────┴──────────┐
         │                    │
   Evidence sufficient?     Evidence weak?
         │                    │
        YES                  NO
         │                    │
         ▼                    ▼
 Deterministic Fusion   Request More Evidence
         │
         ▼
 Freshness Assessment
         │
         ▼
 Gemma Explanation
         │
         ▼
 Human Verification
```

---

# 🍌 Supported Fruits

Current prototype supports:

- Apple
- Banana
- Tomato

Fruit identity is initially suggested automatically using visual evidence.

Because single-frame vision can be noisy, FreshFusion also supports **operator confirmation**.

```text
Camera Suggestion
      ↓
Apple / Banana / Tomato
      ↓
Operator Confirmation
      ↓
Stable Inspection Identity
```

This prevents one noisy camera frame from contaminating the whole freshness assessment.

---

# 📷 One Camera Is Enough

FreshFusion does **not** require three physical cameras.

A single smartphone camera can identify the fruit.

Additional views are used to improve:

- Surface coverage
- Damage visibility
- Physical-fruit verification
- Confidence in the assessment

Current workflow:

```text
Front View
   ↓
Left View
   ↓
Right View
   ↓
Multi-view Evidence
```

The system uses **multiple viewpoints**, not multiple mandatory cameras.

---

# 🧠 Hybrid Investigation Architecture

FreshFusion uses a hybrid architecture.

Not every module is an LLM agent.

Some components use computer vision, some use deterministic logic, and some use local AI only for explanation.

### Main Investigation Modules

#### 1. Intake / Identity Module

Determines the inspection fruit and keeps the identity stable across the session.

Current modes:

```text
Auto Identity
Apple
Banana
Tomato
```

---

#### 2. Vision Analyst

Processes smartphone images and extracts:

- Fruit presence
- Fruit identity
- Surface colour
- Brown regions
- Dark regions
- Texture
- Edge density
- Roughness
- Surface damage estimate
- Healthy surface estimate
- Frame quality

---

#### 3. Sensor Analyst

Processes physical ESP32 telemetry.

Current sensors:

```text
DHT11
├── Temperature
└── Humidity

MQ135
└── Raw / Relative Gas Response
```

Important:

> MQ135 raw ADC values are **not treated as calibrated ethylene ppm values**.

FreshFusion uses them as relative evidence only.

---

# 🧪 MQ135 Baseline Logic

A raw MQ135 number alone has very little meaning.

FreshFusion first establishes a local **empty-chamber baseline**.

```text
Empty Chamber
     ↓
Record Multiple MQ135 Readings
     ↓
Baseline Mean
     ↓
Insert Fruit
     ↓
Current MQ135 Reading
     ↓
Gas Delta
```

Example:

```text
Empty Chamber Baseline : 1650 ADC
Fruit Reading          : 1872 ADC
Gas Delta              : +222 ADC
```

The system therefore compares the fruit against the same chamber environment instead of assuming a universal gas value.

---

# 🔍 Image Quality Gate

FreshFusion does not blindly trust every camera frame.

Before using visual evidence, it checks:

- Fruit presence
- Centering
- Blur
- Lighting
- Surface visibility
- Multiple fruit-like regions
- Screen/photo suspicion
- View diversity

If visual evidence is poor:

```text
Result = HOLD
```

instead of forcing a freshness prediction.

---

# 🛡 Evidence Critic

This is one of the most important components of FreshFusion.

The Evidence Critic checks whether different evidence sources agree.

Example:

```text
Vision Analyst     → Overripe
Sensor Analyst     → Elevated gas response
Reference Analyst  → Ripe / Overripe
Multi-view Check   → Valid

Agreement          → Strong
```

But if the evidence conflicts:

```text
Vision Analyst     → Fresh
Sensor Analyst     → Strong change
Reference Analyst  → Overripe
Multi-view Check   → Weak
```

FreshFusion can return:

```text
MORE EVIDENCE REQUIRED
```

instead of producing a misleading final answer.

---

# 📊 Provisional vs Final Score

FreshFusion separates live estimation from verified output.

### Provisional Quality Score

Shown while evidence is still being collected.

Example:

```text
62 / 100
```

This helps the operator understand the current trend.

### Final Freshness Score

Released only when required evidence checks pass.

The system clearly distinguishes:

```text
LIVE ESTIMATE
vs
VERIFIED RESULT
```

---

# ⚙️ Deterministic Fusion

FreshFusion does not allow the LLM to decide freshness.

Current prototype fusion combines sensor and vision evidence using deterministic logic.

Example experimental weighting:

```text
Sensor Score × 0.48
+
Vision Score × 0.52
```

These weights are currently experimental and are not claimed as scientifically validated constants.

---

# 🤖 FreshFusion Assistant

FreshFusion includes a proactive assistant inside the inspection workspace.

The assistant does not wait only for questions.

It continuously interprets the current evidence.

Example:

```text
What changed?
Gas response increased compared with recent readings.

What does it mean?
The fruit-chamber gas signal is changing relative to the local baseline.

What should you do?
Continue the inspection and compare the sensor trend with the visual condition.
```

The assistant can also answer questions such as:

```text
Why is the score low?

What should I do with this fruit?

Explain the MQ135 reading.

Which evidence is missing?

Why has FreshFusion not released the final result?
```

---

# 🧠 Gemma + Ollama

FreshFusion uses a local Gemma model through Ollama as an **explanation layer**.

Gemma does not control the final freshness verdict.

```text
Deterministic Decision
        ↓
Gemma
        ↓
Human-readable Explanation
```

If Ollama is unavailable, FreshFusion falls back to a deterministic evidence-based assistant.

Core freshness logic therefore continues working even without the LLM.

---

# 👤 Human-in-the-Loop Verification

FreshFusion keeps humans inside the validation cycle.

Supported actions include:

```text
Accept System Assessment

Mark as Incorrect

Add Ground Truth

Manual Override
```

Human feedback is stored along with the evidence snapshot.

This allows future validation and dataset improvement.

---

# 🧬 Ground Truth & Dataset Development

FreshFusion is designed to grow its own labelled dataset.

Each physical fruit can be assigned a specimen ID.

Example:

```text
APPLE-01
BANANA-04
TOMATO-02
```

Multiple views and repeated inspections of the same fruit remain linked together.

This helps prevent dataset leakage.

---

# 📈 Validation Engine

FreshFusion can calculate real validation metrics once enough ground-truth data exists.

Supported metrics include:

```text
Accuracy
Precision
Recall
F1 Score
Confusion Matrix
Per-Class Performance
Fruit-wise Performance
```

If enough validation data does not exist, the system does **not** display fake accuracy.

Instead it reports:

```text
NOT YET VALIDATED
```

or

```text
PRELIMINARY
```

---

# 🖥 Live Inspection Workspace

The FreshFusion interface is designed around decisions first and raw engineering evidence second.

Main inspection view includes:

```text
Fruit Identity
Current Condition
Recommended Action
Risk
Quality Score
Temperature
Humidity
MQ135 Raw
Gas Delta
Surface Damage
Evidence Status
ESP32 Status
Camera Views
FreshFusion Assistant
```

Detailed analysis remains available for engineering review.

---

# 📊 Detailed Analysis

The detailed inspection panel includes:

### Sensor Trend

Live plots for:

- Temperature
- Humidity
- MQ135 raw response

### Image Analysis

- Original frame
- Defect overlay
- Texture map
- Fruit mask
- Edge map

### Surface Profile

Fruit-dependent colour analysis.

### Texture Analysis

- Entropy
- Roughness
- Edge density
- Laplacian variance
- Healthy surface estimate

### Observations

Automatically highlights visual regions requiring attention.

---

# 🌐 Backend Architecture

FreshFusion uses FastAPI.

Main API families:

```text
/api/v1/samples
/api/v1/sensors
/api/v1/images
/api/v1/datasets
/api/v1/investigation
/api/v1/auth
```

Realtime updates are delivered using WebSockets.

---

# 🗄 Database

FreshFusion uses SQLAlchemy-based persistent storage.

Stored information includes:

```text
Fruit Samples
Sensor Readings
Fruit Images
Fusion Results
Inspection Profiles
Human Verification
Investigation Snapshots
Inspection Events
```

Conceptually:

```text
Inspection
│
├── Fruit Identity
├── Sensor Readings
├── Images
│   ├── Front
│   ├── Left
│   └── Right
├── Evidence Events
├── Investigation Results
├── Fusion Output
├── AI Explanation
└── Human Verification
```

---

# 📡 Hardware Architecture

Current prototype:

```text
ESP32
├── DHT11
│   ├── Temperature
│   └── Humidity
│
├── MQ135
│   └── Relative gas response
│
└── Wi-Fi
    ↓
FastAPI Backend
```

Camera:

```text
Smartphone Rear Camera
        ↓
Trusted HTTPS Connection
        ↓
FreshFusion Backend
```

---

# 🔐 Camera Security

Modern mobile browsers block camera access on untrusted HTTP pages.

FreshFusion therefore provides a trusted HTTPS phone-camera link during startup.

The launcher creates the connection automatically.

```powershell
.\start_freshfusion.ps1
```

The generated phone link can then be opened through the QR code shown in the dashboard.

---

# 🧩 Technology Stack

### Backend

```text
Python
FastAPI
SQLAlchemy
OpenCV
WebSockets
Ollama
Gemma
```

### Frontend

```text
React
Vite
Recharts
Lucide
QRCode
```

### Hardware

```text
ESP32
DHT11
MQ135
Smartphone Camera
```

---

# 📁 Project Structure

```text
FreshFusion/
│
├── backend/
│   ├── app/
│   ├── services/
│   ├── api/
│   └── tests/
│
├── frontend/
│   ├── src/
│   ├── features/
│   ├── components/
│   └── tests/
│
├── esp32/
│
├── ai/
│
├── models/
│
├── uploads/
│
├── docs/
│
└── start_freshfusion.ps1
```

---

# 🚀 Quick Start

### 1. Start FreshFusion

```powershell
cd FreshFusion
Set-ExecutionPolicy -Scope Process Bypass
.\start_freshfusion.ps1
```

The launcher starts:

```text
FastAPI Backend
React Frontend
Phone HTTPS Tunnel
```

---

### 2. Start an Inspection

```text
Open Dashboard
      ↓
New Inspection
      ↓
Auto Identity
      ↓
Show Fruit
      ↓
Confirm Identity if Needed
      ↓
Capture Views
      ↓
Collect ESP32 Evidence
```

---

### 3. MQ135 Baseline

Before inserting the fruit:

```text
Empty Chamber
      ↓
Record baseline readings
      ↓
Insert fruit
      ↓
Compare relative gas response
```

---

# 🧪 Scientific Guardrails

FreshFusion intentionally avoids unsupported claims.

We do not claim:

```text
MQ135 raw ADC = exact ethylene ppm
```

We do not claim:

```text
Reference similarity = model accuracy
```

We do not claim:

```text
Fusion confidence = validated accuracy
```

We do not claim:

```text
RGB camera can reliably measure internal fruit quality
```

We do not claim:

```text
Usable life without labelled time-series calibration
```

Instead, FreshFusion clearly separates:

```text
Observed Evidence
↓
Experimental Assessment
↓
Validated Claims
```

---

# 🎯 What Makes FreshFusion Different

FreshFusion is not built around one prediction.

It is built around **evidence agreement**.

```text
Traditional System
Image
  ↓
Classifier
  ↓
Result
```

FreshFusion:

```text
Camera + Sensors + Multi-view + Reference
                 ↓
          Independent Analysis
                 ↓
           Evidence Critic
                 ↓
       Deterministic Verification
                 ↓
             Decision
                 ↓
          Local AI Explanation
                 ↓
         Human Confirmation
```

---

# 🏆 SIH Vision

FreshFusion aims to evolve from a prototype into an affordable fruit-quality decision-support system for:

- Warehouses
- Retail procurement centres
- Fruit distributors
- Cold-chain operators
- Storage facilities
- Farmers and FPOs
- Post-harvest quality teams

The long-term goal is not simply:

> “Detect whether a fruit is fresh.”

The goal is:

> **Build a system that can explain why it believes a fruit is fresh, identify when the evidence is weak, and continuously improve from real-world verification.**

---

## FreshFusion

### Decision first. Evidence behind it.

**Team OrchardX**
