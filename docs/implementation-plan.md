# Implementation plan

## Goal

Improve faithful Omni Flash recreation when a short video depends on fast repeated motion. The workflow keeps semantic, audio, and kinematic evidence separate, then uses them together to produce and assess one English Omni prompt and, when approved, an Omni reference-image payload.

## Scope

1. Preserve the original `tiktok-to-omni-video` skill in `archive/original-skill/`.
2. Retain `watch` for storyline, composition, object census, and edit boundaries.
3. Add native-frame-rate motion analysis for rapid or cyclic actions.
4. Convert tracked-point trajectories to a machine-readable motion contract.
5. Render an Omni-only motion paragraph; it never emits Seedance tags or prompt-side reference syntax.
6. Re-run the motion contract against a generated clip to quantify cadence loss before a paid retry.
7. Cache an evidence-labelled impact contract, compile three stable batch variants, and rank output candidates before one-variable repair.

## Non-goals

- This repository does not upload source videos, publish source frames, or store API keys. It can send user-approved local storyboard/pose images to the configured Omni endpoint at request time.
- It does not promise pixel-identical replication from text-to-video.
- It does not invoke Seedance, V2V, R2V, or any prompt-side reference-tag workflow.

## Evidence contract

| Layer | Source of truth | Output |
|---|---|---|
| Semantics | `watch` frames plus local audio analysis | plot, shot, fixed inventory, comic mechanism |
| Kinematics | Native-rate tracked points | extension times, stroke rate, amplitude, velocity, alternation |
| Contact proxy | Native-rate points plus a verified target point | geometric contact candidates, force anchor, target response note |
| Prompt | Both layers | English Omni Flash brief with timing/stability locks and optional separate storyboard references |
| QA | Same analyses on generated video | ranked batch candidates and a single-variable repair target |

## Delivery checks

The test suite validates the CSV-to-motion-contract path. Runtime validation must also confirm the resulting Omni MP4 container, duration, and 720×1280 dimensions before it is reported as generated.
