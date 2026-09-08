#!/usr/bin/env python3
"""Render an evidence-bound Omni Flash motion paragraph from motion-spec.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("motion_spec", type=Path)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    spec = json.loads(args.motion_spec.read_text(encoding="utf-8"))
    rate = (spec["left"]["extensions_per_second"] + spec["right"]["extensions_per_second"]) / 2
    print(
        f"{args.subject} performs a continuous alternating left-right extension-and-recoil loop toward {args.target} at approximately {rate:.2f} extensions per paw per second. "
        "Each paw starts near a compact guard, snaps forward along a short visible path, immediately recoils, then hands off to the opposite paw. "
        "Keep the torso, head, collar, environment, and camera stable; only the active paw may show narrow directional motion blur. "
        "Do not substitute slow waving, held boxing poses, gentle dancing, or pauses."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
