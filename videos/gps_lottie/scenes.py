"""
GPS explainer — Professional Lottie animation (much higher quality than Manim).
Defines scenes() returning list of (Animation, duration_ms) tuples.
Uses lottie-python: smooth bezier easing, gradient fills, layered compositing.
"""

from lottie.objects import Animation, ShapeLayer, Group, Ellipse, Fill, Stroke
from lottie.objects.transform import Transform, Keyframe
from lottie import Point, Color

# Professional color palette (dark theme, rich colors)
BG       = Color(0x12, 0x1A, 0x28)
BLUE     = Color(0x4E, 0xA8, 0xF0)
GREEN    = Color(0x5B, 0xC4, 0x7D)
YELLOW   = Color(0xFF, 0xD7, 0x00)
WHITE    = Color(0xFF, 0xFF, 0xFF)
GRAY     = Color(0x55, 0x66, 0x77)
DIM_BLUE = Color(0x1E, 0x3A, 0x5F)


def _ease_in_out():
    """Cubic bezier ease-in-out."""
    return "cubic-bezier(0.42, 0, 0.58, 1)"


def _spring():
    """Spring / elastic easing."""
    return "cubic-bezier(0.34, 1.56, 0.64, 1)"


def make_bg_layer():
    """Full-screen dark background."""
    layer = ShapeLayer()
    layer.name = "background"
    rect = Group()
    r = Ellipse()
    r.size = Point(1, 1)
    r.position = Point(960, 540)
    r.add_style(Fill(color=BG))
    r.add_style(Stroke(color=BG, width=2200))
    rect.add_shape(r)
    layer.add_shape(rect)
    layer.transform = Transform()
    layer.transform.opacity.value = 100
    return layer


def scene1_title():
    """Scene 1: Title reveal with smooth fade-in + satellite orbit."""
    anim = Animation(width=1920, height=1080, framerate=30, duration=10000)
    anim.add_layer(make_bg_layer())

    # ---- Main title circle background ----
    title_layer = ShapeLayer()
    title_layer.name = "title_back"
    circle = Ellipse()
    circle.size = Point(1, 1)
    circle.position = Point(960, 400)
    circle.add_style(Fill(color=DIM_BLUE))
    circle.add_style(Stroke(color=BLUE, width=3))
    title_layer.add_shape(circle)
    t = title_layer.transform = Transform()
    t.position.value = Point(960, 400)
    t.scale.value = Point(0, 0)
    t.scale.add_keyframe(0, Point(0, 0), _ease_in_out())
    t.scale.add_keyframe(1200, Point(100, 100), _ease_in_out())
    anim.add_layer(title_layer)

    # ---- Orbiting satellite dot ----
    sat_layer = ShapeLayer()
    sat_layer.name = "satellite"
    sat = Ellipse()
    sat.size = Point(24, 24)
    sat.position = Point(960, 340)
    sat.add_style(Fill(color=YELLOW))
    sat.add_style(Stroke(color=YELLOW, width=2))
    sat_layer.add_shape(sat)
    st = sat_layer.transform = Transform()
    st.opacity.value = 0
    st.opacity.add_keyframe(0, 0, "linear")
    st.opacity.add_keyframe(800, 100, "linear")
    st.position.value = Point(960, 340)
    st.position.add_keyframe(0,    Point(960, 340), _ease_in_out())
    st.position.add_keyframe(3000, Point(620, 320), _ease_in_out())
    st.position.add_keyframe(6000, Point(1300, 420), _ease_in_out())
    st.position.add_keyframe(9500, Point(960, 340), _ease_in_out())
    anim.add_layer(sat_layer)

    # ---- Signal ring expansion ----
    ring_layer = ShapeLayer()
    ring_layer.name = "signal"
    ring = Ellipse()
    ring.size = Point(24, 24)
    ring.position = Point(960, 340)
    ring.add_style(Stroke(color=BLUE, width=2))
    ring_layer.add_shape(ring)
    rt = ring_layer.transform = Transform()
    rt.opacity.value = 0
    rt.opacity.add_keyframe(1000, 60, "linear")
    rt.opacity.add_keyframe(3000, 0, "linear")
    rt.scale.value = Point(100, 100)
    rt.scale.add_keyframe(1000, Point(100, 100), _ease_in_out())
    rt.scale.add_keyframe(3000, Point(600, 600), _ease_in_out())
    anim.add_layer(ring_layer)

    # ---- Phone icon (rounded rect) ----
    phone_layer = ShapeLayer()
    phone_layer.name = "phone"
    p = Ellipse()
    p.size = Point(60, 90)
    p.position = Point(960, 560)
    p.add_style(Fill(color=GRAY))
    p.add_style(Stroke(color=BLUE, width=3))
    phone_layer.add_shape(p)
    pt = phone_layer.transform = Transform()
    pt.opacity.value = 0
    pt.opacity.add_keyframe(2500, 0, "linear")
    pt.opacity.add_keyframe(4000, 100, _ease_in_out())
    pt.position.value = Point(960, 560)
    pt.position.add_keyframe(2500, Point(960, 640), _ease_in_out())
    pt.position.add_keyframe(4000, Point(960, 560), _ease_in_out())
    anim.add_layer(phone_layer)

    return anim, 10000


def scene2_trilateration():
    """Scene 2: Three satellites + expanding trilateration circles."""
    anim = Animation(width=1920, height=1080, framerate=30, duration=12000)
    anim.add_layer(make_bg_layer())

    satellites = [
        (420, 280, BLUE),
        (1500, 300, GREEN),
        (960, 780, YELLOW),
    ]

    for idx, (sx, sy, color) in enumerate(satellites):
        delay = idx * 1800

        # Satellite dot
        sat_layer = ShapeLayer()
        sat_layer.name = f"sat_{idx}"
        dot = Ellipse()
        dot.size = Point(22, 22)
        dot.position = Point(sx, sy)
        dot.add_style(Fill(color=color))
        dot.add_style(Stroke(color=color, width=2))
        sat_layer.add_shape(dot)
        dt = sat_layer.transform = Transform()
        dt.opacity.value = 0
        dt.opacity.add_keyframe(delay, 0, "linear")
        dt.opacity.add_keyframe(delay + 600, 100, _ease_in_out())
        dt.scale.value = Point(0, 0)
        dt.scale.add_keyframe(delay, Point(0, 0), _spring())
        dt.scale.add_keyframe(delay + 600, Point(100, 100), _spring())
        anim.add_layer(sat_layer)

        # Expanding trilateration circle
        circle_layer = ShapeLayer()
        circle_layer.name = f"circle_{idx}"
        circ = Ellipse()
        circ.size = Point(20, 20)
        circ.position = Point(sx, sy)
        circ.add_style(Stroke(color=color, width=3, opacity=50))
        circle_layer.add_shape(circ)
        ct = circle_layer.transform = Transform()
        ct.opacity.value = 0
        ct.opacity.add_keyframe(delay + 400, 0, "linear")
        ct.opacity.add_keyframe(delay + 800, 70, _ease_in_out())
        ct.scale.value = Point(100, 100)
        ct.scale.add_keyframe(delay + 400, Point(100, 100), _ease_in_out())
        ct.scale.add_keyframe(delay + 2400, Point(1400, 1400), _ease_in_out())
        anim.add_layer(circle_layer)

    return anim, 12000


def scene3_you():
    """Scene 3: Intersection marker with pulse + 'That\\'s you!' reveal."""
    anim = Animation(width=1920, height=1080, framerate=30, duration=10000)
    anim.add_layer(make_bg_layer())

    # ---- Faint circles (background trilateration) ----
    bg_circles = ShapeLayer()
    bg_circles.name = "bg_circles"
    for (sx, sy), col in [
        ((420, 280), BLUE), ((1500, 300), GREEN), ((960, 780), YELLOW)
    ]:
        c = Ellipse()
        c.size = Point(20, 20)
        c.position = Point(sx, sy)
        c.add_style(Stroke(color=col, width=2, opacity=30))
        bg_circles.add_shape(c)
    bt = bg_circles.transform = Transform()
    bt.opacity.value = 0
    bt.opacity.add_keyframe(0, 0, "linear")
    bt.opacity.add_keyframe(1000, 100, _ease_in_out())
    anim.add_layer(bg_circles)

    # ---- Intersection dot ----
    dot_layer = ShapeLayer()
    dot_layer.name = "intersection"
    d = Ellipse()
    d.size = Point(18, 18)
    d.position = Point(880, 440)
    d.add_style(Fill(color=WHITE))
    d.add_style(Stroke(color=WHITE, width=4))
    dot_layer.add_shape(d)
    dt = dot_layer.transform = Transform()
    dt.opacity.value = 0
    dt.opacity.add_keyframe(800, 0, "linear")
    dt.opacity.add_keyframe(1500, 100, _ease_in_out())
    dt.scale.value = Point(0, 0)
    dt.scale.add_keyframe(800, Point(0, 0), _spring())
    dt.scale.add_keyframe(1500, Point(100, 100), _spring())
    anim.add_layer(dot_layer)

    # ---- Pulse ring ----
    pulse = ShapeLayer()
    pulse.name = "pulse"
    pr = Ellipse()
    pr.size = Point(18, 18)
    pr.position = Point(880, 440)
    pr.add_style(Stroke(color=WHITE, width=3))
    pulse.add_shape(pr)
    pt = pulse.transform = Transform()
    pt.opacity.value = 0
    pt.opacity.add_keyframe(1800, 80, "linear")
    pt.opacity.add_keyframe(3500, 0, "linear")
    pt.scale.value = Point(100, 100)
    pt.scale.add_keyframe(1800, Point(100, 100), _ease_in_out())
    pt.scale.add_keyframe(3500, Point(700, 700), _ease_in_out())
    anim.add_layer(pulse)

    return anim, 10000


def scenes():
    """Return all scenes for the GPS explainer."""
    return [scene1_title(), scene2_trilateration(), scene3_you()]
