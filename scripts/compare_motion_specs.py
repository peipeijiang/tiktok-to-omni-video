#!/usr/bin/env python3
"""Compare source and generated motion contracts for one controlled retake."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


FIELDS = ("extensions_per_second", "median_interval_s", "median_amplitude_px", "median_peak_speed_px_s")


def delta(source: object, generated: object) -> float | None:
    if source is None or generated is None:
        return None
    return round(float(generated) - float(source), 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("generated", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    generated = json.loads(args.generated.read_text(encoding="utf-8"))
    limbs = {limb: {field: {"source": source[limb][field], "generated": generated[limb][field], "delta": delta(source[limb][field], generated[limb][field])} for field in FIELDS} for limb in ("left", "right")}
    result = {
        "schema_version": 1,
        "source": str(args.source),
        "generated": str(args.generated),
        "limbs": limbs,
        "alternation_ratio": {
            "source": source["alternation"]["alternation_ratio"],
            "generated": generated["alternation"]["alternation_ratio"],
            "delta": delta(source["alternation"]["alternation_ratio"], generated["alternation"]["alternation_ratio"]),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
