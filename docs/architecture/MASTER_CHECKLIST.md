# FreshFusion Master Engineering Checklist

This file exists so the project is not managed only by whatever feature someone remembers next. Use it as the cross-system checklist before internal selection and SIH demos.

## Status legend

- `[x]` foundation exists
- `[~]` partial / needs physical verification, data or completion
- `[ ]` not yet complete

## 1. Data acquisition

- [x] Phone camera upload path
- [x] Multi-view labels
- [x] ESP32 telemetry ingestion
- [x] DHT11 temperature/humidity
- [x] MQ135 raw ADC capture
- [~] Real phone background/reconnect validation
- [~] Real ESP32 reconnect/network validation
- [x] Controlled capture/real-world validation protocol documented
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
- [x] Alembic migration system
- [x] Investigation run snapshots
- [ ] Persistent evidence-event table if reconstruction becomes insufficient
- [x] Model/version provenance table foundation
- [x] Validation-run persistence
- [x] Local database/evidence backup script
- [~] Migration + backup recovery test on the real demo database copy

## 4. Vision intelligence

- [x] Fruit-presence evidence
- [x] Apple/Banana identity-supporting logic
- [x] Color/brown/dark analysis
- [x] Texture/defect evidence
- [x] Screen/presentation artifact evidence
- [~] Lighting/background robustness
- [~] Real fruit identity validation
- [ ] Validated trained freshness model
- [~] Model artifact/version tracking workflow (table exists; no validated model yet)

## 5. Sensor intelligence

- [x] Required packet validation
- [x] Hardware vs simulator provenance
- [x] Stale sensor gating
- [x] Relative MQ135 ADC contribution
- [x] MQ135 relative-response experiment protocol documented
- [~] Baseline/chamber experiments physically performed
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
- [x] Evidence Agreement contract + visualization
- [x] Persistent investigation run snapshots
- [~] Final report generation (structured snapshot + Gemma explanation exist; PDF/report export still optional)

## 9. Fusion and confidence

- [x] Deterministic gating
- [x] Sensor + vision fusion path
- [x] Locked verdict when evidence is incomplete
- [x] Simulator exclusion from physical verdict
- [x] Current weights documented as experimental
- [ ] Calibrate thresholds/weights with real ground truth
- [ ] Independent held-out evaluation

## 10. Ollama + Gemma

- [x] Optional Ollama client
- [x] Gemma structured explanation contract
- [x] LLM separated from final deterministic verdict
- [x] Offline-safe core architecture
- [x] Ollama + `gemma3:4b` verified on Tarun's laptop through the local API
- [x] Frontend explanation UX implemented
- [~] End-to-end explanation click verified inside the final FreshFusion branch/build
- [~] Report-generation use case if time permits

## 11. Human verification and ground truth

- [x] Accept action
- [x] Incorrect action
- [x] Ground-truth action
- [x] Append-only review record
- [x] Assessment snapshot
- [~] Reviewer workflow/UI polish
- [x] Ground-truth/real-world validation protocol documented
- [ ] Enough real labelled physical samples for evaluation

## 12. Dataset and validation

- [x] Public dataset metadata
- [x] Local reference counts/state
- [x] Human label counts/state
- [x] Honest `NOT YET VALIDATED` behavior
- [x] Real observational validation-metrics engine from human review snapshots
- [x] Validation-run persistence
- [x] Confusion-matrix UI when comparable real labels exist
- [x] Accuracy / macro precision / macro recall / macro F1 computation when real comparable labels exist
- [x] Per-class precision/recall/F1/support computation
- [ ] Sample-based immutable train/validation/test split manifest
- [ ] Enough real ground-truth inspections to populate trustworthy metrics
- [ ] Independent held-out test set
- [ ] Repeated condition/lighting study

## 13. Frontend/product workspace

- [x] Overview
- [x] Live Inspection
- [x] Investigation
- [x] Evidence
- [x] Dataset & Validation
- [x] History
- [x] Protected sample selection/state guards
- [x] WebSocket lifecycle guards
- [x] Evidence Agreement UI
- [x] Gemma explanation UI
- [x] Validation metrics/confusion-matrix UI
- [~] Evidence filtering/export
- [~] History search/pagination
- [~] Human review UX
- [~] Final professional UI consistency pass
- [~] Accessibility/responsive polish

## 14. Error and degraded states

- [x] No fruit
- [x] Missing/stale sensor
- [x] Simulator evidence
- [x] Physical verification blocked
- [x] Missing reference index
- [x] Locked/inconclusive verdict
- [x] Ollama unavailable UX foundation
- [~] Camera permission/network failure UX physical verification
- [~] Backend disconnected UX
- [x] Launcher local-only recovery mode
- [x] Demo recovery playbook

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
- [x] Local-only degraded launcher mode
- [~] Environment/config documentation
- [ ] Authentication before public deployment
- [ ] Secure device pairing
- [ ] Rate limiting/upload abuse protection
- [ ] PostgreSQL deployment test
- [ ] Production reverse-proxy/deployment design

## 17. Testing

- [x] Backend regression suite foundation
- [x] Validation/agreement unit regression tests added
- [x] Frontend production build path
- [x] Browser workflow tests
- [x] Virtual-camera regression path
- [~] Run all automated tests against this final hardening branch on Tarun's laptop
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
- [x] Real-world validation protocol
- [x] MQ135 experiment protocol
- [x] Final demo/recovery runbook
- [~] Final API reference if contracts expand further

## 19. Internal-round PPT and presentation

- [~] New six-slide internal-round PPT being rebuilt around current architecture
- [~] Problem/gap evidence
- [~] Architecture diagram
- [~] Innovation comparison
- [ ] Real final prototype screenshots/images
- [x] Honest validation wording defined
- [x] Demo sequence documented
- [ ] Sajiya narrative practice
- [ ] Tarun technical demo practice
- [ ] Soha/Prerna Q&A preparation

## 20. Final definition of done for the current SIH prototype

The software foundation is ready for final physical verification when:

```text
real fruit
  -> correct inspection
  -> multiple physical camera views
  -> fresh physical ESP32 telemetry
  -> analysts populated
  -> evidence agreement is visible
  -> critic explains evidence quality
  -> deterministic gate releases or blocks responsibly
  -> Gemma can explain but is not required
  -> human can verify/correct
  -> investigation snapshot persists
  -> evidence persists in history
  -> validation state/metrics are truthful
  -> database can be migrated/backed up safely
  -> team can recover from tunnel/Ollama/ESP32 failure
  -> presentation claims match what was actually tested
```

Do not mark scientific validation complete based only on software tests, synthetic fixtures or small observational datasets.
