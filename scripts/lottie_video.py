#!/usr/bin/env python3
"""
lottie_video.py — Professional Lottie animation → video pipeline.

Renders Lottie animations to PNG frames via rlottie, adds AI voiceover,
and stitches into a final narrated MP4. Much higher quality than Manim.

Usage:  python3 scripts/lottie_video.py <video_name>
Setup:  pip install lottie rlottie pillow
Output: output/final.mp4

videos/<name>/
  scenes.py     — must define scenes() returning list of Animation objects
  narration.txt — one narration line per scene
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
    print(">>", " ".join(cmd))
    subprocess.run(cmd, check=True, capture_output=True)


def anim_to_json(anim):
    """Convert a lottie Animation object to JSON string."""
    try:
        from lottie.exporters import LottieJsonExporter
        return LottieJsonExporter(anim).export()
    except Exception:
        pass
    try:
        return json.dumps(anim.to_dict(), indent=None)
    except Exception:
        pass
    try:
        from lottie.utils import json_dumps
        return json_dumps(anim)
    except Exception:
        pass
    try:
        return json.dumps(anim)
    except Exception:
        raise RuntimeError("Cannot export Lottie Animation to JSON — "
                           "check lottie library version")


def render_frames(json_str, width, height, fps, duration_ms):
    """Render Lottie JSON to PNG frames via rlottie."""
    import rlottie
    from PIL import Image
    import io

    frames = []
    n_frames = max(1, int(duration_ms / 1000 * fps))
    out = rlottie.render(json_str, width=width, height=height)
    # rlottie.render may return fewer frames than requested
    for img in out:
        frames.append(img)
    return frames


def save_frames(frames, tmpdir):
    """Save PIL Images as numbered PNGs."""
    for i, img in enumerate(frames):
        img.save(os.path.join(tmpdir, f"frame_{i:04d}.png"))


def frames_to_video(frames_dir, n_frames, output_mp4, fps):
    """ffmpeg PNG sequence → MP4."""
    run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", f"scale={WIDTH}:{HEIGHT}",
        output_mp4,
    ])


def generate_voiceover(narration_lines, audio_dir, scene_durations):
    """Generate one voiceover MP3 per scene, padded to scene duration."""
    os.makedirs(audio_dir, exist_ok=True)
    for i, (line, dur) in enumerate(zip(narration_lines, scene_durations), start=1):
        raw_mp3 = os.path.join(audio_dir, f"raw_{i:02d}.mp3")
        fit_mp3 = os.path.join(audio_dir, f"fit_{i:02d}.mp3")
        run([
            "edge-tts", "--voice", VOICE, "--text", line,
            "--write-media", raw_mp3,
        ])
        # Get narration duration
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", raw_mp3],
            capture_output=True, text=True,
        )
        tts_dur = float(out.stdout.strip())
        target = dur / 1000.0  # scene duration in seconds
        if tts_dur > target:
            run(["ffmpeg", "-y", "-i", raw_mp3, "-t", f"{target:.3f}",
                 "-c", "copy", fit_mp3])
        else:
            pad = target - tts_dur
            run(["ffmpeg", "-y", "-i", raw_mp3,
                 "-af", f"apad=pad_dur={pad:.3f}",
                 "-t", f"{target:.3f}", fit_mp3])
    return audio_dir


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 lottie_video.py <video_name>")
    NAME = sys.argv[1]
    ROOT = Path(__file__).resolve().parent.parent
    VIDEO_DIR = ROOT / "videos" / NAME
    OUT_DIR = ROOT / "output"
    OUT_DIR.mkdir(exist_ok=True)

    # Load scenes
    scenes_py = VIDEO_DIR / "scenes.py"
    spec = importlib.util.spec_from_file_location(f"scenes_{NAME}", str(scenes_py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    anims = mod.scenes()  # must return list of (Animation, duration_ms)
    print(f"Loaded {len(anims)} scenes")

    # Load narration
    nar_lines = (VIDEO_DIR / "narration.txt").read_text().splitlines()
    nar_lines = [l.strip() for l in nar_lines if l.strip()]

    scene_vids = []
    for i, (anim, dur_ms) in enumerate(anims, start=1):
        print(f"\n--- Scene {i} ({dur_ms}ms) ---")
        json_str = anim_to_json(anim)
        with tempfile.TemporaryDirectory() as tmpdir:
            frames = render_frames(json_str, WIDTH, HEIGHT, FPS, dur_ms)
            if not frames:
                print("WARNING: no frames rendered, creating black frame")
                from PIL import Image
                frames = [Image.new("RGB", (WIDTH, HEIGHT), (28, 28, 28))]
            save_frames(frames, tmpdir)
            vid = str(OUT_DIR / f"scene_{i:02d}.mp4")
            frames_to_video(tmpdir, len(frames), vid, FPS)
            scene_vids.append(vid)

    # Voiceover
    audio_dir = str(OUT_DIR / "audio")
    scene_durs = [dur for _, dur in anims]
    generate_voiceover(nar_lines, audio_dir, scene_durs)

    # Concat scenes → full video
    vlist = str(OUT_DIR / "vlist.txt")
    alist = str(OUT_DIR / "alist.txt")
    with open(vlist, "w") as vf, open(alist, "w") as af:
        for vid in scene_vids:
            vf.write(f"file '{vid}'\n")
        for i in range(1, len(nar_lines) + 1):
            af.write(f"file '{audio_dir}/fit_{i:02d}.mp3'\n")

    full_vid = str(OUT_DIR / "full_video.mp4")
    full_aud = str(OUT_DIR / "full_audio.m4a")
    final   = str(OUT_DIR / "final.mp4")

    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", vlist,
         "-c", "copy", full_vid])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alist,
         "-c:a", "aac", "-b:a", "192k", full_aud])
    run(["ffmpeg", "-y", "-i", full_vid, "-i", full_aud,
         "-c:v", "copy", "-c:a", "aac", "-shortest", final])

    print(f"\n✅ DONE → {final}")


if __name__ == "__main__":
    main()
