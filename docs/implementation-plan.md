# Implementation plan

## Goal

Improve faithful Omni Flash T2V recreation when a short video depends on fast repeated motion. The workflow keeps semantic, audio, and kinematic evidence separate, then uses them together to produce and assess one English Omni prompt.

## Scope

1. Preserve the original `tiktok-to-omni-video` skill in `archive/original-skill/`.
2. Retain `watch` for storyline, composition, object census, and edit boundaries.
3. Add native-frame-rate motion analysis for rapid or cyclic actions.
4. Convert tracked-point trajectories to a machine-readable motion contract.
5. Render an Omni-only motion paragraph; it never emits Seedance tags or reference-upload syntax.
6. Re-run the motion contract against a generated clip to quantify cadence loss before a paid retry.

## Non-goals

- This repository does not upload source videos, publish source frames, or store API keys.
- It does not promise pixel-identical replication from text-to-video.
- It does not invoke Seedance, V2V, R2V, or any reference-tag workflow.

## Evidence contract

| Layer | Source of truth | Output |
|---|---|---|
| Semantics | `watch` frames plus local audio analysis | plot, shot, fixed inventory, comic mechanism |
| Kinematics | Native-rate tracked points | extension times, stroke rate, amplitude, velocity, alternation |
| Prompt | Both layers | English Omni Flash T2V brief with timing and stability locks |
| QA | Same analyses on generated video | source/output delta and a single-variable repair target |

## Delivery checks

The test suite validates the CSV-to-motion-contract path. Runtime validation must also confirm the resulting Omni MP4 container, duration, and 720×1280 dimensions before it is reported as generated.
