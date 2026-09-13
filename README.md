## System Architecture

FreshFusion is designed as an **evidence-first multimodal inspection system**.  
Instead of relying on one black-box prediction, it separates evidence collection, independent analysis, trust validation, decision-making, and explanation.

```mermaid
flowchart TB

    subgraph INPUT["1. Evidence Collection"]
        A1["Smartphone Camera"]
        A2["ESP32 Sensor Node"]
        A3["DHT11<br/>Temperature + Humidity"]
        A4["MQ135<br/>Relative Gas Response"]
    end

    subgraph ANALYSIS["2. Independent Analysis"]
        B1["Fruit Identity"]
        B2["Surface Damage Analysis"]
        B3["Color + Texture Analysis"]
        B4["Multi-View Analysis"]
        B5["Sensor Analysis"]
    end

    subgraph TRUST["3. Evidence Validation"]
        C1["Image Quality Check"]
        C2["Sensor Health Check"]
        C3["Evidence Critic"]
    end

    subgraph DECISION["4. Decision Layer"]
        D1{"Evidence Sufficient?"}
        D2["Deterministic Fusion"]
        D3["Request More Evidence"]
    end

    subgraph OUTPUT["5. Explain + Verify"]
        E1["Quality Assessment"]
        E2["FreshFusion Assistant"]
        E3["Gemma / Ollama Explanation"]
        E4["Human Verification"]
    end

    A1 --> B1
    A1 --> B2
    A1 --> B3
    A1 --> B4

    A2 --> B5
    A3 --> B5
    A4 --> B5

    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1
    B5 --> C2

    C1 --> C3
    C2 --> C3

    C3 --> D1

    D1 -->|Yes| D2
    D1 -->|No| D3

    D3 --> A1
    D3 --> A2

    D2 --> E1
    E1 --> E2
    E1 --> E3
    E2 --> E4
    E3 --> E4
```

### How FreshFusion Thinks

```text
Physical Fruit
      ↓
Camera + Sensor Evidence
      ↓
Independent Analysis
      ↓
Evidence Validation
      ↓
Evidence Critic
      ↓
Deterministic Decision
      ↓
AI Explanation
      ↓
Human Verification
```

The important difference is that FreshFusion can **hold a result instead of forcing one** when camera, sensor, or multi-view evidence is incomplete or inconsistent.

---

## Inspection Workflow

A single smartphone camera is enough for fruit identification.  
Multiple physical cameras are **not required**.

```mermaid
flowchart LR

    A["Start Inspection"] --> B["Place Fruit"]
    B --> C["Initial Fruit Identity"]

    C --> D{"Identity Correct?"}

    D -->|Yes| E["Continue"]
    D -->|No| F["Operator Confirmation"]

    F --> E

    E --> G["Capture Front View"]
    G --> H["Capture Left View"]
    H --> I["Capture Right View"]

    I --> J["Collect ESP32 Evidence"]
    J --> K["Validate Evidence"]

    K --> L{"Enough Evidence?"}

    L -->|No| M["Request Missing Evidence"]
    M --> G

    L -->|Yes| N["Quality Assessment"]

    N --> O["Explain Result"]
    O --> P["Human Verification"]
```

### Why Multiple Views?

Multiple views improve:

- Surface coverage
- Damage visibility
- Confidence
- Physical-fruit verification
- Resistance to single-angle errors

A single clear frame can provide an **initial identity**, while additional views strengthen the final assessment.

---

## Evidence Flow

```mermaid
flowchart LR

    A["Camera"] --> B["Vision Evidence"]
    C["DHT11"] --> D["Environmental Evidence"]
    E["MQ135"] --> F["Relative Gas Evidence"]

    B --> G["Evidence Critic"]
    D --> G
    F --> G

    G --> H["Deterministic Fusion"]

    H --> I["Provisional / Final Score"]
    I --> J["FreshFusion Assistant"]
    I --> K["Human Verification"]
```

FreshFusion does not allow the LLM to directly decide freshness.

```text
Evidence
   ↓
Deterministic Logic
   ↓
Assessment
   ↓
Gemma / Ollama
   ↓
Explanation Only
```

This keeps the core decision path independent from the language model.
