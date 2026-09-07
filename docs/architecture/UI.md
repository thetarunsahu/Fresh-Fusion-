# UI Architecture and Design Rules

## Goal

FreshFusion should look like a professional inspection/investigation product, not a gaming dashboard and not a collection of unrelated cards. The UI must make evidence quality, uncertainty, blocked states and human review understandable within seconds.

## Primary navigation

```text
Overview
Live Inspection
Investigation
Evidence
Dataset & Validation
History
```

## Core screen hierarchy

### 1. Context header

Always show:

- active/selected inspection ID;
- fruit type;
- inspection status;
- active capture target vs historical selection;
- hardware/backend connection state.

### 2. Evidence area

Show current camera evidence, sensor freshness, view coverage and reference state before showing a final result.

### 3. Analyst area

Use consistent analyst cards:

```text
Analyst name
Status
Primary finding
Supporting measurements
Warning / limitation
```

### 4. Critic area

The critic should be visually different from ordinary analyst cards. It must explicitly surface:

- supporting evidence;
- missing evidence;
- contradictions;
- warnings;
- next recommended evidence.

### 5. Decision area

Only show a final freshness label/score when the deterministic gate says it is ready. Otherwise show one of the semantic states such as:

- MORE EVIDENCE REQUIRED
- WAITING FOR ESP32
- PHYSICAL FRUIT NOT VERIFIED
- CONFLICTING EVIDENCE
- INCONCLUSIVE

Never replace a missing score with a visually meaningful `50%` or similar placeholder.

### 6. Human review area

Actions:

- Accept system assessment
- Mark incorrect
- Add ground truth

Ground truth is separate from public dataset labels and system predictions.

## Status semantics

Use status language consistently across pages.

| State | Meaning |
| --- | --- |
| Ready | Evidence/module is currently usable |
| Waiting | Required evidence/service has not arrived |
| Warning | Usable but needs review |
| Blocked | A contradiction or gate prevents final assessment |
| Inconclusive | System intentionally declines to force a verdict |
| Not validated | No trustworthy evaluation result exists yet |

## Design principles

1. Evidence before verdict.
2. No fake metrics.
3. Clear provenance: camera, ESP32, simulator, public reference, human label.
4. Separate system prediction from human ground truth.
5. Use typography and spacing for hierarchy rather than excessive neon effects.
6. Charts only when they answer a real question.
7. Use real fruit images/evidence rather than decorative 3D objects.
8. Show degraded/offline states explicitly.
9. Keep technical details expandable rather than permanently crowding the main view.
10. Mobile capture UI and desktop investigation UI have different jobs and should not be forced into one layout.

## Recommended Investigation page layout

```text
+-------------------------------------------------------------+
| Inspection context | status | active target | connections   |
+-----------------------------+-------------------------------+
| Current fruit evidence      | Vision Analyst                |
| Image / views / capture     +-------------------------------+
|                             | Sensor Analyst                |
|                             +-------------------------------+
|                             | Reference Analyst             |
|                             +-------------------------------+
|                             | Multi-view Analyst            |
+-----------------------------+-------------------------------+
| Evidence Critic                                             |
| support | missing | contradictions | warnings | next step   |
+-------------------------------------------------------------+
| Assessment / locked state                                  |
+-------------------------------------------------------------+
| Gemma explanation (optional)                               |
+-------------------------------------------------------------+
| Human verification                                         |
+-------------------------------------------------------------+
```

## Evidence Agreement Matrix

A useful future UI element is an evidence agreement matrix:

| Evidence source | Finding | Strength | Agreement |
| --- | --- | --- | --- |
| Vision | Overripe tendency | Experimental | Supports |
| Sensor | Elevated relative gas response | Experimental | Supports |
| Reference | Closest normal/rotten class | Similarity only | Partial conflict |
| Multi-view | Physical fruit likely | Gate evidence | Supports |

This is a visualization layer only; it must not invent new confidence numbers.

## Final UI phase

Do not spend the entire development window polishing appearance while backend contracts are changing. The preferred order is:

```text
Working data flow
-> stable investigation contract
-> all pages functional
-> real validation/hardware states
-> final UI redesign and consistency pass
```

If a teammate can genuinely own React/CSS design, UI polish can be delegated after core functionality stabilizes. Otherwise the core owner should perform the final integration pass.