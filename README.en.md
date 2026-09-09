# TikTok to Omni Video

[简体中文](README.md) · **English**

> Compile story, audio, and high-temporal-motion evidence from a short video into auditable Omni Flash recreation prompts, with optional pose-storyboard reference images.

[![CI](https://github.com/peipeijiang/tiktok-to-omni-video/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/peipeijiang/tiktok-to-omni-video/actions/workflows/ci.yml) [![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

TikTok to Omni Video keeps the original story, audio, comedy, and continuity analysis while adding native-frame-rate motion analysis. `watch` answers *what happens and why it lands*; tracked points answer *how fast, how far, and in which alternating order*. Both constrain an English Omni Flash text prompt and the generated take is measured with the same motion contract.

## Pipeline

```mermaid
flowchart LR
  V[Local or public video] --> W[watch: story, framing, subjects]
  V --> A[Local Whisper: speech and audio]
  V --> T[Native-rate tracked points]
  T --> M[motion-spec.json]
  M --> I[impact-spec.json]
  W --> P[English Omni prompt]
  A --> P
  M --> P
  I --> P
  P --> O[First Omni Flash render]
  O --> Q[Repeat trajectory/contact-candidate QA]
  M --> Q
  I --> Q
  Q --> R[Batch ranking and one-variable repair]
```

## Quick start

Python 3.10+ is required. Full video analysis also requires the original skill's `ffmpeg`, `ffprobe`, and local Whisper prerequisites. This repository contains no source videos, frames, audio, task manifests, or keys.

Convert point tracks exported by CoTracker or another tracker to normalized CSV, then build a motion specification:

```bash
python3 -m pip install -r requirements-motion.txt

python3 scripts/cotracker_npz_to_csv.py paw-tracks.npz \
  --out tracks.csv --prefix paw

python3 scripts/build_motion_spec.py tracks.csv \
  --fps 30 --left paw0,paw1 --right paw2,paw3 --axis 1 0 \
  --out artifacts/source-motion-spec.json

python3 scripts/render_omni_motion_block.py artifacts/source-motion-spec.json \
  --subject "The hairless cat" --target "the black sofa"
```

The final command prints an English motion paragraph that can be inserted into an Omni prompt. It never emits Seedance tags, image/video reference tags, or upload instructions.

## Outputs

| Artifact | Purpose |
|---|---|
| `watch` frames and local audio analysis | Camera, subjects, props, causal action, comedy, and audio evidence |
| `tracks.csv` | Native-rate point tracks; one visible point position per row |
| `motion-spec.json` | Extension timing, stroke rate, amplitude, peak speed, and alternation |
| `impact-spec.json` | Force anchor, target point, geometric contact candidates, and verified target response |
| English Omni prompt | Scene and causality locks plus measurable motion and continuity constraints |
| `motion-delta.json` | Source-versus-output cadence, amplitude, speed, and alternation differences |

## Omni Flash only

Prompts always contain clean English natural language, never `@Video1`, `@Image1`, source URLs, or upload syntax. The default route is text-to-video; when the user explicitly approves a pose/storyboard, put one to three PNG/JPEG/WebP paths (relative to the job file) or HTTP(S) URLs in the job's `reference_images` field. The runner sends them separately as Omni Flash `params.images`. Each job is a 10-second, 9:16, 720P continuous phone shot. The first job must download and pass container, duration, and dimension checks before the queue continues.

A fast action needs an actor, forward direction, measured rate, extension-to-recoil path, stable anchors, and an endpoint. `fast punches` is not enough; use the measured cadence, compact guard, short extension, and immediate recoil. See [motion analysis](docs/motion-analysis.md) and the [Omni prompt contract](docs/omni-prompt-contract.md).

## Pose-storyboard references

Storyboards make pose grammar, camera side, and cyclic action easier to hold; they do not replace the native-rate motion specification. Add one to three authorized images to a batch:

```json
{
  "reference_images": ["cat-pose-board.jpg", "opening-pose.jpg"]
}
```

The compiler preserves the field. At request time the runner encodes local images as image data and passes remote URLs through to `params.images`; image bytes are not saved in the job JSON or manifest. The prompt must still say that the images are pose/composition references only and must not become a collage.

## Fast batches and impact

The batch path downloads no model weights. It uses OpenCV optical flow, native-rate tracks, and cached JSON: analyze each source once, compile `cadence`, `impact`, and `framing` Omni variants, rank generated candidates by rate, alternation, and geometric contact candidates, then repair one failed dimension only. See the [batch impact workflow](docs/batch-impact-workflow.md) for commands, JSON inputs, and the important limitation that geometric contact is not a physics simulation.

## Motion QA

Run the same point groups and action axis on the generated output:

```bash
python3 scripts/build_motion_spec.py generated-tracks.csv \
  --fps 30 --left paw0,paw1 --right paw2,paw3 --axis 1 0 \
  --out artifacts/output-motion-spec.json

python3 scripts/compare_motion_specs.py artifacts/source-motion-spec.json \
  artifacts/output-motion-spec.json --out artifacts/motion-delta.json
```

When cadence misses, revise only the motion paragraph and preserve subject, environment, camera, and audio locks. Do not infer a model-internal cause from one failed take.

## Optional CoTracker

[CoTracker](https://github.com/facebookresearch/co-tracker) can follow arbitrary pixels in non-standard animal poses such as Sphynx forepaws. It is optional: this project accepts any tracker that emits the documented [CSV schema](docs/motion-analysis.md#track-schema). Review CoTracker's license and hardware requirements before use.

## Privacy, rights, and limitations

- Analyze only media you own, are licensed to use, or are authorized to process. Do not publish source video, private likenesses, readable watermarks, or brand marks.
- API keys are read only from environment variables, never from job JSON, logs, or this repository.
- Measured motion constraints and approved storyboard references improve control; they cannot guarantee pixel- or trajectory-identical output.
- The pre-upgrade skill snapshot is retained in [archive/original-skill](archive/original-skill) for auditability.

## Development

```bash
python3 -m unittest discover -s tests -v
```

Contributions are welcome through Issues and Pull Requests. See [troubleshooting](docs/troubleshooting.md).

## License

[MIT](LICENSE)
