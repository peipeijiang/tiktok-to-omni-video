#!/usr/bin/env python3
"""Rank Omni candidates and name the one motion-control profile to repair next."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def resolve(value: str, source: Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else source.parent / candidate


def load(value: str | None, source: Path) -> dict | None:
    return json.loads(resolve(value, source).read_text(encoding="utf-8")) if value else None


def similarity(source: float, generated: float) -> float:
    if source <= 0:
        return 0.0
    return round(max(0.0, 1.0 - min(abs(generated / source - 1.0), 1.0)), 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path, help="JSON array with source/generated spec paths")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.candidates.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        parser.error("candidates must be a JSON array")
    scored = []
    for record in records:
        source = load(record["source_motion_spec"], args.candidates)
        generated = load(record["generated_motion_spec"], args.candidates)
        rate_score = sum(
            similarity(source[limb]["extensions_per_second"], generated[limb]["extensions_per_second"])
            for limb in ("left", "right")
        ) / 2
        alternation_score = round(
            max(0.0, 1.0 - abs(source["alternation"]["alternation_ratio"] - generated["alternation"]["alternation_ratio"])),
            3,
        )
        source_impact = load(record.get("source_impact_spec"), args.candidates)
        generated_impact = load(record.get("generated_impact_spec"), args.candidates)
        contact_score = None
        if source_impact and generated_impact:
            contact_score = similarity(
                source_impact["combined"]["geometric_contact_ratio"],
                generated_impact["combined"]["geometric_contact_ratio"],
            )
        if contact_score is None:
            overall = round(0.7 * rate_score + 0.3 * alternation_score, 3)
            repair = "impact_visual_check"
        else:
            overall = round(0.5 * rate_score + 0.2 * alternation_score + 0.3 * contact_score, 3)
            repair = "impact" if contact_score < min(rate_score, alternation_score) else "cadence"
        scored.append(
            {
                "candidate_id": record.get("candidate_id", "unnamed"),
                "profile": record.get("profile"),
                "overall_score": overall,
                "rate_score": round(rate_score, 3),
                "alternation_score": alternation_score,
                "contact_score": contact_score,
                "next_repair_profile": repair,
                "contact_note": "geometric candidates require visual confirmation; this is not a force simulation",
            }
        )
    scored.sort(key=lambda item: item["overall_score"], reverse=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"schema_version": 1, "ranked": scored}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
