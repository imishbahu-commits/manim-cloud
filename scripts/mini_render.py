#!/usr/bin/env python3
"""
mini_render.py — Lightweight frame renderer for our Lottie JSON format.
No rlottie, no lottie library — just Pillow. Renders ellipses with
position/scale/opacity animation and easing curves.

Usage: called by lottie_video.py
"""

from PIL import Image, ImageDraw
import math


def _bezier_ease(t, p0, p1, p2, p3):
    """Cubic bezier easing: given t in [0,1], compute eased value."""
    # Newton-Raphson approximation of cubic bezier inverse
    # Find parameter u where bezier(u) ≈ t, then compute bezier_y(u)
    cx = 3 * p0
    bx = 3 * (p2 - p0) - cx
    ax = 1 - cx - bx
    cy = 3 * p1
    by = 3 * (p3 - p1) - cy
    ay = 1 - cy - by

    def sample_x(u):
        return ((ax * u + bx) * u + cx) * u
    def sample_y(u):
        return ((ay * u + by) * u + cy) * u
    def sample_dx(u):
        return (3 * ax * u + 2 * bx) * u + cx

    # Newton's method to find u for given t
    u = t
    for _ in range(8):
        x = sample_x(u) - t
        if abs(x) < 1e-6:
            break
        dx = sample_dx(u)
        if abs(dx) < 1e-9:
            break
        u -= x / dx
    u = max(0, min(1, u))
    return sample_y(u)


def _interp_keyframes(keyframes, time_ms, default=None):
    """Interpolate keyframe values at given time. keyframes = list of {'t': ms, 's': [val]}."""
    if not keyframes:
        return default
    # Find surrounding keyframes
    prev = keyframes[0]
    for kf in keyframes:
        if kf["t"] > time_ms:
            break
        prev = kf
    else:
        return prev.get("s", default)

    # Find next keyframe
    nxt = None
    for kf in keyframes:
        if kf["t"] > prev["t"]:
            nxt = kf
            break
    if nxt is None:
        return prev.get("s", default)

    # Time interpolation
    t_range = nxt["t"] - prev["t"]
    if t_range <= 0:
        return prev.get("s", default)
    t_raw = (time_ms - prev["t"]) / t_range  # 0..1
    t_raw = max(0, min(1, t_raw))

    # Apply easing
    ease = None
    if "i" in prev and "o" in prev:
        # Cubic bezier control points
        ease = _bezier_ease(
            t_raw,
            prev["i"]["y"][0], prev["o"]["y"][0],
            prev["i"]["x"][0], prev["o"]["x"][0] if "x" in prev["o"] else prev["o"]["y"][0],
        )
    elif "i" in nxt:
        pass  # easing is on the outgoing of prev

    if ease is not None:
        t_eased = ease
    else:
        t_eased = t_raw

    # Interpolate values
    s0 = prev.get("s", default or [0])
    s1 = nxt.get("s", default or [0])
    result = []
    for a, b in zip(s0, s1):
        result.append(a + (b - a) * t_eased)
    return result


def _resolve_prop(prop, time_ms, default=None):
    """Resolve a property (static or animated) at a given time."""
    if isinstance(prop, dict):
        if prop.get("a", 0) == 1 and "k" in prop:
            return _interp_keyframes(prop["k"], time_ms, default)
        elif "k" in prop:
            val = prop["k"]
            return val if isinstance(val, list) else [val]
    elif isinstance(prop, (list, tuple)):
        return list(prop)
    return default or [0]


def render_frame(layers, width, height, time_ms):
    """Render a single frame at time_ms from a Lottie layers list."""
    img = Image.new("RGB", (width, height), (18, 26, 40))
    draw = ImageDraw.Draw(img, "RGBA")

    for layer in layers:
        # Check in/out points
        ip = layer.get("ip", 0)
        op = layer.get("op", 9999)
        if time_ms < ip or time_ms > op:
            continue

        layer_type = layer.get("ty", 4)

        if layer_type == 1:  # Solid layer
            sc = layer.get("sc", "#000000")
            r = int(sc[1:3], 16) if sc.startswith("#") else 0
            g = int(sc[3:5], 16)
            b = int(sc[5:7], 16)
            alpha = _resolve_prop(layer.get("ks", {}).get("o", {}), time_ms, [100])[0]
            draw.rectangle([0, 0, width, height], fill=(r, g, b, int(alpha * 2.55)))

        elif layer_type == 4:  # Shape layer
            ks = layer.get("ks", {})
            # Resolve layer transform
            l_pos = _resolve_prop(ks.get("p", {}), time_ms, [width/2, height/2])
            l_scale = _resolve_prop(ks.get("s", {}), time_ms, [100, 100])
            l_opacity = _resolve_prop(ks.get("o", {}), time_ms, [100])[0]

            for shape in layer.get("shapes", []):
                _draw_shape(draw, shape, l_pos, l_scale, l_opacity, time_ms)

    return img


def _draw_shape(draw, shape, parent_pos, parent_scale, parent_opacity, time_ms):
    """Draw a shape (ellipse or rect) with its own transform."""
    ty = shape.get("ty", "")

    if ty == "el":  # Ellipse
        # Resolve shape properties
        size = _resolve_prop(shape.get("s", {}), time_ms, [100, 100])
        pos = _resolve_prop(shape.get("p", {}), time_ms, [0, 0])
        o = _resolve_prop(shape.get("o", {}), time_ms, [100])[0]

        # Apply parent transform
        scale = parent_scale[0] / 100.0
        cx = parent_pos[0] + pos[0] * scale
        cy = parent_pos[1] + pos[1] * scale
        sw = size[0] * scale / 2.0
        sh = size[1] * scale / 2.0
        alpha = int(parent_opacity * o / 100 * 2.55)

        # Draw fill
        fl = shape.get("fl")
        if fl:
            c = fl.get("c", {}).get("k", [0, 0, 0, 1])
            fr = int(c[0] * 255)
            fg = int(c[1] * 255)
            fb = int(c[2] * 255)
            draw.ellipse([cx - sw, cy - sh, cx + sw, cy + sh],
                        fill=(fr, fg, fb, alpha))

        # Draw stroke
        st = shape.get("st")
        if st:
            c = st.get("c", {}).get("k", [1, 1, 1, 1])
            sr = int(c[0] * 255)
            sg = int(c[1] * 255)
            sb = int(c[2] * 255)
            sw_px = st.get("w", {}).get("k", 2)
            if isinstance(sw_px, list):
                sw_px = sw_px[0]
            draw.ellipse([cx - sw, cy - sh, cx + sw, cy + sh],
                        outline=(sr, sg, sb, alpha), width=max(1, int(sw_px * scale)))

    elif ty == "rc":  # Rectangle
        size = _resolve_prop(shape.get("s", {}), time_ms, [100, 100])
        pos = _resolve_prop(shape.get("p", {}), time_ms, [0, 0])
        o = _resolve_prop(shape.get("o", {}), time_ms, [100])[0]
        scale = parent_scale[0] / 100.0
        cx = parent_pos[0] + pos[0] * scale
        cy = parent_pos[1] + pos[1] * scale
        hw = size[0] * scale / 2.0
        hh = size[1] * scale / 2.0
        alpha = int(parent_opacity * o / 100 * 2.55)
        fl = shape.get("fl")
        if fl:
            c = fl.get("c", {}).get("k", [0, 0, 0, 1])
            draw.rectangle([cx - hw, cy - hh, cx + hw, cy + hh],
                          fill=(int(c[0]*255), int(c[1]*255), int(c[2]*255), alpha))

    # Handle group nesting
    if "it" in shape:
        for child in shape["it"]:
            _draw_shape(draw, child, parent_pos, parent_scale, parent_opacity, time_ms)
