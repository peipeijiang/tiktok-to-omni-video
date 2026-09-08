# Batch impact workflow

This is a lightweight Omni Flash workflow for forceful-looking actions such as punches, kicks, pushes, taps, throws, doors closing, or objects colliding. It uses tracked points and OpenCV-style geometry only. It downloads no model weights and does not claim to run a force simulation.

## What is measured

`motion-spec.json` measures cadence and extension/recoil peaks. An `impact-spec.json` adds a *geometric contact candidate*: at an extension peak, does the tracked active part enter a user-verified distance threshold around a user-verified target point? It also records the force origin and any target response actually visible in the source.

The result is evidence-labelled. A close point is not proof of a collision, so visually verify contact and target response before claiming an exact recreation.

## Per-source analysis, once

```bash
python3 scripts/build_motion_spec.py tracks.csv \
  --fps 30 --left paw0,paw1 --right paw2,paw3 --axis -1 0 \
  --out artifacts/clip-1-motion.json

python3 scripts/build_impact_spec.py tracks.csv artifacts/clip-1-motion.json \
  --fps 30 --left paw0,paw1 --right paw2,paw3 \
  --subject "The hairless cat" --target "the black sofa cushion" \
  --anchor "the shoulders" --target-point 40 325 \
  --contact-threshold-px 35 \
  --target-response "a brief, small cushion compression" \
  --out artifacts/clip-1-impact.json
```

The manual target point is deliberate. A broad semantic label such as “sofa” is not precise enough to assert contact. Use dense source frames to place the point on the actual hit area. Cache the two JSON files; prompt variants never repeat this analysis.

## Compile three reusable variants

Create `batch.json`. Paths are relative to this file; `base_prompt` is the already evidence-checked, complete English Omni prompt without reference tags.

```json
[
  {
    "source_id": "clip-1",
    "base_prompt": "Create a 10-second vertical 9:16 smartphone video...",
    "subject": "The hairless cat",
    "action": "alternating paw strikes",
    "motion_spec": "artifacts/clip-1-motion.json",
    "impact_spec": "artifacts/clip-1-impact.json",
    "framing_lock": "tight left-facing crop; the sofa hit area remains at upper left; no full-body wide view."
  }
]
```

```bash
python3 scripts/compile_omni_batch.py batch.json \
  --out artifacts/omni-jobs.json --version v1
```

This emits three jobs per source in stable order:

1. `cadence`: compact preparation → extension → immediate recoil.
2. `impact`: cadence plus anchor → target → contact → rebound causality.
3. `framing`: impact plus the explicit source camera/composition lock.

The output remains Omni T2V-only: it rejects `@Video` and `@Image` syntax. Submit it with the existing manifest runner. The first-job review gate remains in force; after explicit continuation, use `--all-remaining` for the already compiled queue.

## Batch QA and one-variable repair

Run the same tracking and impact analysis on each generated candidate. Its target point must be valid for that generated framing; if the camera moved, mark contact as visually unresolved rather than scoring an unrelated pixel.

```json
[
  {
    "candidate_id": "clip-1-impact-v1",
    "profile": "impact",
    "source_motion_spec": "artifacts/clip-1-motion.json",
    "generated_motion_spec": "artifacts/clip-1-impact-output.json",
    "source_impact_spec": "artifacts/clip-1-impact.json",
    "generated_impact_spec": "artifacts/clip-1-impact-output.json"
  }
]
```

```bash
python3 scripts/score_impact_batch.py candidates.json \
  --out artifacts/batch-ranking.json
```

The ranker compares per-side rate, alternation and, when both target points are valid, the geometric-contact ratio. It returns exactly one next repair profile: `cadence`, `impact`, or `impact_visual_check`. It never diagnoses hidden model causes and does not treat a geometric candidate as physical force.
