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
- [x] Add conservative Tomato visual compatibility support without claiming a trained Tomato classifier.
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
- [x] Add physical-fruit specimen ID for repeated-inspection tracking and leakage-safe validation splits.
- [x] Add product-facing inspection quality / protocol panel.
- [x] Add decision provenance: rule, recommendation, dataset, calibration, split and model-artifact identifiers.
- [x] Keep previous QR, sensor graph, reference, image analysis, colour, texture and observation modules available.

### P0 scientific limitation still open

- [ ] Calibrate fruit-specific freshness / recommendation thresholds using collected Apple, Banana and Tomato ground truth. Software now derives empirical distributions from real labelled chamber data, but does not invent or auto-activate thresholds before enough data exists.

## P0 — Real dataset and validation

- [ ] Build a controlled Apple dataset using real fruit observations.
- [ ] Build a controlled Banana dataset using real fruit observations.
- [ ] Build a controlled Tomato dataset using real fruit observations.
- [ ] Record multiple physical fruits per freshness stage.
- [ ] Record Fresh / Ripe / Overripe / Spoiled ground truth independently from predictions.
- [x] Software stores multi-view images, sensor data, baseline, delta and timestamps per inspection.
- [ ] Finalize freshness-stage labelling protocol to reduce subjective ground truth.
- [x] Add deterministic sample/specimen-level train/validation/test split manifest.
- [x] Prevent declared repeated observations of the same physical fruit from leaking across splits via fruit specimen ID.
- [x] Compute confusion matrix, accuracy, precision, recall and F1 only from matched human-ground-truth + verified-prediction pairs.
- [x] Keep UI state as `NOT YET VALIDATED` when no real evaluation pairs exist.
- [x] Mark sparse metrics as preliminary instead of validated accuracy claims.
- [x] Add fruit-wise evaluation summaries.
- [x] Add data-derived Apple/Banana/Tomato calibration-readiness summaries.
- [x] Derive observed MQ135 baseline-delta and visual distributions from FreshFusion-labelled chamber data instead of inventing universal thresholds.
- [ ] Collect enough real labelled observations for those distributions to become calibration-ready.

## P1 — Business decision layer

- [x] Show simple quality status.
- [x] Show action recommendation separately from freshness status.
- [x] Show risk level.
- [x] Show a clear reason for the recommendation.
- [x] Keep raw measurements as small supporting evidence.
- [x] Show local MQ135 baseline delta beside the raw reading when available.
- [x] Show sensor evidence quality beside operator-facing evidence.
- [x] Add current score formula / contribution explanation.
- [ ] Add validated / calibrated remaining-useful-life estimation; requires longitudinal real data.
- [ ] Replace operational recommendation heuristics with dataset-calibrated evidence references after enough data exists.
- [ ] Add action completion states: sold, processed, rejected, reinspected.
- [ ] Track business outcome after recommendation.
- [ ] Add batch-level recommendations.
- [ ] Add high-risk / priority-sale stock summary.
- [ ] Add waste-risk and stock-at-risk analytics.
- [ ] Add supplier and storage-location comparison.

## P1 — Proactive & interactive assistant

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
- [x] Add an interactive inspection assistant question box.
- [x] Connect local Ollama/Gemma to evidence-grounded operator Q&A.
- [x] Add deterministic Q&A fallback when Ollama is unavailable.
- [x] Include previous verified condition context, current critic state, product recommendation and human verifications in assistant evidence.
- [x] Persist assistant questions/answers as inspection events.
- [ ] Consolidate the older proactive side panel and the new interactive assistant console into one final visual component after UI verification.

## P1 — Reliability and edge cases

- [ ] Add repeatability statistics for repeated scans of the same physical fruit; specimen IDs now provide the required linkage.
- [x] Add unsupported-fruit handling.
- [x] Add multiple-fruit detection / warning heuristic.
- [x] Separate visible damage from freshness state.
- [ ] Add mold-like visual warning without making a food-safety claim.
- [ ] Add explicit preliminary vs confirmed assessment wording across every screen.
- [ ] Add offline/local graceful-degradation behaviour.
- [ ] Add backup / recovery for database and labelled dataset.
- [ ] Add clearly labelled replay / recorded-demo fallback mode.

## P1 — Human verification & traceability

- [x] Store human Accept / Incorrect / Ground Truth observations separately from the system assessment.
- [x] Add explicit manual override with required label and reason.
- [x] Store reviewer text and verification timestamp.
- [x] Persist verification/override audit events with the original system label and score snapshot.
- [x] Persist physical-fruit specimen identity across repeated inspections when the operator reuses the specimen ID.
- [x] Add batch ID, supplier and storage-location metadata.
- [ ] Add arrival-date metadata.
- [x] Expose rule / recommendation / dataset / calibration / split version provenance in the investigation product state.
- [x] Compute model artifact SHA-256 provenance when a model artifact exists.
- [ ] Replace text reviewer identity with authenticated user identity everywhere once auth integration is reconciled on the active branch.
- [ ] Add action-completion audit events for sold / processed / rejected / reinspected.

## P2 — Product UX / operations

- [ ] Role-based final UI: Operator / Manager / QA-Technical.
- [ ] Guided inspection workflow: place fruit, close chamber, capture views, wait for stabilization, complete inspection.
- [ ] Large operator controls and simplified mobile-friendly layout.
- [ ] Batch-mode inspection workflow.
- [ ] Report export to PDF / CSV.
- [ ] Multilingual UI for deployment use cases.
- [ ] Formal DB migrations instead of relying only on additive create-all behaviour.
- [ ] Database + labelled-dataset backup / restore workflow.
- [ ] Recorded-demo / replay fallback for network or camera failure.

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
- Tomato visual compatibility is a conservative heuristic, not a trained Tomato classifier.
- Do not claim internal quality from the current camera + DHT11 + MQ135 sensing setup.
- Do not make food-safety claims.
- Do not show fabricated validation metrics.
- Fruit-specific remaining useful life must remain uncalibrated until supported by longitudinal data.

## Current product direction

Earlier:

`Reading -> Threshold -> Score -> Dashboard`

FreshFusion V2:

`Standardized Measurement -> Evidence -> Independent Analysis -> Evidence Critic -> Traceable Decision -> Condition Tracking -> Business Recommendation -> Proactive + Interactive Assistant -> Human Verification -> Ground Truth -> Validation / Calibration`
