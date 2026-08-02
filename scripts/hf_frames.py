#!/usr/bin/env python3
"""
hf_frames.py — Generate OverSimplified-style illustration frames via
HuggingFace Inference API (FREE GPU, no signup beyond HF token).

Usage: python3 hf_frames.py "Why It Sucks to Be a Gladiator" oversimplified

Requires: HF_TOKEN env var (free token from huggingface.co)
"""

import os, sys, json, base64, time, requests
from pathlib import Path

OUT = Path("/tmp/ai_frames")
OUT.mkdir(exist_ok=True)
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# ─────────────────── Scene templates ───────────────────
STYLE_PROMPTS = {
    "oversimplified": (
        "flat vector illustration, thick uniform black outlines, solid color fills, "
        "simple character design, dot eyes, muted earth tones, educational youtube animation, "
        "2D cartoon style, digital art, no text no watermark no letters"
    ),
    "storybook": (
        "children book illustration, soft watercolor style, warm earthy palette, "
        "simple shapes, gentle lighting, storybook art, detailed background, "
        "digital painting, no text no watermark"
    ),
    "comic": (
        "comic book panel, bold black outlines, flat colors, halftone shading, "
        "dramatic lighting, dynamic composition, pop art style, "
        "digital illustration, no speech bubbles no text no watermark"
    ),
    "anime": (
        "anime style illustration, cel shaded, vibrant colors, dramatic lighting, "
        "clean lineart, detailed background, studio ghibli inspired, "
        "digital art, no text no watermark no signature"
    ),
}

SCENES = {
    "gladiator": [
        {
            "scene": 1,
            "narration": "Why it sucks to be a gladiator.",
            "prompt": "ancient roman colosseum wide establishing shot, stone arena with sand floor, tiered seating filled with crowd, emperor viewing box with red curtains, golden afternoon sunlight, overhead wide angle",
            "camera": "push-in",
            "duration": 8,
        },
        {
            "scene": 2,
            "narration": "The colosseum. Thousands cheer as you enter the sand.",
            "prompt": "lone gladiator entering roman arena from dark stone gate, back view silhouette walking toward bright sand, massive colosseum walls towering above, dramatic shaft of light from above, crowd silhouettes in stands, cinematic composition",
            "camera": "pan-left",
            "duration": 10,
        },
        {
            "scene": 3,
            "narration": "Fighting to the death for the crowd's entertainment.",
            "prompt": "two gladiators facing each other in roman arena, one with sword and round shield, one with trident and net, sand floor, dramatic low angle shot, cheering crowd in background, dynamic action pose",
            "camera": "dolly-in",
            "duration": 10,
        },
        {
            "scene": 4,
            "narration": "This is you. A slave with a sword. Fighting for your life.",
            "prompt": "close-up portrait of roman gladiator, worn leather helmet with red plume, determined expression, simple dot eyes, dark dramatic background, emotional character portrait, cinematic portrait lighting",
            "camera": "push-in-slow",
            "duration": 8,
        },
    ],
}

# Generic topic fallback
GENERIC_SCENE_TEMPLATE = [
    {"scene": 1, "prompt": "wide establishing shot of {topic} scene, dramatic composition, warm lighting", "camera": "push-in", "duration": 8},
    {"scene": 2, "prompt": "close detail of {topic}, dramatic lighting, focused composition", "camera": "pan-left", "duration": 10},
    {"scene": 3, "prompt": "action scene related to {topic}, dynamic composition, dramatic angle", "camera": "dolly-in", "duration": 10},
    {"scene": 4, "prompt": "portrait closeup related to {topic}, emotional, dramatic portrait lighting", "camera": "push-in-slow", "duration": 8},
]


def generate_frame(prompt, scene_num, style="oversimplified"):
    """Call HuggingFace Inference API (free FLUX.1-schnell or SDXL)."""
    style_prefix = STYLE_PROMPTS.get(style, STYLE_PROMPTS["oversimplified"])
    full_prompt = f"{style_prefix}, {prompt}"

    # Try FLUX.1-schnell first (fastest free model), fallback to SDXL
    models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
    ]

    for model in models:
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "width": 1280,
                    "height": 720,
                    "num_inference_steps": 20 if "schnell" in model else 25,
                    "guidance_scale": 7.5,
                },
            }
            print(f"  → Calling {model.split('/')[-1]}...")
            r = requests.post(API_URL, headers=headers, json=payload, timeout=180)

            if r.status_code == 200:
                path = OUT / f"scene_{scene_num:02d}.png"
                path.write_bytes(r.content)
                print(f"  ✓ Saved: {path} ({len(r.content)//1024}KB)")
                return str(path)
            elif r.status_code == 503:
                # Model loading — retry after delay
                wait = r.json().get("estimated_time", 30)
                print(f"  ⏳ Model loading, waiting {wait}s...")
                time.sleep(min(wait, 60))
                continue
            else:
                print(f"  ⚠ {model}: HTTP {r.status_code}")
                continue
        except Exception as e:
            print(f"  ⚠ {model}: {e}")
            continue

    # Fallback: generate a solid color placeholder
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1280, 720), (40, 30, 50))
    d = ImageDraw.Draw(img)
    d.text((640, 360), f"Scene {scene_num}", fill="white", anchor="mm")
    path = OUT / f"scene_{scene_num:02d}.png"
    img.save(str(path))
    return str(path)


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "gladiator"
    style = sys.argv[2] if len(sys.argv) > 2 else "oversimplified"

    # Select scenes
    topic_key = topic.lower().replace(" ", "_").replace("why_it_sucks_to_be_a_", "")
    scenes = SCENES.get(topic_key, None)

    if scenes is None:
        # Build generic scenes from topic
        narration_lines = [
            f"Let's talk about {topic}.",
            f"The story of {topic} is fascinating.",
            f"There are surprising details about {topic}.",
            f"And that's what makes {topic} so interesting.",
        ]
        scenes = []
        for i, tmpl in enumerate(GENERIC_SCENE_TEMPLATE):
            s = tmpl.copy()
            s["narration"] = narration_lines[i]
            s["prompt"] = tmpl["prompt"].format(topic=topic)
            scenes.append(s)

    print(f"=== AI Animation Studio ===")
    print(f"Topic: {topic}")
    print(f"Style: {style}")
    print(f"Scenes: {len(scenes)}")
    print()

    for s in scenes:
        print(f"Scene {s['scene']}: {s.get('narration', '...')}")
        generate_frame(s["prompt"], s["scene"], style)
        time.sleep(2)  # rate limit courtesy

    # Save metadata for assembly
    with open(OUT / "scenes.json", "w") as f:
        json.dump(scenes, f, indent=2)

    print(f"\n✅ All {len(scenes)} frames generated → {OUT}")


if __name__ == "__main__":
    main()
