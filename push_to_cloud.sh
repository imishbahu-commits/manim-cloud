#!/bin/bash
# =============================================================================
# push_to_cloud.sh — send a scene file to the cloud render farm
#
# Usage:
#   ./push_to_cloud.sh scenes/my_animation.py
#
# What it does:
#   copies your scene into scenes/, commits, and pushes to GitHub.
#   GitHub Actions then renders it for free and posts the MP4 as an
#   "artifact" on the Actions run page.
#
# First time only (see README):
#   git remote add origin https://github.com/YOUR_USERNAME/manim-cloud.git
# =============================================================================
set -e
cd "$(dirname "$0")"

SCENE="${1:-}"
if [ -z "$SCENE" ]; then
  echo "Usage: $0 <scene.py>" >&2
  echo "Example: $0 scenes/example.py" >&2
  exit 1
fi
if [ ! -f "$SCENE" ]; then
  echo "File not found: $SCENE" >&2
  exit 1
fi

cp "$SCENE" scenes/
git add scenes/
git commit -m "render: $(basename "$SCENE")"
git push origin main

echo ""
echo "✅ Pushed! Open GitHub in your browser:"
echo "   repo → Actions tab → 'Render Manim' run → Artifacts → manim-videos"
