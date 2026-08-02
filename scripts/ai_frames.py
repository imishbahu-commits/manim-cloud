"""
ai_frames.py — Generate OverSimplified-style illustration frames using
Stable Diffusion on Kaggle GPU (free 30h/week T4 GPU).

Pipeline:
1. Receive narration lines → break into scenes
2. For each scene: generate an illustration with AI
3. Apply Ken Burns camera moves (pan/zoom)
4. Export frame sequences for ffmpeg assembly

Usage (on Kaggle with T4 GPU):
  pip install diffusers transformers accelerate torch safetensors
  python ai_frames.py "Why It Sucks to Be a Gladiator"
"""

import json, os, subprocess, sys

# ──────────── Scene breakdown (from narration) ────────────
SCENE_PROMPTS = {
    "gladiator": [
        {
            "scene": 1,
            "narration": "Why it sucks to be a gladiator.",
            "prompt": "flat vector illustration, ancient roman colosseum wide establishing shot, "
                      "stone arena with sand floor, tiered seating filled with crowd, "
                      "emperor viewing box with red curtains, golden sunlight, "
                      "simple clean cartoon style, muted earth tones, thick black outlines, "
                      "overhead wide angle, digital art, no text",
            "camera": "push-in",
            "duration": 8,
        },
        {
            "scene": 2,
            "narration": "The colosseum. Thousands cheer as you enter the sand.",
            "prompt": "flat vector illustration, lone gladiator entering roman arena from dark gate, "
                      "back view silhouette, massive colosseum walls towering above, "
                      "sand floor, dramatic lighting from above, crowd silhouettes in stands, "
                      "muted earth tones, thick black outlines, simple cartoon style, "
                      "dramatic cinematic composition, digital art, no text",
            "camera": "pan-left",
            "duration": 10,
        },
        {
            "scene": 3,
            "narration": "Fighting to the death for the crowd's entertainment.",
            "prompt": "flat vector illustration, two gladiators facing each other in roman arena, "
                      "one with sword and shield, one with trident and net, "
                      "sand floor, dramatic low angle, crowd cheering in background, "
                      "muted earth tones with red accents, thick black outlines, "
                      "simple clean cartoon style, dynamic composition, digital art, no text",
            "camera": "dolly-in",
            "duration": 10,
        },
        {
            "scene": 4,
            "narration": "This is you. A slave with a sword. Fighting for your life.",
            "prompt": "flat vector illustration, close-up portrait of a roman gladiator, "
                      "worn leather helmet with red plume, determined expression, "
                      "simple dot eyes, thick black outlines, muted earth tones, "
                      "dark dramatic background, simple clean cartoon style, "
                      "emotional character portrait, digital art, no text",
            "camera": "push-in-slow",
            "duration": 8,
        },
    ],
}

STYLE_PREFIX = (
    "over simplified style, 2D flat vector art, thick uniform black outlines, "
    "solid color fills without gradients, simple character design, dot eyes, "
    "educational youtube animation style, "
)


def generate_frames_gpu(topic="gladiator"):
    """Generate illustration frames using Stable Diffusion (T4 GPU)."""
    try:
        import torch
        from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
    except ImportError:
        print("ERROR: diffusers not installed. Run: pip install diffusers transformers accelerate torch")
        sys.exit(1)

    print(f"Loading SDXL pipeline (GPU: {torch.cuda.is_available()})...")
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to("cuda")

    scenes = SCENE_PROMPTS.get(topic, SCENE_PROMPTS["gladiator"])
    all_frames = []
    os.makedirs("/tmp/ai_frames", exist_ok=True)

    for s in scenes:
        print(f"\nScene {s['scene']}: {s['narration'][:40]}...")
        full_prompt = STYLE_PREFIX + s["prompt"]
        # Generate 4 variations, pick best (highest CLIP score)
        # For speed: just generate 1 at 1280x720 (matching video)
        image = pipe(
            prompt=full_prompt,
            negative_prompt="text, letters, words, watermark, blurry, realistic, photograph, 3d render",
            width=1280,
            height=720,
            num_inference_steps=25,
            guidance_scale=7.5,
            generator=torch.Generator("cuda").manual_seed(42 + s["scene"]),
        ).images[0]
        path = f"/tmp/ai_frames/scene_{s['scene']:02d}.png"
        image.save(path)
        all_frames.append(path)
        print(f"  Saved: {path}")

    return all_frames, scenes


def ken_burns(input_img, output_dir, duration_sec, fps=30, camera="push-in"):
    """Apply Ken Burns (pan/zoom) effect to a still image → frame sequence."""
    os.makedirs(output_dir, exist_ok=True)
    total_frames = duration_sec * fps

    # Ken Burns transforms: scale starts/ends, position offset
    transforms = {
        "push-in":    {"start_scale": 1.0, "end_scale": 1.25, "dx": 0, "dy": -0.05},
        "push-in-slow": {"start_scale": 1.0, "end_scale": 1.15, "dx": 0, "dy": -0.03},
        "pan-left":   {"start_scale": 1.15, "end_scale": 1.15, "dx": 0.08, "dy": 0},
        "pan-right":  {"start_scale": 1.15, "end_scale": 1.15, "dx": -0.08, "dy": 0},
        "pull-out":   {"start_scale": 1.25, "end_scale": 1.0, "dx": 0, "dy": 0.05},
        "dolly-in":   {"start_scale": 1.0, "end_scale": 1.35, "dx": 0, "dy": -0.02},
    }
    t = transforms.get(camera, transforms["push-in"])

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", input_img,
        "-vf", (
            f"scale=8000:-1,"
            f"zoompan=z='if(eq(on,1),{t["start_scale"]},"
            f"min(zoom+(({t["end_scale"]}-{t["start_scale"]})/{total_frames}),{t["end_scale"]}))'"
            f":x='iw/2-(iw/zoom/2)+{t["dx"]}*iw*on/{total_frames}'"
            f":y='ih/2-(ih/zoom/2)+{t["dy"]}*ih*on/{total_frames}'"
            f":d={total_frames}:s=1280x720:fps={fps}"
        ),
        "-frames:v", str(total_frames),
        os.path.join(output_dir, "frame_%04d.png"),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Ken Burns {camera}: {total_frames} frames → {output_dir}")


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "gladiator"
    fps = 30
    out_root = "/tmp/ai_frames"
    os.makedirs(out_root, exist_ok=True)

    print(f"=== Generating AI frames for: {topic} ===")
    all_imgs, scenes = generate_frames_gpu(topic)

    # Apply Ken Burns to each scene
    for img_path, scene in zip(all_imgs, scenes):
        seg_dir = os.path.join(out_root, f"seg{scene['scene']}")
        print(f"\nKen Burns: scene {scene['scene']} ({scene['camera']}, {scene['duration']}s)")
        ken_burns(img_path, seg_dir, scene["duration"], fps, scene["camera"])

    # Save scene info for assembly
    with open(os.path.join(out_root, "scenes.json"), "w") as f:
        json.dump(scenes, f, indent=2)

    print(f"\n✅ All frames generated → {out_root}")
    print("Next: ffmpeg assembly + voiceover")


if __name__ == "__main__":
    main()
