#!/usr/bin/env python3
"""
lottie_video.py — Lottie animation → video pipeline (zero API risk).
Accepts either:
  - lottie Animation objects (if lottie lib installed)
  - Pure JSON dicts from lottie_builder.py

Usage:  python3 scripts/lottie_video.py <video_name>
Output: output/final.mp4
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

VOICE = os.environ.get("VIDEO_VOICE", "en-US-ChristopherNeural")
WIDTH  = int(os.environ.get("VIDEO_WIDTH",  "1920"))
HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1080"))
FPS    = int(os.environ.get("VIDEO_FPS",    "30"))


def run(cmd):
    print(">>", " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDERR:", result.stderr[-500:])
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


def to_json(data):
    """Convert to JSON string — handles dicts, lottie objects, or raw JSON."""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return json.dumps(data, separators=(",", ":"))
    # Try lottie library export
    try:
        from lottie.exporters import LottieJsonExporter
        return LottieJsonExporter(data).export()
    except Exception:
        pass
    try:
        return json.dumps(data.to_dict(), separators=(",", ":"))
    except Exception:
        pass
    return json.dumps(data)


def render_scene_json(json_str, scene_idx, out_dir):
    """Render a Lottie JSON string to PNG frames, then to MP4 via custom renderer."""
    from mini_render import render_frame
    anim = json.loads(json_str)
    layers = anim.get("layers", [])
    fps = anim.get("fr", 30)
    total_frames = anim.get("op", 300)

    frames_dir = os.path.join(out_dir, f"frames_{scene_idx:02d}")
    os.makedirs(frames_dir, exist_ok=True)

    print(f"  Rendering scene {scene_idx}: {total_frames} frames @ {fps}fps...")
    for f in range(total_frames):
        time_ms = int(f * 1000 / fps)
        img = render_frame(layers, WIDTH, HEIGHT, time_ms)
        img.save(os.path.join(frames_dir, f"frame_{f:04d}.png"))
        if f % 50 == 0:
            print(f"    frame {f}/{total_frames}")
    print(f"  {total_frames} frames rendered")

    # ffmpeg → MP4
    vid = os.path.join(out_dir, f"scene_{scene_idx:02d}.mp4")
    run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        vid,
    ])
    return vid


def generate_voiceover(narration_lines, audio_dir, scene_durations_ms):
    """Generate AI voiceover per scene, padded to scene duration."""
    os.makedirs(audio_dir, exist_ok=True)
    for i, (line, dur_ms) in enumerate(zip(narration_lines, scene_durations_ms), start=1):
        raw = os.path.join(audio_dir, f"raw_{i:02d}.mp3")
        fit = os.path.join(audio_dir, f"fit_{i:02d}.mp3")
        run(["edge-tts", "--voice", VOICE, "--text", line, "--write-media", raw])
        tts_dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", raw],
            capture_output=True, text=True).stdout.strip())
        target = dur_ms / 1000.0
        if tts_dur > target:
            run(["ffmpeg", "-y", "-i", raw, "-t", f"{target:.3f}", "-c", "copy", fit])
        else:
            pad = target - tts_dur
            run(["ffmpeg", "-y", "-i", raw,
                 "-af", f"apad=pad_dur={pad:.3f}", "-t", f"{target:.3f}", fit])
    return audio_dir


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 lottie_video.py <video_name>")
    NAME = sys.argv[1]
    ROOT = Path(__file__).resolve().parent.parent
    OUT  = ROOT / "output"
    OUT.mkdir(exist_ok=True)

    # ── Load scenes ──
    scenes_py = ROOT / "videos" / NAME / "scenes.py"
    spec = importlib.util.spec_from_file_location(f"scenes_{NAME}", str(scenes_py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw = mod.scenes()  # list of (dict_or_anim, duration_ms)
    print(f"Loaded {len(raw)} scenes from {scenes_py.name}")

    # ── Load narration ──
    nar_path = ROOT / "videos" / NAME / "narration.txt"
    nar_lines = [l.strip() for l in nar_path.read_text().splitlines() if l.strip()]

    # ── Render each scene ──
    scene_vids = []
    durations = []
    for i, (data, dur) in enumerate(raw, start=1):
        json_str = to_json(data)
        vid = render_scene_json(json_str, i, str(OUT))
        scene_vids.append(vid)
        durations.append(dur)
        print(f"  Scene {i} done → {vid}")

    # ── Voiceover ──
    audio_dir = str(OUT / "audio")
    generate_voiceover(nar_lines, audio_dir, durations)

    # ── Concat scenes → full video ──
    vlist = str(OUT / "vlist.txt")
    alist = str(OUT / "alist.txt")
    with open(vlist, "w") as vf, open(alist, "w") as af:
        for v in scene_vids:
            vf.write(f"file '{v}'\n")
        for i in range(1, len(nar_lines) + 1):
            af.write(f"file '{audio_dir}/fit_{i:02d}.mp3'\n")

    full_vid = str(OUT / "full_video.mp4")
    full_aud = str(OUT / "full_audio.m4a")
    final    = str(OUT / "final.mp4")

    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", vlist,
         "-c", "copy", full_vid])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alist,
         "-c:a", "aac", "-b:a", "192k", full_aud])
    run(["ffmpeg", "-y", "-i", full_vid, "-i", full_aud,
         "-c:v", "copy", "-c:a", "aac", "-shortest", final])

    size = os.path.getsize(final)
    print(f"\n✅ DONE → {final} ({size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
