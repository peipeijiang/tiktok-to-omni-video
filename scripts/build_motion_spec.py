#!/usr/bin/env python3
"""Turn tracked points into a prompt-ready motion contract.

Input CSV columns: frame,point_id,x,y[,visible].  Frame zero is accepted.
The selected points for each limb are averaged before projecting onto an action
axis.  Local maxima along that axis represent extension beats.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def parse_ids(raw: str) -> set[str]:
    values = {item.strip() for item in raw.split(",") if item.strip()}
    if not values:
        raise ValueError("at least one point id is required")
    return values


def load_tracks(path: Path, fps: float) -> dict[str, list[tuple[float, float, float]]]:
    grouped: dict[str, dict[int, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("visible", "1").strip().lower() in {"0", "false", "no"}:
                continue
            grouped[row["point_id"]][int(row["frame"])].append((float(row["x"]), float(row["y"])))
    result: dict[str, list[tuple[float, float, float]]] = {}
    for point_id, frames in grouped.items():
        result[point_id] = [
            (frame / fps, statistics.fmean(x for x, _ in values), statistics.fmean(y for _, y in values))
            for frame, values in sorted(frames.items())
        ]
    return result


def moving_average(values: list[float], radius: int = 1) -> list[float]:
    return [statistics.fmean(values[max(0, i - radius) : min(len(values), i + radius + 1)]) for i in range(len(values))]


def limb_series(tracks: dict[str, list[tuple[float, float, float]]], ids: set[str], axis: tuple[float, float]) -> list[tuple[float, float]]:
    per_time: dict[float, list[tuple[float, float]]] = defaultdict(list)
    for point_id in ids:
        if point_id not in tracks:
            raise ValueError(f"point id not found: {point_id}")
        for time_s, x, y in tracks[point_id]:
            per_time[time_s].append((x, y))
    norm = math.hypot(*axis)
    if norm == 0:
        raise ValueError("motion axis must be non-zero")
    ax, ay = axis[0] / norm, axis[1] / norm
    return [(time_s, statistics.fmean(x for x, _ in points) * ax + statistics.fmean(y for _, y in points) * ay) for time_s, points in sorted(per_time.items())]


def extensions(series: list[tuple[float, float]], fps: float, min_gap_s: float = 0.10) -> dict[str, object]:
    if len(series) < 5:
        raise ValueError("need at least five visible frames per limb")
    times = [item[0] for item in series]
    positions = moving_average([item[1] for item in series])
    velocity = [(positions[i] - positions[i - 1]) * fps for i in range(1, len(positions))]
    peak_indices: list[int] = []
    for index in range(1, len(velocity)):
        if velocity[index - 1] > 0 >= velocity[index] and (not peak_indices or times[index] - times[peak_indices[-1]] >= min_gap_s):
            peak_indices.append(index)
    amplitudes = [positions[index] - min(positions[max(0, index - 3) : index + 1]) for index in peak_indices]
    speeds = [max(velocity[max(0, index - 3) : min(len(velocity), index + 1)], default=0.0) for index in peak_indices]
    duration = max(times[-1] - times[0], 1.0 / fps)
    intervals = [times[b] - times[a] for a, b in zip(peak_indices, peak_indices[1:])]
    return {
        "extension_times_s": [round(times[index], 4) for index in peak_indices],
        "extensions_per_second": round(len(peak_indices) / duration, 3),
        "median_interval_s": round(statistics.median(intervals), 4) if intervals else None,
        "median_amplitude_px": round(statistics.median(amplitudes), 3) if amplitudes else 0.0,
        "median_peak_speed_px_s": round(statistics.median(speeds), 3) if speeds else 0.0,
    }


def alternating(left: list[float], right: list[float]) -> dict[str, object]:
    merged = sorted([(time_s, "left") for time_s in left] + [(time_s, "right") for time_s in right])
    changes = sum(label != previous for (_, previous), (_, label) in zip(merged, merged[1:]))
    return {"ordered_extensions": [{"time_s": round(time_s, 4), "limb": label} for time_s, label in merged], "alternation_ratio": round(changes / max(len(merged) - 1, 1), 3)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tracks", type=Path)
    parser.add_argument("--fps", type=float, required=True)
    parser.add_argument("--left", required=True, help="comma-separated left-limb point IDs")
    parser.add_argument("--right", required=True, help="comma-separated right-limb point IDs")
    parser.add_argument("--axis", nargs=2, type=float, metavar=("X", "Y"), required=True, help="forward action direction in image coordinates")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.fps <= 0:
        parser.error("--fps must be positive")
    tracks = load_tracks(args.tracks, args.fps)
    left = extensions(limb_series(tracks, parse_ids(args.left), tuple(args.axis)), args.fps)
    right = extensions(limb_series(tracks, parse_ids(args.right), tuple(args.axis)), args.fps)
    report = {"schema_version": 1, "source_tracks": str(args.tracks), "fps": args.fps, "axis": args.axis, "left": left, "right": right, "alternation": alternating(left["extension_times_s"], right["extension_times_s"])}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
