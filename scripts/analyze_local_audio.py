#!/usr/bin/env python3
"""Extract a complete audio evidence bundle and transcribe speech with local MLX Whisper."""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path


DEFAULT_MLX_MODEL = Path.home() / ".cache" / "watch" / "whisper-small-mlx"
DEFAULT_CPP_MODEL = Path.home() / ".cache" / "whisper.cpp" / "ggml-base.bin"


def find_program(name: str) -> str | None:
    candidates = [f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}", shutil.which(name)]
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        result = subprocess.run([candidate, "-version"], text=True, capture_output=True)
        if result.returncode == 0 and result.stdout.lower().startswith(f"{name} version"):
            return candidate
    return None


def find_mlx_whisper() -> str | None:
    candidates = [os.environ.get("LOCAL_WHISPER_BIN"), shutil.which("mlx_whisper")]
    candidates.extend(
        sorted(glob.glob(str(Path.home() / "Library" / "Python" / "*" / "bin" / "mlx_whisper")), reverse=True)
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(Path(candidate).resolve())
    return None


def find_whisper_cpp() -> str | None:
    candidates = [
        os.environ.get("WHISPER_CPP_BIN"),
        os.environ.get("LOCAL_WHISPER_BIN"),
        shutil.which("whisper-cli"),
        "/opt/homebrew/bin/whisper-cli",
        "/usr/local/bin/whisper-cli",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            if Path(candidate).name == "whisper-cli":
                return str(Path(candidate).resolve())
    return None


def preflight() -> dict:
    mlx_bin = find_mlx_whisper()
    mlx_model = Path(
        os.environ.get("LOCAL_WHISPER_MODEL", str(DEFAULT_MLX_MODEL))
    ).expanduser().resolve()
    cpp_bin = find_whisper_cpp()
    cpp_model = Path(
        os.environ.get("WHISPER_CPP_MODEL", str(DEFAULT_CPP_MODEL))
    ).expanduser().resolve()
    mlx_ready = bool(
        mlx_bin and (mlx_model / "config.json").is_file() and (mlx_model / "weights.npz").is_file()
    )
    cpp_ready = bool(cpp_bin and cpp_model.is_file())
    backend = "mlx_whisper" if mlx_ready else "whisper_cpp" if cpp_ready else None
    executable = mlx_bin if backend == "mlx_whisper" else cpp_bin if backend == "whisper_cpp" else None
    model = mlx_model if backend == "mlx_whisper" else cpp_model if backend == "whisper_cpp" else mlx_model
    result = {
        "ffmpeg": find_program("ffmpeg"),
        "ffprobe": find_program("ffprobe"),
        "backend": backend,
        "executable": executable,
        "model": str(model),
        "model_ready": mlx_ready or cpp_ready,
        "mlx_whisper": {"executable": mlx_bin, "model": str(mlx_model), "ready": mlx_ready},
        "whisper_cpp": {"executable": cpp_bin, "model": str(cpp_model), "ready": cpp_ready},
    }
    result["ready"] = bool(
        result["ffmpeg"] and result["ffprobe"] and result["backend"] and result["model_ready"]
    )
    return result


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        raise SystemExit(f"Command failed ({cmd[0]}): {detail}")
    return result


def audio_features(wav_path: Path, window_seconds: float = 0.5) -> list[dict]:
    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit("numpy is required for local audio measurements") from exc
    with wave.open(str(wav_path), "rb") as source:
        rate = source.getframerate()
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        raw_samples = source.readframes(source.getnframes())
    dtype_by_width = {1: np.dtype("u1"), 2: np.dtype("<i2"), 4: np.dtype("<i4")}
    if sample_width not in dtype_by_width:
        raise SystemExit(f"Unsupported PCM sample width: {sample_width} bytes")
    dtype = dtype_by_width[sample_width]
    samples = np.frombuffer(raw_samples, dtype=dtype).astype(np.float64)
    if sample_width == 1:
        samples -= 128.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    scale = float(2 ** (8 * sample_width - 1))
    samples = samples / scale
    size = max(1, int(rate * window_seconds))
    rows = []
    for offset in range(0, len(samples), size):
        chunk = samples[offset:offset + size]
        if not len(chunk):
            continue
        rms = float(np.sqrt(np.mean(chunk * chunk)))
        rms_dbfs = 20.0 * math.log10(max(rms, 1e-9))
        zcr = float(np.mean(np.abs(np.diff(np.signbit(chunk))))) if len(chunk) > 1 else 0.0
        spectrum = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
        freqs = np.fft.rfftfreq(len(chunk), 1.0 / rate)
        total = float(spectrum.sum()) or 1.0
        centroid = float((freqs * spectrum).sum() / total)

        def ratio(low: float, high: float) -> float:
            mask = (freqs >= low) & (freqs < high)
            return float(spectrum[mask].sum() / total)

        rows.append(
            {
                "start": round(offset / rate, 3),
                "end": round(min(offset + size, len(samples)) / rate, 3),
                "rms_dbfs": round(rms_dbfs, 2),
                "spectral_centroid_hz": round(centroid, 1),
                "zero_crossing_rate": round(zcr, 4),
                "low_ratio_20_250hz": round(ratio(20, 250), 4),
                "mid_ratio_250_4000hz": round(ratio(250, 4000), 4),
                "high_ratio_4000_12000hz": round(ratio(4000, 12000), 4),
                "silence_candidate": rms_dbfs < -45.0,
            }
        )
    return rows


def normalize_transcript(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "transcription" in raw:
        segments = []
        full_text = []
        for segment in raw.get("transcription", []):
            offsets = segment.get("offsets") or {}
            text = str(segment.get("text", "")).strip()
            words = []
            for token in segment.get("tokens", []):
                token_text = str(token.get("text", ""))
                if token_text.startswith("[_"):
                    continue
                token_offsets = token.get("offsets") or {}
                words.append(
                    {
                        "start": round(float(token_offsets.get("from", 0)) / 1000.0, 3),
                        "end": round(float(token_offsets.get("to", 0)) / 1000.0, 3),
                        "word": token_text.strip(),
                    }
                )
            row = {
                "start": round(float(offsets.get("from", 0)) / 1000.0, 3),
                "end": round(float(offsets.get("to", 0)) / 1000.0, 3),
                "text": text,
            }
            if words:
                row["words"] = words
            segments.append(row)
            if text:
                full_text.append(text)
        return {
            "language": (raw.get("result") or {}).get("language"),
            "text": " ".join(full_text).strip(),
            "segments": segments,
        }
    segments = []
    for segment in raw.get("segments", []):
        row = {
            "start": round(float(segment.get("start", 0)), 3),
            "end": round(float(segment.get("end", 0)), 3),
            "text": str(segment.get("text", "")).strip(),
        }
        if segment.get("words"):
            row["words"] = [
                {
                    "start": round(float(word.get("start", 0)), 3),
                    "end": round(float(word.get("end", 0)), 3),
                    "word": str(word.get("word", "")).strip(),
                }
                for word in segment["words"]
            ]
        segments.append(row)
    return {
        "language": raw.get("language"),
        "text": str(raw.get("text", "")).strip(),
        "segments": segments,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--language", help="optional Whisper language code; auto-detect by default")
    parser.add_argument("--check", action="store_true", help="verify local dependencies without processing media")
    args = parser.parse_args()
    status = preflight()
    if args.check:
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0 if status["ready"] else 2
    if not status["ready"]:
        raise SystemExit("Local audio preflight failed:\n" + json.dumps(status, ensure_ascii=False, indent=2))
    if not args.video or not args.video.is_file():
        raise SystemExit("Provide an existing local video path")
    out_dir = (
        args.out_dir
        or args.video.with_suffix("").with_name(args.video.stem + "-audio-evidence")
    ).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    full_mix = out_dir / "full_mix.wav"
    whisper_wav = out_dir / "whisper.wav"
    spectrogram = out_dir / "spectrogram.png"
    waveform = out_dir / "waveform.png"
    ffmpeg = str(status["ffmpeg"])
    run(
        [
            ffmpeg, "-y", "-i", str(args.video.resolve()), "-vn", "-ac", "2", "-ar", "44100",
            "-c:a", "pcm_s16le", str(full_mix),
        ]
    )
    run([ffmpeg, "-y", "-i", str(full_mix), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(whisper_wav)])
    run([ffmpeg, "-y", "-i", str(full_mix), "-lavfi", "showspectrumpic=s=1600x900:legend=1:color=fiery", str(spectrogram)])
    run(
        [
            ffmpeg, "-y", "-i", str(full_mix), "-filter_complex",
            "aformat=channel_layouts=mono,showwavespic=s=1600x500:colors=white",
            "-frames:v", "1", str(waveform),
        ]
    )
    transcript_raw = out_dir / "transcript_raw.json"
    if status["backend"] == "mlx_whisper":
        whisper_cmd = [
            str(status["executable"]), str(whisper_wav), "--model", str(status["model"]),
            "--output-format", "json", "--output-dir", str(out_dir), "--output-name", "transcript_raw",
            "--verbose", "False", "--word-timestamps", "True",
        ]
        if args.language:
            whisper_cmd.extend(["--language", args.language])
    else:
        whisper_cmd = [
            str(status["executable"]), "-m", str(status["model"]), "-f", str(whisper_wav),
            "-l", args.language or "auto", "-ojf", "-of", str(transcript_raw.with_suffix("")), "-np",
        ]
    run(whisper_cmd)
    transcript = normalize_transcript(transcript_raw)
    transcript_path = out_dir / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    probe = run(
        [
            str(status["ffprobe"]), "-v", "error", "-show_entries",
            "format=duration:stream=index,codec_name,channels,sample_rate", "-of", "json", str(full_mix),
        ]
    )
    analysis = {
        "source": str(args.video.resolve()),
        "local_whisper": {
            "backend": status["backend"], "executable": status["executable"],
            "model": status["model"], "uploaded": False,
        },
        "probe": json.loads(probe.stdout),
        "windows": audio_features(full_mix),
        "interpretation_guard": (
            "Use measurements to locate candidate changes, then verify against full_mix.wav, spectrogram, "
            "transcript, and visible action. Do not infer song, genre, instrument, emotion, or source from measurements alone."
        ),
        "artifacts": {
            "full_mix": str(full_mix), "whisper_audio": str(whisper_wav),
            "transcript": str(transcript_path), "spectrogram": str(spectrogram), "waveform": str(waveform),
        },
    }
    analysis_path = out_dir / "audio_analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "ready": True, "out_dir": str(out_dir), "artifacts": analysis["artifacts"],
                "analysis": str(analysis_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
