# AI and Investigation Architecture

## Design goal

FreshFusion should not depend on one model or one confidence number. It uses multiple evidence-producing modules, a critic, deterministic gating/fusion, optional local LLM explanation, and human verification.

## Investigation modules

| Module | Role | Current technology |
| --- | --- | --- |
| Intake / Triage | Confirm usable fruit evidence and inspection context | Rules + CV evidence |
| Vision Analyst | Identity-supporting features, surface/color/defect evidence | OpenCV, optional ML path |
| Sensor Analyst | Temperature, humidity, MQ135 relative response, provenance and staleness | Deterministic rules |
| Reference Analyst | Compare current visual features with cached public reference classes | Handcrafted feature similarity |
| Multi-view Analyst | Check viewpoint diversity, identity consistency, screen/flat-image suspicion | OpenCV + physical validation |
| Evidence Critic | Detect missing/contradictory/invalid evidence | Deterministic critic rules |
| Explanation Agent | Explain evidence and next steps | Ollama + Gemma, optional |

The first six are software analysis modules; they are not independent LLM agents.

## Core flow

```text
Camera + ESP32 + Reference
          |
          v
   Evidence collection
          |
  +-------+--------+-----------+-----------+
  |                |           |           |
Vision          Sensor      Reference   Multi-view
  |                |           |           |
  +----------------+-----------+-----------+
                   |
                   v
          Freshness hypothesis
                   |
                   v
             Evidence critic
                   |
          +--------+---------+
          |                  |
     evidence valid     evidence blocked
          |                  |
          v                  v
 deterministic fusion   more evidence /
 and confidence         inconclusive
          |
          v
 optional Gemma explanation
          |
          v
 human verification
```

## Vision layer

Current vision evidence is primarily interpretable OpenCV-derived information such as fruit presence, color distribution, brown/dark surface, texture/roughness, edge/defect features, shape/identity support and display-artifact evidence.

A transfer-learning freshness classifier such as MobileNetV3-Small is a planned ML path. A model must not be described as deployed or validated unless an actual artifact is present, inference is demonstrated and held-out evaluation exists.

## Sensor layer

Inputs:

- temperature;
- humidity;
- MQ135 raw ADC;
- device/provenance metadata;
- timestamps.

`mq135_raw` is a relative electrical signal. Current prototype logic may normalize it to the ADC range for an experimental penalty, but this is not ppm, ethylene concentration or calibrated spoilage chemistry.

## Reference layer

The public reference system uses a compact local feature index. Its similarity result is supporting evidence only. It must not be presented as:

- probability;
- model confidence;
- validation accuracy;
- exact ground truth mapping.

Public class labels must remain distinct from FreshFusion `fresh / ripe / overripe / spoiled` human labels unless an explicit reviewed mapping is later defined.

## Multi-view physical evidence

The multi-view layer tries to reduce simple screen/photo spoofing by checking:

- multiple named viewpoints;
- changed fruit appearance/fingerprints;
- planar consistency;
- screen/display suspicion;
- identity consistency;
- fresh sensor evidence.

This remains probabilistic monocular verification. Production-grade liveness would need stronger sensing such as depth, stereo, NIR or controlled mechanical capture.

## Evidence critic

The critic should block or warn on conditions including:

- no fruit;
- insufficient physical viewpoints;
- stale/missing ESP32 data;
- simulator-only evidence;
- fruit identity conflict;
- screen/flat-reference suspicion;
- weak identity;
- reference unavailable;
- visual/sensor disagreement;
- unsupported model/validation claims.

Expected semantic outcomes include:

- `PASSED`
- `WARNING`
- `NEEDS MORE DATA`
- `BLOCKED`
- `INCONCLUSIVE`
- `WAITING FOR ESP32`
- `PHYSICAL FRUIT NOT VERIFIED`
- `CONFLICTING EVIDENCE`

## Fusion and confidence

Fusion is deterministic and experimental. It combines only eligible evidence after gating. Existing weights/thresholds are prototype rules and must be calibrated against real FreshFusion ground truth before any scientific accuracy claim.

The product must prefer an inconclusive/locked state over fabricating certainty.

## Ollama + Gemma

FreshFusion connects to local Ollama and defaults to a Gemma model through environment configuration. Gemma is explanation-oriented, not the final decision maker.

Allowed Gemma tasks:

- summarize current evidence;
- explain supporting evidence;
- describe contradictions;
- describe missing evidence;
- recommend the next capture step;
- later generate a human-readable inspection report.

Not allowed:

- invent sensor readings;
- fabricate ppm;
- generate validation accuracy;
- override deterministic gate/fusion;
- claim food safety certification.

If Ollama is offline, the core investigation must still work.

## Human-in-the-loop learning path

```text
System assessment
      |
      v
Human review
  |      |       |
Accept Incorrect Ground truth
                 |
                 v
      FreshFusion labelled data
                 |
                 v
       Sample-based evaluation
                 |
                 v
       Future model training
```

The human label becomes a separate audit record. It does not silently rewrite historical system output.

## Validation before model claims

Before saying the AI is accurate:

1. collect multiple physical fruits/batches;
2. define reviewed ground truth;
3. split by physical sample/batch rather than camera frame;
4. preserve a held-out test set;
5. record the exact model/configuration;
6. calculate per-class and per-fruit metrics;
7. repeat on new conditions/lighting;
8. report limitations and sample size.

Until then, UI and presentation should use `experimental`, `prototype`, `requires calibration`, and `NOT YET VALIDATED` where appropriate.