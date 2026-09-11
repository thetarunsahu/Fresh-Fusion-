# FreshFusion V2 Product Implementation Checklist

FreshFusion is moving from a sensor-heavy prediction dashboard to an evidence-driven fruit quality decision-support product.

The primary product rule is:

> Decision first. Evidence behind it. Every number must have a source, and every recommendation must be actionable.

## P0 — SIH-critical product changes

- [x] Add an operator-first decision view.
- [x] Keep technical numbers visible but visually secondary.
- [x] Add proactive assistant messages driven by backend evidence.
- [x] Use a 3-view workflow for the current prototype.
- [x] Add Tomato as a manually selectable inspection fruit.
- [x] Clearly separate internal quality from what the current prototype can measure.
- [x] Avoid pretending that remaining useful life is calibrated.
- [ ] Add previous-vs-current condition comparison.
- [ ] Add persistent condition-change events.
- [ ] Add fruit-specific recommendation rules backed by collected data.
- [ ] Add evidence-score breakdown so every point in the 100-point score is traceable.
- [ ] Add image-quality gating: blur, lighting, framing and duplicate-view checks.
- [ ] Add stronger sensor-health state: warm-up, stale reading, flat/stuck signal and drift warning.
- [ ] Add empty-chamber baseline capture and baseline-relative MQ135 delta.
- [ ] Add fixed inspection-time protocol in software.
- [ ] Add chamber purge/reset workflow between samples.
- [ ] Add fruit quantity / approximate weight metadata for gas-response interpretation.

## P0 — Real dataset and validation

- [ ] Build a controlled Apple dataset.
- [ ] Build a controlled Banana dataset.
- [ ] Build a controlled Tomato dataset.
- [ ] Record multiple physical fruits per freshness stage.
- [ ] Record Fresh / Ripe / Overripe / Spoiled ground truth independently from predictions.
- [ ] Store multi-view images, sensor data, baseline, delta and timestamps per sample.
- [ ] Define freshness-stage labelling rules to reduce subjective ground truth.
- [ ] Use immutable sample-level train/validation/test splits.
- [ ] Prevent multiple views of the same physical fruit leaking across splits.
- [ ] Add confusion matrix, precision, recall and F1 only after real validation.
- [ ] Keep UI state as `NOT YET VALIDATED` until metrics exist.
- [ ] Derive fruit-specific MQ135 distributions from controlled measurements instead of inventing universal thresholds.

## P1 — Business decision layer

- [x] Show simple quality status.
- [x] Show action recommendation separately from freshness status.
- [x] Show risk level.
- [x] Show a clear reason for the recommendation.
- [x] Keep raw measurements as small supporting evidence.
- [ ] Add validated / calibrated remaining-useful-life estimation.
- [ ] Add recommendation justification with explicit evidence references.
- [ ] Add action completion states: sold, processed, rejected, reinspected.
- [ ] Track business outcome after recommendation.
- [ ] Add batch-level recommendations.
- [ ] Add high-risk / priority-sale stock summary.
- [ ] Add waste-risk and stock-at-risk analytics.
- [ ] Add supplier and storage-location comparison.

## P1 — Proactive assistant

- [x] Assistant can generate guidance without waiting for a user question.
- [x] Assistant warns about blocked evidence, missing views and stale sensor evidence.
- [x] Assistant clearly states that it does not independently decide freshness.
- [ ] Trigger assistant messages on freshness-class change.
- [ ] Trigger assistant messages on sharp score deterioration.
- [ ] Trigger assistant messages on gas-trend increase.
- [ ] Trigger assistant messages when fruit enters priority-sale / reject zones.
- [ ] Add alert severity: info, warning, critical.
- [ ] Add alert cooldown / de-duplication.
- [ ] Persist assistant events in the evidence timeline.
- [ ] Add current-inspection and previous-inspection context to assistant explanations.

## P1 — Reliability and edge cases

- [ ] Add repeatability check for repeated scans of the same fruit.
- [ ] Add unsupported-fruit handling.
- [ ] Add multiple-fruit detection / warning.
- [ ] Separate visible damage from freshness state.
- [ ] Add mold-like visual warning without making a food-safety claim.
- [ ] Add preliminary vs confirmed assessment states.
- [ ] Add offline/local graceful-degradation behaviour.
- [ ] Add backup / recovery for database and labelled dataset.
- [ ] Add clearly labelled replay / recorded-demo fallback mode.

## P1 — Traceability

- [ ] Persist sample identity across repeated inspections.
- [ ] Add batch ID, supplier, arrival date and storage-location metadata.
- [ ] Record which user added ground truth or manual override.
- [ ] Store model version.
- [ ] Store rule / scoring version.
- [ ] Store dataset version.
- [ ] Store sensor calibration version.
- [ ] Store recommendation-rule version.
- [ ] Add full audit trail for evidence, decisions, overrides and actions.

## P2 — Product UX

- [ ] Role-based UI: Operator / Manager / QA-Technical.
- [ ] Guided inspection workflow: place fruit, close chamber, capture views, wait for stabilization, complete inspection.
- [ ] Large operator controls and simplified mobile-friendly layout.
- [ ] Batch-mode inspection workflow.
- [ ] Report export to PDF / CSV.
- [ ] Multilingual UI for deployment use cases.

## P2 — Internal quality roadmap

The current prototype does **not** directly measure internal texture, firmness, internal browning, Brix or internal rot.

- [ ] Evaluate a low-cost firmness / compression sensor.
- [ ] Evaluate NIR spectroscopy for internal-quality estimation.
- [ ] Consider hyperspectral / advanced optical sensing only for later industrial versions.
- [ ] Keep internal-quality status explicitly labelled as `Not measured` until validated hardware exists.

## Scientific boundaries

- MQ135 raw ADC is not ppm without calibration.
- There is no universal MQ135 number for a fresh Apple, Banana or Tomato.
- Reference similarity is not model accuracy or probability.
- Experimental fusion weights are not scientific constants.
- A 100-point score must not be presented as a validated freshness percentage unless calibrated and validated.
- Do not claim internal quality from the current camera + DHT11 + MQ135 prototype.
- Do not make food-safety claims.
- Do not show fabricated validation metrics.
- Fruit-specific remaining useful life must remain uncalibrated until supported by longitudinal data.

## Current product direction

Earlier:

`Reading -> Threshold -> Score -> Dashboard`

FreshFusion V2:

`Standardized Measurement -> Evidence -> Independent Analysis -> Evidence Critic -> Traceable Decision -> Condition Tracking -> Business Recommendation -> Proactive Assistant -> Human Verification -> Validation`
