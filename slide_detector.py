#!/usr/bin/env python3
"""Extract blue-background slide frames from a lecture video using ffmpeg.

The script automates the manual steps we ran earlier:
1. Use ffmpeg scene detection to grab potential slide frames.
2. Reduce each candidate to a 1x1 pixel (average colour) and keep frames that
   look blue.
3. Optionally assemble the filtered frames into a contact sheet JPEG.

Example:
    python3 slide_detector.py --video test.mp4 --contact-sheet slide_detector.jpeg
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass


def run_ffmpeg(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess:
    """Execute ffmpeg with shared defaults."""
    base_cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if capture:
        return subprocess.run(base_cmd + args, check=True, stdout=subprocess.PIPE)
    subprocess.run(base_cmd + args, check=True)
    return subprocess.CompletedProcess(args=[], returncode=0)


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

def extract_candidates(video: Path, raw_dir: Path, threshold: float) -> list[Path]:
    ensure_clean_dir(raw_dir)
    pattern = raw_dir / "slide_%03d.png"
    filter_expr = f"select='gt(scene,{threshold})'"
    run_ffmpeg([
        "-y",
        "-i",
        str(video),
        "-vf",
        filter_expr,
        "-vsync",
        "vfr",
        str(pattern),
    ])
    return sorted(raw_dir.glob("*.png"))


def escape_movie_path(path: Path) -> str:
    return str(path).replace("'", r"\'")


def scene_timestamps(video: Path, threshold: float) -> list[float]:
    escaped = escape_movie_path(video.resolve())
    filter_spec = f"movie='{escaped}',select=gt(scene\\,{threshold})"
    proc = subprocess.run(
        [
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            filter_spec,
            "-show_entries",
            "frame=best_effort_timestamp_time",
            "-of",
            "csv=p=0",
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    timestamps: list[float] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            timestamps.append(float(line))
        except ValueError:
            continue
    return timestamps


@dataclass
class SlideRecord:
    image: Path
    timestamp: float
    rgb: tuple[int, int, int]


def average_rgb(image_path: Path) -> tuple[int, int, int] | None:
    try:
        proc = run_ffmpeg(
            [
                "-i",
                str(image_path),
                "-vf",
                "scale=1:1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-",
            ],
            capture=True,
        )
    except subprocess.CalledProcessError:
        return None

    raw = proc.stdout
    if len(raw) < 3:
        return None
    return raw[0], raw[1], raw[2]


def looks_blue(rgb: tuple[int, int, int], *, minimum: int, dominance: int) -> bool:
    r, g, b = rgb
    if b < minimum:
        return False
    return (b - r) >= dominance and (b - g) >= dominance


def filter_blue_frames(
    frames: list[tuple[Path, float]],
    out_dir: Path,
    *,
    minimum: int,
    dominance: int,
) -> list[SlideRecord]:
    ensure_clean_dir(out_dir)
    kept: list[SlideRecord] = []
    for src, timestamp in frames:
        rgb = average_rgb(src)
        if rgb is None:
            continue
        if looks_blue(rgb, minimum=minimum, dominance=dominance):
            dest = out_dir / src.name
            shutil.copy2(src, dest)
            kept.append(SlideRecord(image=dest, timestamp=timestamp, rgb=rgb))
    return kept


def build_contact_sheet(images: list[Path], sheet_path: Path) -> None:
    if not images:
        return
    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    count = len(images)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    run_ffmpeg(
        [
            "-y",
            "-pattern_type",
            "glob",
            "-i",
            str(images[0].parent / "*.png"),
            "-filter_complex",
            f"tile={cols}x{rows}",
            str(sheet_path),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, default=Path("test.mp4"), help="Input video path")
    parser.add_argument("--raw-dir", type=Path, default=Path("slides_raw"), help="Temp folder for scene frames")
    parser.add_argument("--output-dir", type=Path, help="Override output folder (defaults per video name)")
    parser.add_argument("--scene-threshold", type=float, default=0.05, help="Scene detection sensitivity")
    parser.add_argument("--blue-min", type=int, default=80, help="Minimum blue channel value (0-255)")
    parser.add_argument("--blue-dominance", type=int, default=20, help="Required blue dominance over R/G")
    parser.add_argument(
        "--contact-sheet",
        type=Path,
        default=Path("slide_detector.jpeg"),
        help="Optional contact sheet output (set to '-' to skip)",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Where to write slide metadata (defaults to <video_basename>/slide_meta.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")

    base_name = args.video.stem
    target_root = args.output_dir if args.output_dir else Path(base_name)
    image_dir = target_root
    json_path = args.json_output if args.json_output else target_root / "slide_meta.json"

    raw_frames = extract_candidates(args.video, args.raw_dir, args.scene_threshold)
    timestamps = scene_timestamps(args.video, args.scene_threshold)

    frame_pairs = list(zip(raw_frames, timestamps))
    if len(raw_frames) != len(timestamps):
        print(
            "Warning: number of extracted frames and timestamps differ; pairing by shortest sequence",
        )
        frame_pairs = list(zip(raw_frames, timestamps))

    slides = filter_blue_frames(
        frame_pairs,
        image_dir,
        minimum=args.blue_min,
        dominance=args.blue_dominance,
    )

    if args.contact_sheet != Path("-"):
        sheet_path = args.contact_sheet if args.contact_sheet != Path("slide_detector.jpeg") else target_root / "slide_detector.jpeg"
        build_contact_sheet([record.image for record in slides], sheet_path)

    summary = {
        "video": str(args.video),
        "scene_threshold": args.scene_threshold,
        "blue_min": args.blue_min,
        "blue_dominance": args.blue_dominance,
        "slides": [
            {
                "image": str(record.image),
                "timestamp_seconds": record.timestamp,
                "average_rgb": list(record.rgb),
            }
            for record in slides
        ],
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(f"Detected {len(slides)} blue slide(s). Output folder: {image_dir}")
    if args.contact_sheet != Path("-"):
        print(f"Contact sheet: {sheet_path}")
    print(f"Metadata JSON: {json_path}")


if __name__ == "__main__":
    main()
