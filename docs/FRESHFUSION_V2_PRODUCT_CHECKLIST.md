# FreshFusion V2 Product Implementation Checklist

FreshFusion is moving from a sensor-heavy prediction dashboard to an evidence-driven fruit quality decision-support product.

The primary product rule is:

> Decision first. Evidence behind it. Every number must have a source, and every recommendation must be actionable.

## P0 — Product-critical changes

- [x] Add an operator-first decision view.
- [x] Keep technical numbers visible but visually secondary.
- [x] Add proactive assistant messages driven by backend evidence.
- [x] Use a 3-view workflow for the current product flow.
- [x] Add Tomato as a manually selectable inspection fruit.
- [x] Clearly separate internal quality from what the current sensing setup can measure.
- [x] Avoid pretending that remaining useful life is calibrated.
- [x] Add previous-vs-current condition comparison.
- [x] Add persistent condition-change events.
- [x] Add traceable evidence-score breakdown for the current deterministic score.
- [x] Add image-quality gating: blur, lighting, framing and duplicate-view checks.
- [x] Add multiple-fruit-like-region warning.
- [x] Add stronger 3-view evidence gating.
- [x] Add unsupported-fruit handling for product decision rules.
- [x] Separate visible damage from freshness state in recommendation logic.
- [x] Add sensor warm-up state.
- [x] Detect stale physical sensor evidence.
- [x] Add flat/stuck MQ135 signal warning.
- [x] Add long-term MQ135 baseline-drift warning against prior baseline sessions.
- [x] Add explicit empty-chamber baseline capture.
- [x] Add baseline-relative MQ135 raw delta.
- [x] Add recent MQ135 raw trend and rate-of-change reporting.
- [x] Add sensor evidence quality: Strong / Moderate / Weak.
- [x] Add configurable inspection stabilization-time protocol.
- [x] Add chamber purge/reset state to the inspection protocol.
- [x] Add fruit quantity / approximate weight metadata for gas-response interpretation.
- [x] Add batch ID, supplier and storage-location fields to the inspection profile.
- [x] Add product-facing inspection quality / protocol panel.
- [x] Keep previous QR, sensor graph, reference, image analysis, colour, texture and observation modules available.

### P0 scientific limitation still open

- [ ] Calibrate fruit-specific freshness / recommendation thresholds using collected Apple, Banana and Tomato ground truth. Current fruit-aware action rules are operational heuristics, not validated biological thresholds.

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
- [x] Show local MQ135 baseline delta beside the raw reading when available.
- [x] Show sensor evidence quality beside operator-facing evidence.
- [x] Add current score formula / contribution explanation.
- [ ] Add validated / calibrated remaining-useful-life estimation.
- [ ] Add recommendation justification with dataset-calibrated evidence references.
- [ ] Add action completion states: sold, processed, rejected, reinspected.
- [ ] Track business outcome after recommendation.
- [ ] Add batch-level recommendations.
- [ ] Add high-risk / priority-sale stock summary.
- [ ] Add waste-risk and stock-at-risk analytics.
- [ ] Add supplier and storage-location comparison.

## P1 — Proactive assistant

- [x] Assistant can generate guidance without waiting for a user question.
- [x] Assistant warns about blocked evidence, missing views and stale/missing sensor evidence.
- [x] Assistant clearly states that it does not independently decide freshness.
- [x] Assistant warns while the sensor warm-up gate is incomplete.
- [x] Assistant warns when an MQ135 signal appears stuck/flat.
- [x] Assistant asks for an empty-chamber baseline when none is available.
- [x] Assistant reacts to a rising / falling / stable MQ135 raw trend when a verdict is available.
- [x] Persist freshness-class-change events.
- [x] Persist sharp score-deterioration events.
- [x] Persist priority-sale / quick-sale / reject-zone events.
- [x] Add alert severity semantics: info, warning, critical.
- [x] Add alert cooldown / de-duplication.
- [x] Persist assistant events in the evidence timeline.
- [x] Show recent condition / alert events in the Live Inspection decision layer.
- [ ] Make the right-side conversational assistant directly prioritize the newest persisted alert before all local guidance rules.

## P1 — Reliability and edge cases

- [ ] Add repeatability check for repeated scans of the same physical fruit.
- [x] Add unsupported-fruit handling.
- [x] Add multiple-fruit detection / warning heuristic.
- [x] Separate visible damage from freshness state.
- [ ] Add mold-like visual warning without making a food-safety claim.
- [ ] Add preliminary vs confirmed assessment states.
- [ ] Add offline/local graceful-degradation behaviour.
- [ ] Add backup / recovery for database and labelled dataset.
- [ ] Add clearly labelled replay / recorded-demo fallback mode.

## P1 — Traceability

- [ ] Persist physical-fruit identity across repeated-day inspections.
- [x] Add batch ID, supplier and storage-location metadata.
- [ ] Add arrival-date metadata.
- [ ] Record which user added ground truth or manual override.
- [ ] Store model version.
- [ ] Store rule / scoring version.
- [ ] Store dataset version.
- [ ] Store sensor calibration version.
- [ ] Store recommendation-rule version.
- [ ] Add full audit trail for evidence, decisions, overrides and completed actions.

## P2 — Product UX

- [ ] Role-based UI: Operator / Manager / QA-Technical.
- [ ] Guided inspection workflow: place fruit, close chamber, capture views, wait for stabilization, complete inspection.
- [ ] Large operator controls and simplified mobile-friendly layout.
- [ ] Batch-mode inspection workflow.
- [ ] Report export to PDF / CSV.
- [ ] Multilingual UI for deployment use cases.

## P2 — Internal quality roadmap

The current sensing setup does **not** directly measure internal texture, firmness, internal browning, Brix or internal rot.

- [ ] Evaluate a low-cost firmness / compression sensor.
- [ ] Evaluate NIR spectroscopy for internal-quality estimation.
- [ ] Consider hyperspectral / advanced optical sensing only for later industrial versions.
- [x] Keep internal-quality status explicitly labelled as `Not measured` until validated hardware exists.

## Scientific boundaries

- MQ135 raw ADC is not ppm without calibration.
- There is no universal MQ135 number for a fresh Apple, Banana or Tomato.
- Empty-chamber baseline and MQ135 delta are local operational references, not universal standards.
- Historical baseline drift is an operational warning, not a laboratory calibration certificate.
- Reference similarity is not model accuracy or probability.
- Current fusion weights are not scientific constants.
- A 100-point score must not be presented as a validated freshness percentage unless calibrated and validated.
- Do not claim internal quality from the current camera + DHT11 + MQ135 sensing setup.
- Do not make food-safety claims.
- Do not show fabricated validation metrics.
- Fruit-specific remaining useful life must remain uncalibrated until supported by longitudinal data.

## Current product direction

Earlier:

`Reading -> Threshold -> Score -> Dashboard`

FreshFusion V2:

`Standardized Measurement -> Evidence -> Independent Analysis -> Evidence Critic -> Traceable Decision -> Condition Tracking -> Business Recommendation -> Proactive Assistant -> Human Verification -> Validation`
