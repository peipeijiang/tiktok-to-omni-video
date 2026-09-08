#!/usr/bin/env python3
"""Track manually seeded points with Lucas–Kanade optical flow into the shared CSV format."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--points", required=True, help='JSON object, e.g. {"paw0":[31,330]}')
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    points = json.loads(args.points)
    if not points or any(len(point) != 2 for point in points.values()):
        raise SystemExit("--points must map each point id to [x, y].")
    ids = list(points)
    tracked = np.asarray([points[point_id] for point_id in ids], dtype=np.float32).reshape(-1, 1, 2)
    capture = cv2.VideoCapture(str(args.video))
    ok, first = capture.read()
    if not ok:
        raise SystemExit(f"Unable to read {args.video}")
    previous_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    rows = [(0, point_id, *map(float, tracked[index, 0]), 1) for index, point_id in enumerate(ids)]
    frame = 0
    while True:
        ok, current = capture.read()
        if not ok:
            break
        frame += 1
        current_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
        next_points, status, _error = cv2.calcOpticalFlowPyrLK(
            previous_gray, current_gray, tracked, None, winSize=(31, 31), maxLevel=4,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        for index, point_id in enumerate(ids):
            visible = int(status[index, 0])
            if visible:
                tracked[index] = next_points[index]
            x, y = tracked[index, 0]
            rows.append((frame, point_id, float(x), float(y), visible))
        previous_gray = current_gray
    capture.release()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame", "point_id", "x", "y", "visible"])
        writer.writerows(rows)
    print(f"wrote {args.out} ({frame + 1} frames, {len(ids)} points)")


if __name__ == "__main__":
    main()
