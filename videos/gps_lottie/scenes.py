"""
GPS explainer — Professional Lottie animation via pure JSON builder.
No lottie library needed for creation; only rlottie for rendering.
Smooth bezier easing, layered compositing, rich color palette.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from lottie_builder import (
    build_animation, ellipse, shape_layer, solid_layer,
    anim_transform, _kf, _kf_last,
    EASE_IN_OUT, SPRING, LINEAR, EASE_OUT,
)

# ──── Palette (dark theme, rich colors) ────
BG      = [0.071, 0.102, 0.157, 1]     # #121A28
BLUE    = [0.306, 0.659, 0.941, 1]     # #4EA8F0
GREEN   = [0.357, 0.769, 0.490, 1]     # #5BC47D
YELLOW  = [1.0,   0.843, 0.0,   1]     # #FFD700
WHITE   = [1, 1, 1, 1]
GRAY    = [0.333, 0.400, 0.478, 1]     # #556677
DIM_BG  = [0.118, 0.227, 0.373, 1]     # #1E3A5F


def _bg():
    return solid_layer("bg", "#121A28", opacity=100)


# ══════════════════════════════════════════════════════════
#  SCENE 1 — Title reveal with orbiting satellite (10s)
# ══════════════════════════════════════════════════════════
def scene1():
    dur = 10000
    layers = [_bg()]

    # Title circle — scales in from zero
    layers.append(shape_layer("title_circle", [
        ellipse(800, 800, fill=DIM_BG, stroke=BLUE, sw=3),
    ], transform=anim_transform(
        scale_kf=[_kf(0, [0, 0], EASE_IN_OUT), _kf(1500, [100, 100], EASE_IN_OUT)],
        pos=(960, 400),
    ), end=dur))

    # Satellite — orbits around center
    layers.append(shape_layer("satellite", [
        ellipse(24, 24, fill=YELLOW),
    ], transform=anim_transform(
        opacity_kf=[_kf(0, 0), _kf(600, 100)],
        pos_kf=[
            _kf(0,    [960, 340], EASE_IN_OUT),
            _kf(3000, [620, 320], EASE_IN_OUT),
            _kf(6000, [1300, 420], EASE_IN_OUT),
            _kf(9500, [960, 340], EASE_IN_OUT),
        ],
    ), end=dur))

    # Signal ring — expands and fades
    layers.append(shape_layer("signal_ring", [
        ellipse(24, 24, stroke=BLUE, sw=2),
    ], transform=anim_transform(
        pos=(960, 340),
        opacity_kf=[_kf(0, 0), _kf(1000, 60), _kf(3500, 0)],
        scale_kf=[_kf(1000, [100, 100], EASE_IN_OUT), _kf(3500, [600, 600], EASE_IN_OUT)],
    ), end=dur))

    # Second signal ring (offset)
    layers.append(shape_layer("signal_ring2", [
        ellipse(24, 24, stroke=BLUE, sw=2),
    ], transform=anim_transform(
        pos=(960, 340),
        opacity_kf=[_kf(0, 0), _kf(2000, 40), _kf(4500, 0)],
        scale_kf=[_kf(2000, [100, 100], EASE_IN_OUT), _kf(4500, [500, 500], EASE_IN_OUT)],
    ), end=dur))

    # Phone icon — slides up from bottom
    layers.append(shape_layer("phone", [
        ellipse(60, 90, fill=GRAY, stroke=BLUE, sw=3),
    ], transform=anim_transform(
        opacity_kf=[_kf(0, 0), _kf(3500, 100)],
        pos_kf=[_kf(2500, [960, 640], EASE_IN_OUT), _kf(4000, [960, 560], EASE_IN_OUT)],
        pos=(960, 560),
    ), end=dur))

    # Label text (simulated as dot for now — real text needs font embedding)
    layers.append(shape_layer("label", [
        ellipse(4, 4, fill=WHITE),
    ], transform=anim_transform(
        pos=(960, 700),
        opacity_kf=[_kf(0, 0), _kf(5000, 90)],
    ), end=dur))

    return build_animation(layers, duration_ms=dur)


# ══════════════════════════════════════════════════════════
#  SCENE 2 — Trilateration circles (12s)
# ══════════════════════════════════════════════════════════
def scene2():
    dur = 12000
    layers = [_bg()]

    satellites = [
        (420, 280, BLUE,  0),
        (1500, 300, GREEN, 2000),
        (960, 780, YELLOW, 4000),
    ]

    for sx, sy, col, delay in satellites:
        # Satellite dot — springs in
        layers.append(shape_layer(f"sat_{sx}_{sy}", [
            ellipse(22, 22, fill=col, stroke=col, sw=2),
        ], transform=anim_transform(
            pos=(sx, sy),
            opacity_kf=[_kf(delay, 0), _kf(delay + 600, 100)],
            scale_kf=[_kf(delay, [0, 0], SPRING), _kf(delay + 600, [100, 100], SPRING)],
        ), end=dur))

        # Expanding circle — ease-in-out
        layers.append(shape_layer(f"circle_{sx}_{sy}", [
            ellipse(20, 20, stroke=col, sw=3),
        ], transform=anim_transform(
            pos=(sx, sy),
            opacity_kf=[_kf(delay + 400, 0), _kf(delay + 800, 70)],
            scale_kf=[_kf(delay + 400, [100, 100], EASE_IN_OUT), _kf(delay + 3000, [1400, 1400], EASE_IN_OUT)],
        ), end=dur))

    return build_animation(layers, duration_ms=dur)


# ══════════════════════════════════════════════════════════
#  SCENE 3 — "That's you!" intersection marker (10s)
# ══════════════════════════════════════════════════════════
def scene3():
    dur = 10000
    layers = [_bg()]

    # Faint background circles
    for sx, sy, col in [(420, 280, BLUE), (1500, 300, GREEN), (960, 780, YELLOW)]:
        layers.append(shape_layer(f"bg_{sx}_{sy}", [
            ellipse(20, 20, stroke=col, sw=2),
        ], transform=anim_transform(
            pos=(sx, sy),
            opacity_kf=[_kf(0, 0), _kf(800, 35)],
            scale_kf=[_kf(0, [800, 800], EASE_IN_OUT)],
        ), end=dur))

    # Intersection dot — springs in
    layers.append(shape_layer("intersection", [
        ellipse(18, 18, fill=WHITE, stroke=WHITE, sw=4),
    ], transform=anim_transform(
        pos=(880, 440),
        opacity_kf=[_kf(800, 0), _kf(1500, 100)],
        scale_kf=[_kf(800, [0, 0], SPRING), _kf(1500, [100, 100], SPRING)],
    ), end=dur))

    # Pulse ring — expanding
    layers.append(shape_layer("pulse", [
        ellipse(18, 18, stroke=WHITE, sw=3),
    ], transform=anim_transform(
        pos=(880, 440),
        opacity_kf=[_kf(1800, 80), _kf(4000, 0)],
        scale_kf=[_kf(1800, [100, 100], EASE_IN_OUT), _kf(4000, [700, 700], EASE_IN_OUT)],
    ), end=dur))

    # Second pulse ring
    layers.append(shape_layer("pulse2", [
        ellipse(18, 18, stroke=BLUE, sw=2),
    ], transform=anim_transform(
        pos=(880, 440),
        opacity_kf=[_kf(2500, 60), _kf(5000, 0)],
        scale_kf=[_kf(2500, [100, 100], EASE_IN_OUT), _kf(5000, [900, 900], EASE_IN_OUT)],
    ), end=dur))

    # Arrow pointing down
    layers.append(shape_layer("arrow", [
        ellipse(8, 40, fill=WHITE),
    ], transform=anim_transform(
        pos=(880, 510),
        opacity_kf=[_kf(3500, 0), _kf(4200, 100)],
        pos_kf=[_kf(3500, [880, 440], EASE_IN_OUT), _kf(4200, [880, 520], EASE_IN_OUT)],
    ), end=dur))

    return build_animation(layers, duration_ms=dur)


def scenes():
    return [(scene1(), 10000), (scene2(), 12000), (scene3(), 10000)]
