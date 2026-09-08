#!/usr/bin/env python3
"""Convert a CoTracker-style NPZ (`tracks`, optional `visibility`) to CSV."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prefix", default="point")
    args = parser.parse_args()
    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit("Install numpy to convert CoTracker NPZ files.") from exc
    data = np.load(args.input)
    tracks = data["tracks"]
    if tracks.ndim == 4:
        tracks = tracks[0]
    if tracks.ndim != 3 or tracks.shape[-1] != 2:
        raise SystemExit("tracks must have shape T,N,2 or 1,T,N,2")
    visibility = data["visibility"] if "visibility" in data else None
    if visibility is not None and visibility.ndim == 3:
        visibility = visibility[0]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["frame", "point_id", "x", "y", "visible"])
        writer.writeheader()
        for frame in range(tracks.shape[0]):
            for point in range(tracks.shape[1]):
                writer.writerow({"frame": frame, "point_id": f"{args.prefix}{point}", "x": float(tracks[frame, point, 0]), "y": float(tracks[frame, point, 1]), "visible": int(visibility is None or bool(visibility[frame, point]))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
