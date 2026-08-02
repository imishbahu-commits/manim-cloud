#!/usr/bin/env python3
"""
render_all.py — find all Scene classes in a .py file and render them.
Avoids manim's interactive chooser (which hangs without a keyboard in CI).

Usage: python3 scripts/render_all.py scenes.py [media_dir] [--ql]
"""
import ast
import os
import subprocess
import sys


def find_scenes(script_path):
    """Parse a manim file and return all Scene subclass names."""
    tree = ast.parse(open(script_path, encoding="utf-8").read())
    scenes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [getattr(b, "id", "") for b in node.bases if isinstance(b, ast.Name)]
            if any("Scene" in b for b in bases):
                scenes.append(node.name)
    return scenes


def main():
    script = sys.argv[1]
    media_dir = sys.argv[2] if len(sys.argv) > 2 else "media"
    low_quality = "--ql" in sys.argv

    scenes = find_scenes(script)
    if not scenes:
        print(f"ERROR: no Scene classes found in {script}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(scenes)} scenes: {', '.join(scenes)}")
    cmd = [sys.executable, "-m", "manim", "-qm" if not low_quality else "-ql",
           script, *scenes, "--media_dir", media_dir]
    print(">>", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
