"""
lottie_builder.py — Build professional Lottie JSON animations using plain Python.
No dependency on the lottie library's internal API — pure JSON dicts.
Only runtime dependency for rendering: rlottie-python + pillow.
"""

import json


# ──────────────────────── Easing presets ────────────────────────
EASE_IN_OUT  = [0.42, 0, 0.58, 1]
EASE_OUT     = [0, 0, 0.58, 1]
EASE_IN      = [0.42, 0, 1, 1]
SPRING       = [0.34, 1.56, 0.64, 1]
LINEAR       = None
ELASTIC      = [0.36, 1.6, 0.5, 1]
BOUNCE       = [0.34, 1.5, 0.64, 1]


def _easing(ease):
    if ease is None:
        return {}
    return {"e": ease}


def _kf(t, val, ease=None, s=None, e=None):
    """Keyframe: time (ms), value, optional easing + start/end offsets."""
    d = {"t": t}
    if isinstance(val, list):
        d["s"] = val
    elif isinstance(val, (int, float)):
        d["s"] = [val]
    if s is not None or e is not None:
        d["i"] = {"x": [s[0] if s else 0.5], "y": [s[1] if s else 0.5]}
        d["o"] = {"x": [e[0] if e else 0.5], "y": [e[1] if e else 0.5]}
    elif ease:
        d["i"] = {"x": [ease[0]], "y": [ease[1]]}
        d["o"] = {"x": [ease[2]], "y": [ease[3]]}
    return d


def _kf_last(t):
    """End keyframe (no value)."""
    return {"t": t}


# ──────────────────────── Primitives ────────────────────────

def ellipse(w, h, cx=0, cy=0, fill=None, stroke=None, sw=0, opacity=100):
    d = {"ty": "el", "nm": "ellipse",
         "d": 1,
         "s": {"a": 0, "k": [w, h]},
         "p": {"a": 0, "k": [cx, cy]},
         "o": {"a": 0, "k": opacity}}
    if fill:
        d["fl"] = {"ty": "fl", "c": {"a": 0, "k": fill}, "o": {"a": 0, "k": opacity}, "r": 1}
    if stroke:
        d["st"] = {"ty": "st", "c": {"a": 0, "k": stroke},
                    "o": {"a": 0, "k": opacity},
                    "w": {"a": 0, "k": sw},
                    "lc": 1, "lj": 1}
    return d


def rect(w, h, rx=0, ry=0, fill=None, stroke=None, sw=0, opacity=100, cx=0, cy=0):
    d = {"ty": "rc", "nm": "rect",
         "d": 1,
         "s": {"a": 0, "k": [w, h]},
         "p": {"a": 0, "k": [cx, cy]},
         "r": {"a": 0, "k": rx},
         "o": {"a": 0, "k": opacity}}
    if fill:
        d["fl"] = {"ty": "fl", "c": {"a": 0, "k": fill}, "o": {"a": 0, "k": opacity}, "r": 1}
    if stroke:
        d["st"] = {"ty": "st", "c": {"a": 0, "k": stroke},
                    "o": {"a": 0, "k": opacity},
                    "w": {"a": 0, "k": sw}, "lc": 1, "lj": 1}
    return d


# ──────────────────────── Layers ────────────────────────

def solid_layer(name, color, w=1920, h=1080, opacity=100):
    return {
        "ty": 1, "nm": name,
        "sr": 1, "ks": _transform(opacity=opacity),
        "sw": w, "sh": h, "sc": color,
        "ip": 0, "op": 9999, "st": 0,
    }


def shape_layer(name, shapes, transform=None, start=0, end=9999):
    return {
        "ty": 4, "nm": name,
        "sr": 1,
        "ks": transform or _transform(),
        "shapes": shapes if isinstance(shapes, list) else [shapes],
        "ip": start, "op": end, "st": 0,
    }


# ──────────────────────── Transform ────────────────────────

def _transform(pos=(960, 540), scale=(100, 100), rot=0, opacity=100, anchor=(0, 0)):
    return {
        "o": {"a": 1, "k": [_kf(0, opacity)] + [_kf_last(9999)]},
        "r": {"a": 1, "k": [_kf(0, rot)] + [_kf_last(9999)]},
        "p": {"a": 1, "k": [_kf(0, list(pos))] + [_kf_last(9999)]},
        "a": {"a": 0, "k": list(anchor)},
        "s": {"a": 1, "k": [_kf(0, list(scale))] + [_kf_last(9999)]},
    }


def anim_transform(
    pos=None, pos_kf=None,
    scale=None, scale_kf=None,
    opacity=None, opacity_kf=None,
    rot_kf=None, duration=9999,
):
    t = _transform()
    if pos_kf:
        t["p"] = {"a": 1, "k": pos_kf + [_kf_last(duration)]}
    elif pos:
        t["p"] = {"a": 0, "k": list(pos)}
    if scale_kf:
        t["s"] = {"a": 1, "k": scale_kf + [_kf_last(duration)]}
    elif scale:
        t["s"] = {"a": 0, "k": list(scale)}
    if opacity_kf:
        t["o"] = {"a": 1, "k": opacity_kf + [_kf_last(duration)]}
    elif opacity is not None:
        t["o"] = {"a": 0, "k": opacity}
    if rot_kf:
        t["r"] = {"a": 1, "k": rot_kf + [_kf_last(duration)]}
    return t


# ──────────────────────── Assemble animation ────────────────────────

def build_animation(layers, width=1920, height=1080, fps=30, duration_ms=10000):
    """Build a complete Lottie JSON dict."""
    total_frames = int(duration_ms / 1000 * fps)
    for layer in layers:
        if "op" not in layer or layer["op"] >= 9999:
            layer["op"] = total_frames
    return {
        "v": "5.12.2",
        "fr": fps,
        "ip": 0,
        "op": total_frames,
        "w": width,
        "h": height,
        "nm": "animation",
        "ddd": 0,
        "assets": [],
        "layers": layers,
    }


def to_json(anim_dict):
    return json.dumps(anim_dict, separators=(",", ":"))
