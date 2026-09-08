# Motion analysis for Omni Flash

## Why it exists

Semantic video analysis can identify an action such as “boxing,” but a sparse storyboard cannot establish its cadence. A high-frequency gesture must be measured from native-rate frames before it becomes a text constraint.

## Track schema

`build_motion_spec.py` reads CSV rows with these fields:

```text
frame,point_id,x,y,visible
0,left_wrist,120.4,83.2,1
```

Use two to five stable points per active limb. `cotracker_npz_to_csv.py` converts an NPZ containing `tracks` shaped `T,N,2` (or `1,T,N,2`) to that schema.

When CoTracker is impractical, `lk_points_to_csv.py` tracks manually seeded points at the source video's native frame rate with Lucas–Kanade optical flow and writes the same schema. Inspect those tracks before treating them as a motion contract: optical flow can drift during occlusion or blur.

## Example

```bash
python3 scripts/cotracker_npz_to_csv.py paw-tracks.npz --out tracks.csv --prefix paw
python3 scripts/build_motion_spec.py tracks.csv \
  --fps 30 --left paw0,paw1 --right paw2,paw3 --axis 1 0 \
  --out artifacts/source-motion-spec.json
python3 scripts/render_omni_motion_block.py artifacts/source-motion-spec.json \
  --subject "The hairless cat" --target "the black sofa"
```

Fast local fallback for manually inspected seeds:

```bash
python3 scripts/lk_points_to_csv.py source.mp4 \
  --points '{"paw0":[30,330],"paw1":[54,312],"paw2":[214,366],"paw3":[232,392]}' \
  --out tracks.csv
```

The axis points in the visual direction of the strike. Check the resulting extension timestamps against dense frames before treating the report as evidence.

## Prompt integration

Append the generated motion paragraph after the scene and inventory paragraph, then preserve the existing one-shot, 10-second, 9:16 Omni lock. Keep only one primary motion demand. A reference video is never named in the prompt because this workflow is T2V only.

## QA

Analyze the output with the same point groups and axis, then calculate the delta:

```bash
python3 scripts/compare_motion_specs.py artifacts/source-motion-spec.json \
  artifacts/output-motion-spec.json --out artifacts/motion-delta.json
```

Compare rate, median interval, extension amplitude, and alternation ratio. When cadence is wrong, revise the motion paragraph only; do not simultaneously change character, environment, camera, and audio.
