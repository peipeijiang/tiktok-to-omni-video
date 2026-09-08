#!/usr/bin/env python3
"""Derive evidence-labelled contact candidates from tracked action points.

This intentionally does not claim to simulate force.  It locates extension peaks
that geometrically approach a user-verified target point so a prompt can request
the visible contact-and-recoil consequence, and so a generated take can be
ranked on the same evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from build_motion_spec import load_tracks, parse_ids


def averaged_positions(
    tracks: dict[str, list[tuple[float, float, float]]], ids: set[str]
) -> dict[float, tuple[float, float]]:
    per_time: dict[float, list[tuple[float, float]]] = defaultdict(list)
    for point_id in ids:
        if point_id not in tracks:
            raise ValueError(f"point id not found: {point_id}")
        for time_s, x, y in tracks[point_id]:
            per_time[time_s].append((x, y))
    return {
        time_s: (statistics.fmean(point[0] for point in points), statistics.fmean(point[1] for point in points))
        for time_s, points in per_time.items()
    }


def nearest_position(positions: dict[float, tuple[float, float]], time_s: float) -> tuple[float, float]:
    nearest = min(positions, key=lambda candidate: abs(candidate - time_s))
    return positions[nearest]


def limb_contact_candidates(
    extension_times: list[float],
    positions: dict[float, tuple[float, float]],
    target: tuple[float, float],
    threshold: float,
) -> dict[str, object]:
    candidates = []
    for time_s in extension_times:
        x, y = nearest_position(positions, float(time_s))
        distance = math.hypot(x - target[0], y - target[1])
        candidates.append(
            {
                "time_s": round(float(time_s), 4),
                "distance_px": round(distance, 3),
                "within_threshold": distance <= threshold,
            }
        )
    hits = sum(candidate["within_threshold"] for candidate in candidates)
    return {
        "extension_count": len(candidates),
        "geometric_contact_count": hits,
        "geometric_contact_ratio": round(hits / len(candidates), 3) if candidates else 0.0,
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tracks", type=Path)
    parser.add_argument("motion_spec", type=Path)
    parser.add_argument("--fps", type=float, required=True)
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--anchor", required=True, help="verified force origin, such as shoulders")
    parser.add_argument("--target-point", nargs=2, type=float, required=True, metavar=("X", "Y"))
    parser.add_argument("--contact-threshold-px", type=float, required=True)
    parser.add_argument("--target-response", default="", help="only a visible response verified in the source")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.fps <= 0 or args.contact_threshold_px <= 0:
        parser.error("--fps and --contact-threshold-px must be positive")
    motion = json.loads(args.motion_spec.read_text(encoding="utf-8"))
    tracks = load_tracks(args.tracks, args.fps)
    target = tuple(args.target_point)
    left = limb_contact_candidates(
        motion["left"]["extension_times_s"],
        averaged_positions(tracks, parse_ids(args.left)),
        target,
        args.contact_threshold_px,
    )
    right = limb_contact_candidates(
        motion["right"]["extension_times_s"],
        averaged_positions(tracks, parse_ids(args.right)),
        target,
        args.contact_threshold_px,
    )
    total_extensions = left["extension_count"] + right["extension_count"]
    total_contacts = left["geometric_contact_count"] + right["geometric_contact_count"]
    report = {
        "schema_version": 1,
        "tracks": str(args.tracks),
        "motion_spec": str(args.motion_spec),
        "fps": args.fps,
        "subject": args.subject,
        "target": args.target,
        "anchor": args.anchor,
        "target_point": list(target),
        "contact_threshold_px": args.contact_threshold_px,
        "target_response": args.target_response or None,
        "evidence_level": "geometric contact candidates only; visually verify contact and target response",
        "left": left,
        "right": right,
        "combined": {
            "geometric_contact_ratio": round(total_contacts / total_extensions, 3) if total_extensions else 0.0,
            "mean_extensions_per_second": round(
                (motion["left"]["extensions_per_second"] + motion["right"]["extensions_per_second"]) / 2,
                3,
            ),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
