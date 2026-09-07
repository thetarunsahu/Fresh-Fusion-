# Team Workflow and Ownership

## Working model

FreshFusion should be developed in parallel without allowing every contributor to edit the same core files. Ownership is divided by subsystem and each teammate should deliver a complete feature slice rather than a one-prompt mockup.

## Current ownership

| Person | Primary ownership |
| --- | --- |
| Tarun | Core backend, AI/investigation architecture, camera/ESP32 integration, fusion, database architecture, Ollama/Gemma, final merge/review |
| Soham | Inspection evidence system: evidence timeline, history, filtering, detailed inspection workflow, export/report path |
| Nayan | Dataset and validation system: ground-truth workflow, validation records, metrics/report ingestion, dataset review |
| Soha | Internal-round PPT structure, story, flow, feasibility/implementation content |
| Prerna | PPT research/evidence: datasets, validation method, comparisons, cost/use cases/references |
| Sajiya | Main presenter, system understanding, problem/solution/innovation narrative and presentation coordination |

Final UI polish should be assigned only to someone who can genuinely own React/CSS design. Otherwise it remains with the core integration owner after functionality stabilizes.

## Tarun protected core

Coordinate before editing:

```text
backend/app/services/image_analysis.py
backend/app/services/sensor_assessment.py
backend/app/services/physical_validation.py
backend/app/services/fusion.py
backend/app/services/inspection_control.py
backend/app/services/investigation_core/
backend/app/services/ollama_client.py
backend/app/api/images.py
backend/app/api/sensors.py
frontend/src/components/CameraStream.jsx
frontend/src/hooks/useInspection.js
esp32/
```

Teammates can request contract changes, but should not independently rewrite these modules.

## Soham task: Inspection and Evidence Platform

This is not a mock-card task. The feature should work against real FreshFusion APIs.

Expected deliverables:

- evidence timeline;
- evidence type filters;
- image preview/detail where safe;
- inspection history search/filter;
- detailed inspection reopen;
- review/status badges;
- loading/error/empty states;
- export/report foundation;
- isolated frontend API/service helpers;
- tests for the implemented workflow.

Acceptance criterion:

> With the real backend running, Soham's feature should display existing inspections and evidence without permanent mock data.

Suggested branch:

```text
feature/inspection-evidence
```

## Nayan task: Dataset and Validation Platform

This feature must distinguish dataset metadata, human ground truth and actual evaluation results.

Expected deliverables:

- public dataset source/license view;
- FreshFusion labelled-data review;
- ground-truth workflow integration;
- sample-based train/validation/test manifest design;
- prediction-vs-ground-truth table;
- validation run history;
- confusion matrix display;
- precision/recall/F1 ingestion when real reports exist;
- per-fruit/per-class results;
- `NOT YET VALIDATED` state when metrics do not exist;
- tests for the implemented workflow.

Acceptance criterion:

> No fabricated accuracy numbers and no frame-randomized leakage presented as independent validation.

Suggested branch:

```text
feature/dataset-validation
```

## Soha + Prerna task: New internal-round PPT

The old deck should not simply be patched. The internal-round deck should reflect the current FreshFusion architecture.

### Soha owns

- problem -> gap -> solution storyline;
- system workflow;
- architecture sequencing;
- feasibility/implementation roadmap;
- slide consistency and density.

### Prerna owns

- dataset/research evidence;
- existing-solution comparison;
- sensor justification;
- validation methodology;
- cost/use cases/impact evidence;
- references.

Tarun verifies technical slides before finalization.

## Sajiya presentation loop

Sajiya should not receive the system explanation only on presentation day. After each major integration, update her on:

- what changed;
- why it matters;
- how to explain it simply;
- what claims are not allowed.

She should clearly understand that:

- MQ135 raw is not calibrated ppm;
- Gemma does not decide the final verdict;
- reference similarity is not accuracy;
- physical verification is probabilistic;
- validation metrics cannot be claimed until measured.

## Presentation handoff

Preferred longer-format flow:

```text
Sajiya
Problem -> gap -> solution -> innovation overview

Tarun
Prototype -> hardware -> architecture -> analysts -> critic -> fusion -> Gemma -> live demo

Soha
Workflow -> feasibility -> implementation/scalability

Prerna
Dataset -> validation method -> research -> impact/references -> close
```

For a short 6-7 minute slot, use Sajiya + Tarun as the main presenters and let Soha/Prerna strengthen Q&A.

## Git rules

1. Teammates work on feature branches.
2. Do not force-push shared branches.
3. Do not push directly to `main` for teammate feature work.
4. Pull/rebase or merge latest `main` before final handoff.
5. Keep one feature per branch where possible.
6. Commit messages should describe the completed slice, not `update files`.
7. Tarun reviews integration conflicts and protected-core changes.
8. Run relevant tests/build before requesting merge.

## Definition of a real teammate task

A task is not complete because an AI coding tool generated a page. A contributor should be able to explain:

- what data contract the feature uses;
- where the data comes from;
- what happens when it is missing;
- what files they changed;
- how they tested it;
- what remains incomplete;
- why their implementation does not break the core pipeline.

That is the expected standard for vibe-coding-assisted work in this project.