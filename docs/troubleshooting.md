# Troubleshooting

## The result recognizes the action but performs it slowly

This is a motion-fidelity failure, not proof of a hidden model cause. Confirm that source tracks use native FPS and that the source `motion-spec.json` contains extension timestamps. Re-run the output through the same tracker, compare with `compare_motion_specs.py`, and revise only the prompt's motion paragraph: rate, guard-to-extension path, recoil, pause limit, and stable anchors.

## Track peaks do not match visible strikes

Check the action axis and selected point IDs against dense frames. Use two to five points per limb, exclude invisible points, and choose an axis that points toward extension. Do not interpret tracker output as evidence until the peak timestamps match inspected video frames.

## A generated video drifts in identity or camera while motion improves

The motion request may be spending too much of the generation budget. Preserve the original subject count, crop, environment, and camera as explicit stable anchors; keep a single primary action and remove secondary motion or decorative instructions.

## The job cannot be submitted or downloaded

Use the original `generate_omni.py` manifest discipline. Set credentials only through `OMNI_API_KEY` or `UPDRAMA_API_KEY`; never place a key in a prompt or jobs file. An uncertain POST must not be submitted again with the same job ID.
