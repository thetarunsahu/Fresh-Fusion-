<div align="center">

# 🍎 FreshFusion

### AI-Powered Multimodal Fruit Freshness Intelligence System

<img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&weight=700&size=24&duration=3000&pause=1000&color=39FF88&center=true&vCenter=true&width=900&lines=Computer+Vision+%2B+Gas+Sensors+%2B+Environmental+Data;Real-Time+Fruit+Freshness+Detection;Color+%7C+Texture+%7C+Defects+%7C+Gas+Analysis;From+Raw+Fruit+to+Actionable+Freshness+Intelligence" alt="FreshFusion Typing Animation" />

<br/>

> **FreshFusion transforms a fruit sample into measurable freshness intelligence by combining computer vision, environmental sensing, gas analysis, AI classification, and real-time data visualization.**

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![React](https://img.shields.io/badge/React-Dashboard-61DAFB?style=for-the-badge\&logo=react\&logoColor=black)
![ESP32](https://img.shields.io/badge/ESP32-IoT-E7352C?style=for-the-badge\&logo=espressif\&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=for-the-badge\&logo=opencv\&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge\&logo=postgresql\&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-AI-EE4C2C?style=for-the-badge\&logo=pytorch\&logoColor=white)

</div>

---

## The Idea

Most fruit freshness systems depend on only **one source of information**.

Some use images.

Some use gas sensors.

Some monitor temperature and humidity.

**FreshFusion combines all of them.**

```text
                  F R E S H F U S I O N
             Multimodal Freshness Intelligence

                         ┌─────────┐
                         │  FRUIT  │
                         └────┬────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼

        ┌───────────────┐           ┌───────────────┐
        │ SENSOR LAYER  │           │ VISION LAYER  │
        │               │           │               │
        │ Gas / VOC     │           │ RGB / HSV     │
        │ Temperature   │           │ Texture       │
        │ Humidity      │           │ Defects       │
        │ Environment   │           │ AI Features   │
        └───────┬───────┘           └───────┬───────┘
                │                           │
                └─────────────┬─────────────┘
                              │
                              ▼

                     ┌─────────────────┐
                     │  FUSION ENGINE  │
                     │                 │
                     │ Sensor Score    │
                     │ Vision Score    │
                     │ AI Confidence   │
                     └────────┬────────┘
                              │
                              ▼

                     ┌─────────────────┐
                     │ FINAL ANALYSIS  │
                     │                 │
                     │ Fresh           │
                     │ Ripe            │
                     │ Overripe        │
                     │ Spoiled         │
                     └────────┬────────┘
                              │
                              ▼

                REAL-TIME ANALYTICS DASHBOARD
```

---

# Why FreshFusion?

A fruit may look healthy from the outside while biochemical changes have already started internally.

Similarly, environmental and gas readings alone may not reveal visible defects such as:

* discoloration
* bruising
* fungal spots
* surface degradation
* texture changes
* abnormal ripening patterns

FreshFusion solves this by creating a **multimodal digital profile** of every fruit sample.

---

## One Fruit. One Complete Digital Profile.

Every analyzed fruit receives a unique sample identity.

```text
Sample ID       : BN-00042
Fruit           : Banana
Captured At     : 29 Aug 2026 — 12:10 PM

Temperature     : 27.4 °C
Humidity        : 64.2 %
Gas Level       : 620 ppm

Yellow Surface  : 62 %
Brown Surface   : 27 %
Dark Damage     : 4 %

Texture Score   : 0.69
Healthy Surface : 66 %

Vision AI       : Overripe — 89 %
Sensor Analysis : Overripe — 84 %

──────────────────────────────────

FINAL RESULT

OVERRIPE

Freshness Score : 31 / 100
Confidence      : 91 %
Spoilage Risk   : HIGH
```

---

# System Architecture

```mermaid
flowchart LR

    F[Fruit Sample]

    F --> CAM[Camera]
    F --> SENS[Sensor Chamber]

    SENS --> MQ[Gas / VOC Sensor]
    SENS --> DHT[Temperature & Humidity]

    MQ --> ESP[ESP32]
    DHT --> ESP

    ESP -->|Wi-Fi / HTTP| API[FastAPI Backend]

    CAM --> IMG[Image Upload]
    IMG --> CV[Computer Vision Engine]

    CV --> COLOR[Color Analysis]
    CV --> TEXTURE[Texture Analysis]
    CV --> DEFECT[Defect Detection]
    CV --> MODEL[AI Classification]

    API --> DB[(PostgreSQL)]
    COLOR --> DB
    TEXTURE --> DB
    DEFECT --> DB
    MODEL --> DB

    DB --> FUSION[Freshness Fusion Engine]

    FUSION --> RESULT[Final Freshness Score]

    RESULT --> DASH[React Dashboard]
```

---

# Computer Vision Intelligence

FreshFusion does not simply send an image to an AI model and display a label.

The vision pipeline extracts measurable visual characteristics from the fruit.

### Color Intelligence

```text
RGB Analysis
HSV Analysis
Color Distribution
Green Percentage
Yellow Percentage
Brown Percentage
Black Percentage
Color Uniformity
Discoloration Index
```

Example:

```text
┌──────────────────────────────┐
│      COLOR DISTRIBUTION      │
├──────────────────────────────┤
│ Yellow              62 %     │
│ Brown               27 %     │
│ Green                7 %     │
│ Dark / Black         4 %     │
└──────────────────────────────┘
```

---

## Texture Intelligence

Fruit skin texture changes significantly during ripening and spoilage.

FreshFusion extracts texture features such as:

| Feature       | Purpose                            |
| ------------- | ---------------------------------- |
| Contrast      | Measures intensity variation       |
| Homogeneity   | Measures texture uniformity        |
| Energy        | Measures repeated texture patterns |
| Entropy       | Measures surface randomness        |
| Correlation   | Measures pixel relationships       |
| Roughness     | Estimates surface irregularity     |
| Edge Density  | Detects structural changes         |
| GLCM Features | Statistical texture representation |
| LBP Features  | Local surface pattern analysis     |

---

# Surface Defect Analysis

FreshFusion can analyze visible fruit damage including:

```text
Brown Spots
Black Spots
Bruised Regions
Discolored Regions
Healthy Surface
Damaged Surface
Potential Decay Regions
```

Future visualization:

```text
Original Image

       ↓

Fruit Segmentation

       ↓

Surface Defect Detection

       ↓

Highlighted Damage Map

       ↓

Freshness Classification
```

---

# Sensor Intelligence

The hardware system continuously captures environmental and gas information around the fruit.

### Current Sensor Layer

| Sensor Data       | Purpose                                                 |
| ----------------- | ------------------------------------------------------- |
| Temperature       | Detect storage and ripening conditions                  |
| Humidity          | Monitor moisture conditions                             |
| Gas / VOC Reading | Detect volatile compounds associated with fruit changes |
| Raw ADC Data      | Preserve original sensor readings                       |
| Timestamp         | Track freshness changes over time                       |

---

## ESP32 → Backend Communication

The ESP32 sends sensor readings to the FreshFusion backend over Wi-Fi.

Example payload:

```json
{
  "device_id": "FRESHFUSION_NODE_01",
  "sample_id": "BN-00042",
  "temperature": 27.4,
  "humidity": 64.2,
  "mq135_raw": 1840,
  "gas_ppm": 620
}
```

The backend:

```text
Receives Data
      ↓
Validates Data
      ↓
Links Data With Sample ID
      ↓
Stores Reading
      ↓
Updates Live Dashboard
      ↓
Feeds Freshness Engine
```

---

# Freshness Fusion Engine

This is the core intelligence layer of FreshFusion.

Instead of trusting a single AI prediction, the system combines independent indicators.

```text
             IMAGE INTELLIGENCE
                     │
                     │
      ┌──────────────┼──────────────┐
      │              │              │
    COLOR         TEXTURE        DEFECTS
      │              │              │
      └──────────────┬──────────────┘
                     │
                  AI SCORE
                     │
                     ▼
              ┌─────────────┐
              │             │
              │   FUSION    │
              │   ENGINE    │
              │             │
              └──────┬──────┘
                     ▲
                     │
             SENSOR INTELLIGENCE
                     │
          ┌──────────┼──────────┐
          │          │          │
        GAS        TEMP      HUMIDITY
```

Possible scoring model:

```text
Vision Score          40 %
Gas Intelligence      35 %
Environmental Score   15 %
Texture / Defect Risk 10 %

                  ↓

       FINAL FRESHNESS SCORE
```

Weights will eventually be learned or calibrated using experimental data rather than being permanently fixed.

---

# Freshness Classes

FreshFusion is being designed around four primary freshness states.

<table>
<tr>
<td align="center">

### FRESH

Low spoilage indicators
Healthy appearance
Normal environmental readings

</td>

<td align="center">

### RIPE

Optimal consumption stage
Expected color transition
Stable sensor profile

</td>
</tr>

<tr>
<td align="center">

### OVERRIPE

Strong ripening indicators
Increasing gas activity
Surface degradation begins

</td>

<td align="center">

### SPOILED

High spoilage indicators
Severe visual defects
Unsafe / unusable condition

</td>
</tr>
</table>

---

# Real-Time Dashboard

The FreshFusion dashboard acts as the control center for the complete system.

```text
┌─────────────────────────────────────────────────────────────┐
│                         FRESHFUSION                         │
│                  FRUIT INTELLIGENCE SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   BANANA                         FRESHNESS SCORE             │
│   Sample BN-00042                       31 / 100             │
│                                      OVERRIPE               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Temperature     Humidity       Gas Level      AI Score     │
│     27.4°C          64%          620 ppm          89%       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                   LIVE SENSOR GRAPH                         │
│                                                             │
│       Gas ───────────────╮                                  │
│                         ╰────────                           │
│       Temp ─────────────────────                            │
│       Humidity ────────────────                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ IMAGE ANALYSIS                                              │
│                                                             │
│ Yellow 62% │ Brown 27% │ Dark 4% │ Healthy 66%             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ AI CLASSIFICATION                                           │
│                                                             │
│ Fresh      ███                               5%             │
│ Ripe       ███████                          16%             │
│ Overripe   █████████████████████████████    74%             │
│ Spoiled    ███                               5%             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ RECOMMENDATION                                              │
│                                                             │
│ Consume Soon                                                │
│ Estimated usable period: < 1 Day                            │
│ Spoilage Risk: HIGH                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# Dashboard Modules

### Overview

Global statistics and current system state.

```text
Total Samples
Fresh Fruits
Overripe Fruits
Spoiled Fruits
Active Sensor Nodes
Average Freshness Score
```

### Live Analysis

Displays the currently analyzed fruit.

### Sensor Monitor

Real-time charts for:

```text
Temperature
Humidity
Gas / VOC
Raw Sensor Values
```

### Vision Lab

Displays:

```text
Original Image
Segmented Fruit
Color Map
Texture Map
Defect Map
AI Heatmap
```

### Sample History

Every fruit analysis is stored for future comparison.

### Analytics

Compare fruit degradation over time.

---

# Backend Architecture

The backend is powered by **FastAPI**.

```text
                    FASTAPI
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
 SENSOR API        IMAGE API        SAMPLE API
       │               │                │
       ▼               ▼                ▼
 Validation        OpenCV          Sample Manager
       │               │                │
       └───────────────┼────────────────┘
                       │
                       ▼
                    DATABASE
                       │
                       ▼
                 FUSION ENGINE
                       │
                       ▼
                    RESULT
```

Planned API structure:

```http
POST /api/sensors/readings
POST /api/samples
POST /api/images/upload
POST /api/analysis/image
POST /api/analysis/fusion

GET  /api/samples
GET  /api/samples/{sample_id}
GET  /api/sensors/latest
GET  /api/samples/{sample_id}/history

WS   /ws/live
```

---

# Database

FreshFusion stores the entire life cycle of a fruit sample.

```text
FRUIT SAMPLE
    │
    ├── Sensor Readings
    │
    ├── Images
    │
    ├── Color Features
    │
    ├── Texture Features
    │
    ├── Defect Features
    │
    ├── AI Predictions
    │
    └── Final Analysis
```

Main tables:

```text
fruits
sensor_readings
images
image_features
ai_predictions
final_results
devices
```

---

# Technology Stack

<table>
<tr>
<td><b>Layer</b></td>
<td><b>Technology</b></td>
</tr>

<tr>
<td>IoT Controller</td>
<td>ESP32</td>
</tr>

<tr>
<td>Backend</td>
<td>Python + FastAPI</td>
</tr>

<tr>
<td>Frontend</td>
<td>React + Vite</td>
</tr>

<tr>
<td>Styling</td>
<td>Tailwind CSS</td>
</tr>

<tr>
<td>Charts</td>
<td>Recharts</td>
</tr>

<tr>
<td>Computer Vision</td>
<td>OpenCV + NumPy + scikit-image</td>
</tr>

<tr>
<td>AI</td>
<td>PyTorch</td>
</tr>

<tr>
<td>Database</td>
<td>PostgreSQL</td>
</tr>

<tr>
<td>Real-Time Communication</td>
<td>WebSocket</td>
</tr>

<tr>
<td>Hardware Communication</td>
<td>HTTP / Wi-Fi</td>
</tr>

</table>

---

# Repository Structure

```text
FreshFusion/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── charts/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── App.jsx
│   │
│   └── package.json
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── sensors.py
│   │   │   ├── samples.py
│   │   │   ├── images.py
│   │   │   └── analysis.py
│   │   │
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   │
│   │   ├── image_processing/
│   │   │   ├── segmentation.py
│   │   │   ├── color_analysis.py
│   │   │   ├── texture_analysis.py
│   │   │   └── defect_detection.py
│   │   │
│   │   ├── ai/
│   │   │   ├── model.py
│   │   │   └── predict.py
│   │   │
│   │   ├── fusion/
│   │   │   └── freshness_engine.py
│   │   │
│   │   └── main.py
│
├── esp32/
│   └── freshfusion_node.ino
│
├── models/
│   └── fruit_freshness_model.pt
│
├── uploads/
│
├── datasets/
│
├── docs/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Development Roadmap

```text
PHASE 01
Backend Foundation
████████████████████░░░░░░░░░░

PHASE 02
ESP32 Live Sensor Integration
██████████░░░░░░░░░░░░░░░░░░░

PHASE 03
Real-Time Dashboard
████████░░░░░░░░░░░░░░░░░░░░░

PHASE 04
Computer Vision Pipeline
████░░░░░░░░░░░░░░░░░░░░░░░░░

PHASE 05
AI Freshness Model
██░░░░░░░░░░░░░░░░░░░░░░░░░░░

PHASE 06
Multimodal Fusion Engine
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

PHASE 07
Validation & Calibration
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

---

# Future Intelligence Layer

FreshFusion is designed to grow beyond basic freshness classification.

Future capabilities include:

```text
Fruit Shelf-Life Prediction
Ripening Curve Estimation
Spoilage Forecasting
Batch Quality Monitoring
Fruit-to-Fruit Comparison
Automatic Fruit Identification
Anomaly Detection
Cold Storage Monitoring
Retail Inventory Integration
QR-Based Fruit History
Mobile Application
Cloud Analytics
Multi-Sensor Calibration
Explainable AI
```

---

# Potential Applications

FreshFusion can eventually be adapted for:

* Fruit retailers
* Warehouses
* Cold storage facilities
* Food supply chains
* Farmers
* Quality inspection centers
* Food processing industries
* Research laboratories
* Smart kitchens
* Supermarkets

---

# What Makes FreshFusion Different?

```text
Traditional Image Classifier

Image
  ↓
AI
  ↓
Fresh / Spoiled
```

FreshFusion:

```text
                       FRUIT

        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
      IMAGE            GAS           ENVIRONMENT
        │                │                │
     COLOR             VOC          TEMPERATURE
     TEXTURE                           HUMIDITY
     DEFECTS
        │                │                │
        └────────────────┼────────────────┘
                         ▼

                 MULTIMODAL FUSION

                         ▼

             DATA-DRIVEN FRESHNESS SCORE

                         ▼

                  RECOMMENDATION
```

The goal is not simply to classify a fruit.

The goal is to **understand its condition.**

---

# Research Direction

FreshFusion explores the relationship between:

```text
Visual degradation
        +
Surface texture changes
        +
Fruit color transitions
        +
Volatile gas behavior
        +
Environmental conditions
        +
AI predictions
```

to build a more reliable fruit freshness assessment system.

---

# Project Status

> **FreshFusion is currently under active development.**

Hardware integration, computer vision pipelines, backend services, AI models, sensor calibration, and dashboard modules are being developed incrementally.

Results shown during development should be considered experimental until sufficient calibration and validation data has been collected.

---

# Core Vision

<div align="center">

### SEE THE FRUIT.

### SENSE THE CHANGE.

### UNDERSTAND THE FRESHNESS.

<br/>

**FreshFusion**

*Turning fruit freshness into measurable intelligence.*

</div>

---

<div align="center">

### Built with AI × IoT × Computer Vision × Data Intelligence

<br/>

⭐ Star the repository if you find the project interesting.

</div>
