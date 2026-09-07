# FreshFusion Master Engineering Checklist

This file exists so the project is not managed only by whatever feature someone remembers next. Use it as the cross-system checklist before internal selection and SIH demos.

## Status legend

- `[x]` foundation exists
- `[~]` partial / needs verification or completion
- `[ ]` not yet complete

## 1. Data acquisition

- [x] Phone camera upload path
- [x] Multi-view labels
- [x] ESP32 telemetry ingestion
- [x] DHT11 temperature/humidity
- [x] MQ135 raw ADC capture
- [~] Real phone background/reconnect validation
- [~] Real ESP32 reconnect/network validation
- [ ] Controlled capture protocol documented for all team demos
- [ ] Multi-device/chamber pairing model

## 2. Inspection/session control

- [x] Unique sample/inspection records
- [x] Explicit active capture target
- [x] Phone sample pairing
- [x] History browsing separated from active target
- [~] Stable fruit auto-routing physically verified
- [ ] Device-session persistence for multi-device scaling

## 3. Database and persistence

- [x] SQLAlchemy database layer
- [x] Fruit samples
- [x] Sensor readings
- [x] Fruit images + analysis JSON
- [x] Fusion history
- [x] Human verification
- [x] Active inspection control
- [ ] Alembic migration system
- [ ] Investigation run snapshots
- [ ] Persistent evidence-event table if reconstruction becomes insufficient
- [ ] Model/version provenance table
- [ ] Validation-run persistence
- [ ] Final backup/export procedure

## 4. Vision intelligence

- [x] Fruit-presence evidence
- [x] Apple/Banana identity-supporting logic
- [x] Color/brown/dark analysis
- [x] Texture/defect evidence
- [x] Screen/presentation artifact evidence
- [~] Lighting/background robustness
- [~] Real fruit identity validation
- [ ] Validated trained freshness model
- [ ] Model artifact/version tracking

## 5. Sensor intelligence

- [x] Required packet validation
- [x] Hardware vs simulator provenance
- [x] Stale sensor gating
- [x] Relative MQ135 ADC contribution
- [~] Baseline/chamber experiments
- [ ] Calibrated gas interpretation
- [ ] Fruit-specific sensor calibration study

## 6. Reference intelligence

- [x] Public dataset registry
- [x] Local compact reference index
- [x] Feature similarity matcher
- [x] Missing-reference warning state
- [~] Label mapping research
- [ ] Sample-based reference/validation study
- [ ] Optional future embedding retrieval (only if justified)

## 7. Multi-view / physical validation

- [x] View count
- [x] Appearance diversity
- [x] Identity consistency
- [x] Screen/flat-reference suspicion
- [x] Planar matching checks
- [x] Sensor recency requirement
- [~] Real physical fruit false-accept/false-reject testing
- [ ] Stronger production liveness/depth hardware

## 8. Investigation architecture

- [x] Evidence adapter
- [x] Vision Analyst
- [x] Sensor Analyst
- [x] Reference Analyst
- [x] Multi-view Analyst
- [x] Evidence Critic
- [x] Structured decision state
- [~] Evidence agreement visualization
- [ ] Persistent investigation run snapshots
- [ ] Final report generation

## 9. Fusion and confidence

- [x] Deterministic gating
- [x] Sensor + vision fusion path
- [x] Locked verdict when evidence is incomplete
- [x] Simulator exclusion from physical verdict
- [~] Current weights documented as experimental
- [ ] Calibrate thresholds/weights with real ground truth
- [ ] Independent held-out evaluation

## 10. Ollama + Gemma

- [x] Optional Ollama client
- [x] Gemma structured explanation contract
- [x] LLM separated from final deterministic verdict
- [x] Offline-safe core architecture
- [~] Verify on the actual demo laptop
- [~] Frontend explanation UX
- [ ] Report-generation use case if time permits

## 11. Human verification and ground truth

- [x] Accept action
- [x] Incorrect action
- [x] Ground-truth action
- [x] Append-only review record
- [x] Assessment snapshot
- [~] Reviewer workflow/UI polish
- [ ] Formal ground-truth protocol
- [ ] Enough real labelled physical samples for evaluation

## 12. Dataset and validation

- [x] Public dataset metadata
- [x] Local reference counts/state
- [x] Human label counts/state
- [x] Honest `NOT YET VALIDATED` behavior
- [ ] Sample-based immutable split manifest
- [ ] Ground-truth review process
- [ ] Validation run ingestion
- [ ] Confusion matrix from real test set
- [ ] Precision/recall/F1 from real test set
- [ ] Per-fruit/per-class error analysis
- [ ] Repeated condition/lighting test

## 13. Frontend/product workspace

- [x] Overview
- [x] Live Inspection
- [x] Investigation
- [x] Evidence
- [x] Dataset & Validation
- [x] History
- [x] Protected sample selection/state guards
- [x] WebSocket lifecycle guards
- [~] Evidence filtering/export
- [~] History search/pagination
- [~] Validation workflow completion
- [~] Human review UX
- [ ] Final professional UI consistency pass
- [ ] Accessibility/responsive polish

## 14. Error and degraded states

- [x] No fruit
- [x] Missing/stale sensor
- [x] Simulator evidence
- [x] Physical verification blocked
- [x] Missing reference index
- [x] Locked/inconclusive verdict
- [~] Ollama unavailable UX
- [~] Camera permission/network failure UX
- [~] Backend disconnected UX
- [ ] Demo recovery playbook

## 15. Realtime and performance

- [x] WebSocket updates
- [x] Stale-response guards
- [x] Socket disposal on sample change
- [~] Continuous capture stress test
- [ ] CPU-heavy OpenCV isolation/background task design if required
- [ ] Latency measurement on demo hardware

## 16. Security and deployment

- [x] Local prototype flow
- [x] Trusted HTTPS phone tunnel launcher
- [~] Environment/config documentation
- [ ] Authentication before public deployment
- [ ] Secure device pairing
- [ ] Rate limiting/upload abuse protection
- [ ] PostgreSQL deployment test
- [ ] Production reverse-proxy/deployment design

## 17. Testing

- [x] Backend regression suite
- [x] Frontend production build
- [x] Browser workflow tests
- [x] Virtual-camera regression path
- [~] Real phone tests
- [~] Real ESP32 tests
- [~] Real fruit spoof/negative tests
- [ ] Full final-demo checklist pass
- [ ] Database migration/backup recovery test

## 18. Documentation

- [x] Root README
- [x] Investigation foundation
- [x] Implementation report
- [x] Local network guide
- [x] Physical validation guide
- [x] Backend architecture
- [x] Frontend architecture
- [x] UI architecture
- [x] Database architecture
- [x] AI architecture
- [x] Hardware architecture
- [x] Testing strategy
- [x] Team workflow
- [ ] Final demo runbook
- [ ] Final API reference if contracts expand

## 19. Internal-round PPT and presentation

- [ ] New internal-round PPT based on current architecture
- [ ] Problem/gap evidence
- [ ] Architecture diagram
- [ ] Innovation comparison
- [ ] Real prototype images
- [ ] Honest validation slide
- [ ] Demo sequence
- [ ] Sajiya narrative practice
- [ ] Tarun technical demo practice
- [ ] Soha/Prerna Q&A preparation

## 20. Final definition of done for the current SIH prototype

The project is ready for a serious demo when:

```text
Real fruit
  -> correct inspection
  -> multiple physical camera views
  -> fresh physical ESP32 telemetry
  -> analysts populated
  -> critic explains evidence quality
  -> deterministic gate releases or blocks responsibly
  -> Gemma can explain but is not required
  -> human can verify/correct
  -> evidence persists in history
  -> validation state is truthful
  -> team can recover from a service failure
  -> presentation claims match what was actually tested
```

Update this checklist as the system evolves. Do not mark scientific validation complete based only on software tests or synthetic fixtures.