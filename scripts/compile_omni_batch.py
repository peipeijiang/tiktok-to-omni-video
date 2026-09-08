#!/usr/bin/env python3
"""Compile cached motion/impact evidence into Omni-only batch job variants."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROFILES = ("cadence", "impact", "framing")


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip(".-")


def resolve(value: str, source: Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else source.parent / candidate


def load_json(value: str | None, source: Path) -> dict | None:
    if not value:
        return None
    return json.loads(resolve(value, source).read_text(encoding="utf-8"))


def reject_reference_syntax(prompt: str) -> None:
    if re.search(r"@(video|image)\d*", prompt, flags=re.IGNORECASE):
        raise ValueError("Omni T2V prompts must not contain media-reference tags")


def cadence_block(item: dict, motion: dict) -> str:
    rate = (motion["left"]["extensions_per_second"] + motion["right"]["extensions_per_second"]) / 2
    action = item.get("action", "repeated action")
    return (
        f"Cadence lock: {item['subject']} performs the source's {action} as an unbroken alternating loop at approximately {rate:.2f} extension-and-recoil cycles per active side per second. "
        "Each cycle uses a compact preparation, a short directed extension, and immediate recoil; no held pose, slow waving, pause, or unrelated gesture."
    )


def impact_block(item: dict, impact: dict) -> str:
    response = impact.get("target_response")
    response_clause = f" Show the verified target response: {response}." if response else ""
    return (
        f"Impact lock: drive each short strike from {impact['anchor']} toward {impact['target']}; at peak extension the active part visibly reaches the target, stops there, and immediately rebounds. "
        "Keep non-active anatomy and the camera stable enough that the acceleration, contact, deceleration, and recoil remain legible. "
        "Do not replace contact with floating, swinging, or air-punch gestures."
        f"{response_clause}"
    )


def framing_block(item: dict) -> str:
    lock = item.get("framing_lock")
    if not lock:
        raise ValueError("framing profile requires framing_lock")
    return f"Framing lock: {lock}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path, help="JSON array of source records")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--profiles", default=",".join(PROFILES), help="comma-separated subset of cadence,impact,framing")
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    profiles = tuple(profile.strip() for profile in args.profiles.split(",") if profile.strip())
    if not profiles or any(profile not in PROFILES for profile in profiles):
        parser.error(f"--profiles must be a subset of {','.join(PROFILES)}")
    records = json.loads(args.batch.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        parser.error("batch must be a JSON array")
    jobs = []
    for item in records:
        required = ("source_id", "base_prompt", "subject")
        missing = [key for key in required if not item.get(key)]
        if missing:
            raise ValueError(f"batch record missing {', '.join(missing)}")
        base_prompt = str(item["base_prompt"]).strip()
        reject_reference_syntax(base_prompt)
        motion = load_json(item.get("motion_spec"), args.batch)
        impact = load_json(item.get("impact_spec"), args.batch)
        for profile in profiles:
            additions = []
            if profile in {"cadence", "impact", "framing"}:
                if not motion:
                    raise ValueError(f"{item['source_id']}: {profile} requires motion_spec")
                additions.append(cadence_block(item, motion))
            if profile in {"impact", "framing"}:
                if not impact:
                    raise ValueError(f"{item['source_id']}: {profile} requires impact_spec")
                additions.append(impact_block(item, impact))
            if profile == "framing":
                additions.append(framing_block(item))
            prompt = base_prompt + "\n\n" + "\n".join(additions)
            reject_reference_syntax(prompt)
            job_id = safe_id(f"{item['source_id']}-{profile}-{args.version}")
            jobs.append(
                {
                    "job_id": job_id,
                    "filename": job_id,
                    "prompt": prompt,
                    "metadata": {"source_id": item["source_id"], "profile": profile, "version": args.version},
                }
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(jobs)} jobs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
