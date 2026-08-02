#!/usr/bin/env python3
"""
build_video.py — the video assembler for the AI Video Studio.

Inputs (for a video named <NAME>):
  videos/<NAME>/scenes.py       — manim scenes (one class per scene)
  videos/<NAME>/narration.txt   — one narration line per scene

Steps:
  1. For each scene MP4, generate AI voiceover for its narration line
     (Microsoft neural voices via edge-tts — free, no API key).
  2. Pad/trim each narration to exactly match its scene duration.
  3. Concatenate scenes -> video track, narration -> audio track.
  4. Mux both tracks into output/final.mp4.

Usage: python3 scripts/build_video.py <NAME>
"""

import glob
import os
import re
import subprocess
import sys

NAME = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(ROOT, "videos", NAME)
OUT_DIR = os.path.join(ROOT, "output")
VOICE = os.environ.get("VIDEO_VOICE", "en-US-ChristopherNeural")
QUALITY_DIRS = ["720p30", "480p15", "1080p60"]  # manim media layout

os.makedirs(OUT_DIR, exist_ok=True)


def run(cmd):
    print(">>", " ".join(cmd))
    subprocess.run(cmd, check=True)


def find_scene_videos():
    """Return scene mp4s in manim's media folder, in scene order."""
    vids = []
    for q in QUALITY_DIRS:
        vids = sorted(glob.glob(os.path.join(ROOT, "media", "videos", NAME, q, "*.mp4")))
        vids += sorted(glob.glob(os.path.join(ROOT, "media", "videos", "scenes", q, "*.mp4")))
        if vids:
            break
    if not vids:
        vids = sorted(glob.glob(os.path.join(ROOT, "media", "**", "*.mp4"), recursive=True))
        vids = [v for v in vids if "/partial" not in v]
    if not vids:
        sys.exit("ERROR: no scene videos found")
    return vids


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def main():
    naration_path = os.path.join(VIDEO_DIR, "narration.txt")
    with open(naration_path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    scene_vids = find_scene_videos()
    print(f"Scenes found: {len(scene_vids)} | Narration lines: {len(lines)}")
    if len(lines) != len(scene_vids):
        print(f"WARNING: count mismatch — using {min(len(lines), len(scene_vids))} of each")

    audio_dir = os.path.join(OUT_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    # 1. Generate one voiceover per scene
    for i, (vid, line) in enumerate(zip(scene_vids, lines), start=1):
        mp3 = os.path.join(audio_dir, f"narr_{i:02d}.mp3")
        print(f"--- Voiceover {i}: {line!r}")
        run(["edge-tts", "--voice", VOICE, "--text", line, "--write-media", mp3])

    # 2. Pad each narration to its scene length; collect concat lists
    vlist = os.path.join(OUT_DIR, "video_list.txt")
    alist = os.path.join(OUT_DIR, "audio_list.txt")
    with open(vlist, "w") as vf, open(alist, "w") as af:
        for i, vid in enumerate(scene_vids, start=1):
            mp3 = os.path.join(audio_dir, f"narr_{i:02d}.mp3")
            if not os.path.exists(mp3):
                continue
            d_v = duration(vid)
            d_a = duration(mp3)
            target = os.path.join(audio_dir, f"fit_{i:02d}.mp3")
            if d_a > d_v:
                # narration longer than scene -> trim to scene length
                run(["ffmpeg", "-y", "-i", mp3, "-t", f"{d_v:.3f}", "-c", "copy", target])
            elif d_a < d_v:
                # narration shorter -> pad with silence to scene length
                pad = f"{d_v - d_a:.3f}"
                run(["ffmpeg", "-y", "-i", mp3, "-af", f"apad=pad_dur={pad}",
                     "-t", f"{d_v:.3f}", target])
            else:
                run(["cp", mp3, target])
            vf.write(f"file '{vid}'\n")
            af.write(f"file '{target}'\n")

    # 3. Concatenate video track and audio track
    full_video = os.path.join(OUT_DIR, "full_video.mp4")
    full_audio = os.path.join(OUT_DIR, "full_audio.m4a")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", vlist,
         "-c", "copy", full_video])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alist,
         "-c:a", "aac", "-b:a", "192k", full_audio])

    # 4. Mux narration over the video
    final = os.path.join(OUT_DIR, "final.mp4")
    run(["ffmpeg", "-y", "-i", full_video, "-i", full_audio,
         "-c:v", "copy", "-c:a", "aac", "-shortest", final])
    print(f"\nDONE -> {final} ({duration(final):.1f}s)")


if __name__ == "__main__":
    main()
