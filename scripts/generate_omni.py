#!/usr/bin/env python3
"""Submit, poll, and download Omni Flash jobs exactly once per job_id."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://api.lk888.ai"


def request_json(url: str, method: str, payload: dict | None, key: str, timeout: int = 30) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode())


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-") or "omni-video"


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid manifest {path}: {exc}")


def save_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    try:
        path.chmod(0o600)
    except OSError:
        pass


def create_job(
    job: dict,
    manifest: dict,
    manifest_path: Path,
    key: str,
    model: str,
    duration: str | None,
) -> dict:
    job_id = str(job["job_id"])
    if job_id in manifest:
        print(f"{job_id}: already recorded; skip POST")
        return manifest[job_id]
    record = {"job": job, "submitted": False, "state": "not_submitted"}
    manifest[job_id] = record
    save_manifest(manifest_path, manifest)
    try:
        params = {"aspect_ratio": "9:16"}
        if duration is not None:
            params["duration"] = duration
        response = request_json(
            f"{BASE}/v1/media/generate",
            "POST",
            {"model": model, "params": params, "prompt": job["prompt"]},
            key,
        )
    except Exception as exc:
        record.update({"state": "submission_unknown_no_retry", "error": str(exc)})
        save_manifest(manifest_path, manifest)
        print(f"{job_id}: POST uncertain; recorded without retry")
        return record
    task_id = ((response.get("data") or {}).get("task_id") or response.get("task_id") or response.get("id"))
    if not task_id:
        record.update({"state": "submission_failed_no_retry", "response": response})
        save_manifest(manifest_path, manifest)
        print(f"{job_id}: POST failed; recorded without retry")
        return record
    record.update({"submitted": True, "task_id": task_id, "state": "submitted"})
    save_manifest(manifest_path, manifest)
    print(f"{job_id}: submitted task {task_id}")
    return record


def poll_job(record: dict, manifest: dict, manifest_path: Path, output_dir: Path, key: str) -> None:
    if not record.get("submitted") or record.get("state") in {"success", "failed", "submission_failed_no_retry", "submission_unknown_no_retry"}:
        return
    task_id = record["task_id"]
    for _ in range(180):
        try:
            status = request_json(f"{BASE}/v1/media/status?task_id={task_id}", "GET", None, key)
        except Exception as exc:
            print(f"{record['job']['job_id']}: status retry ({exc})")
            time.sleep(5)
            continue
        state = status.get("state", "unknown")
        record.update({"state": state, "progress": status.get("progress", "")})
        save_manifest(manifest_path, manifest)
        print(f"{record['job']['job_id']}: {state} {status.get('progress', '')}")
        if state == "failed":
            record["error"] = status.get("error", "")
            save_manifest(manifest_path, manifest)
            return
        if state == "success":
            result_url = status.get("result_url")
            if not result_url:
                record.update({"state": "success_no_url"})
                save_manifest(manifest_path, manifest)
                return
            filename = safe_name(record["job"].get("filename") or record["job"]["job_id"]) + ".mp4"
            output = output_dir / filename
            try:
                with urllib.request.urlopen(result_url, timeout=60) as response:
                    output.write_bytes(response.read())
            except Exception as exc:
                print(f"{record['job']['job_id']}: download retry ({exc})")
                time.sleep(5)
                continue
            record.update({"state": "success", "file": str(output)})
            save_manifest(manifest_path, manifest)
            return
        time.sleep(5)
    record["state"] = "poll_timeout"
    save_manifest(manifest_path, manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jobs_json", type=Path)
    gate = parser.add_mutually_exclusive_group()
    gate.add_argument("--limit", type=int, default=1, help="first-video review gate; must be 1")
    gate.add_argument(
        "--all-remaining",
        action="store_true",
        help="after explicit user continuation, POST every job not already recorded in the manifest",
    )
    parser.add_argument("--out-dir", type=Path, default=Path.home() / "Desktop" / "wibly-videos")
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--model", default="omni_flash-10s")
    parser.add_argument("--duration", choices=("4", "6", "8", "10"), default=None)
    args = parser.parse_args()
    if not args.all_remaining and args.limit != 1:
        raise SystemExit("First-video review gate: --limit must be 1. Use --all-remaining only after explicit user continuation.")
    submission_limit = None if args.all_remaining else 1
    key = os.environ.get("OMNI_API_KEY") or os.environ.get("UPDRAMA_API_KEY")
    if not key:
        raise SystemExit("Set OMNI_API_KEY or UPDRAMA_API_KEY; never put the key in jobs_json")
    jobs = json.loads(args.jobs_json.read_text())
    if not isinstance(jobs, list):
        raise SystemExit("jobs_json must contain a JSON list")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.manifest or args.out_dir / "omni-task-manifest.json"
    manifest = load_manifest(manifest_path)
    new_count = 0
    records = []
    for job in jobs:
        if str(job["job_id"]) not in manifest and submission_limit is not None and new_count >= submission_limit:
            break
        before = str(job["job_id"]) in manifest
        record = create_job(job, manifest, manifest_path, key, args.model, args.duration)
        records.append(record)
        if not before:
            new_count += 1
    for record in records:
        poll_job(record, manifest, manifest_path, args.out_dir, key)
    success = sum(1 for record in manifest.values() if record.get("state") == "success")
    print(f"summary: recorded={len(manifest)} success={success} manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
