"""
blender_scene.py — Build an OverSimplified-style 3D toon animation in Blender.
"WHY IT SUCKS TO BE A GLADIATOR" — 4 scenes:
  S1 Title card (push-in) → S2 Colosseum flyover → S3 Fight (dolly-in) → S4 "This is you"

Designed to run EITHER:
  A) inside Blender via MCP execute_code  (build + save .blend)
  B) directly:  blender -b -P blender_scene.py  (build + render segments)
"""

import bpy
import math
import os

OUT_DIR = os.environ.get("BLEND_OUT", "/tmp/blender_out")
FPS = 30
W, H = 1280, 720
SEGMENTS = [(1, 240), (241, 540), (541, 840), (841, 1080)]  # 8s, 10s, 10s, 8s

# ──────────────────────────── palette ────────────────────────────
SAND   = (0.82, 0.72, 0.55)
STONE  = (0.62, 0.58, 0.52)
SKIN   = (0.87, 0.69, 0.52)
TUNIC  = (0.55, 0.27, 0.15)
METAL  = (0.45, 0.45, 0.48)
GOLD   = (0.95, 0.78, 0.30)
RED    = (0.72, 0.16, 0.13)
WHITE  = (0.95, 0.95, 0.95)
DARK   = (0.09, 0.08, 0.10)


def mat(name, color, rough=0.8, metal=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.render.resolution_x = W
    bpy.context.scene.render.resolution_y = H
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.world = bpy.data.worlds.new("World")
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*DARK, 1.0)
        bg.inputs[1].default_value = 0.8


def add_prim(obj, name, col, **kw):
    obj.name = name
    obj.data.materials.append(mat(name + "_m", col))
    return obj


def sphere(name, radius, loc, col, subdiv=2):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc)
    return add_prim(bpy.context.object, name, col)


def cyl(name, radius, depth, loc, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.rotation_euler = rot
    return add_prim(obj, name, col)


def box(name, w, h, d, loc, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.scale = (w, h, d)
    obj.rotation_euler = rot
    return add_prim(obj, name, col)


def plane(name, size, loc, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    obj = bpy.context.object
    obj.rotation_euler = rot
    return add_prim(obj, name, col)


def hide_obj(obj, hide=True):
    obj.hide_render = hide
    obj.hide_viewport = hide


# ──────────────────────────── characters ────────────────────────────

def gladiator(name, loc, scale=1.0, tunic=TUNIC, helmet=1):
    """Simple stylized toon gladiator from primitives."""
    x, y, z = loc
    parts = []
    parts.append(cyl(f"{name}_legL", 0.12, 0.5, (x - 0.11, y, z + 0.25), SKIN))
    parts.append(cyl(f"{name}_legR", 0.12, 0.5, (x + 0.11, y, z + 0.25), SKIN))
    parts.append(cyl(f"{name}_body", 0.28, 0.6, (x, y, z + 0.72), tunic))
    parts.append(cyl(f"{name}_armL", 0.09, 0.5, (x - 0.30, y, z + 0.78), SKIN, rot=(0, 0.5, 0)))
    parts.append(cyl(f"{name}_armR", 0.09, 0.5, (x + 0.30, y, z + 0.78), SKIN, rot=(0, -0.5, 0)))
    parts.append(sphere(f"{name}_head", 0.19, (x, y, z + 1.18), SKIN, subdiv=1))
    if helmet:
        parts.append(sphere(f"{name}_helm", 0.22, (x, y, z + 1.22), METAL, subdiv=1))
        # Set metallic on the material after creation
        helm_obj = parts[-1]
        if helm_obj.data.materials:
            helm_obj.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.6
        parts.append(cyl(f"{name}_plume", 0.05, 0.35, (x, y, z + 1.42), RED))
    for p in parts:
        p.scale = (scale, scale, scale)
    return parts


def sword(name, loc, rot=(0, 0, 0)):
    blade = box(f"{name}_blade", 0.08, 1.1, 0.03, loc, (0.85, 0.87, 0.90), rot=rot)
    hilt = cyl(f"{name}_hilt", 0.04, 0.25, (loc[0], loc[1], loc[2] - 0.55), METAL)
    return [blade, hilt]


def shield(name, loc, col=RED):
    s = cyl(f"{name}", 0.32, 0.06, loc, col)
    return [s]


# ──────────────────────────── sets ────────────────────────────

def build_colosseum():
    """Big toon colosseum: sand floor, tiered walls, emperor box, crowd."""
    plane("sand", 30, (0, 0, 0.01), SAND)
    # tiered walls
    tiers = [(11.5, 1.6, 0.8), (12.8, 1.6, 2.4), (14.0, 1.6, 4.0)]
    for r, h, z in tiers:
        cyl(f"wall_{r}", r, h, (0, 0, z), STONE)
    # crowd heads on tiers
    head = sphere("crowd_tpl", 0.22, (0, 0, 0), SKIN)
    head.hide_render = True
    head.hide_viewport = True
    colors = [SKIN, (0.6, 0.4, 0.3), (0.9, 0.8, 0.7), (0.4, 0.3, 0.3)]
    for tier, (r, z) in enumerate([(11.5, 2.4), (12.8, 4.0), (14.0, 5.6)]):
        n = 26
        for i in range(n):
            ang = 2 * math.pi * i / n
            c = head.copy()
            c.data = head.data.copy()
            c.data.materials.clear()
            c.data.materials.append(mat(f"crowd_{tier}_{i}", colors[i % 4]))
            c.location = (r * math.cos(ang), r * math.sin(ang), z)
            bpy.context.collection.objects.link(c)
    # emperor box
    box("emperor_box", 2.6, 1.8, 2.2, (8.5, 0, 1.2), STONE)
    cyl("emperor_col1", 0.18, 3.0, (7.2, 0, 3.0), STONE)
    cyl("emperor_col2", 0.18, 3.0, (9.8, 0, 3.0), STONE)
    box("emperor_roof", 3.4, 2.6, 0.5, (8.5, 0, 4.4), RED)
    # emperor figure
    cyl("emperor_body", 0.25, 0.6, (8.5, 0, 1.9), WHITE)
    sphere("emperor_head", 0.17, (8.5, 0, 2.6), SKIN)
    # gates
    box("gate_l", 0.6, 1.2, 2.2, (-8.5, 0, 1.1), (0.35, 0.3, 0.26))
    box("gate_r", 0.6, 1.2, 2.2, (8.5, 0, 1.1), (0.35, 0.3, 0.26))


def build_scene_sets():
    # S2/S3 characters on sand
    build_colosseum()
    g1 = gladiator("g1", (-2.5, 0, 0), tunic=TUNIC)
    g2 = gladiator("g2", (2.5, 0, 0), tunic=(0.25, 0.35, 0.45), helmet=1)
    sw = sword("g1sword", (-2.5, -0.15, 0.9), rot=(0, 0, 0))
    sh = shield("g2shield", (2.35, -0.2, 0.9))
    # S4: hero character + bubble
    hero = gladiator("hero", (0, -4, 0), tunic=(0.35, 0.45, 0.25))
    s4_sword = sword("herosword", (0, -4.2, 0.9))
    bubble = sphere("bubble", 0.9, (1.6, -4, 2.0), WHITE, subdiv=1)
    bubble.scale = (1.3, 1.0, 0.7)
    tail = cyl("bubble_tail", 0.15, 0.6, (1.0, -4, 1.3), WHITE, rot=(0.8, 0, 0))
    return [g1, g2, sw, sh]


def add_text(name, body, loc, size=1.0, color=GOLD, depth=0.08):
    bpy.ops.object.text_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.extrude = depth
    obj.data.size = size
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    if obj.data.materials:
        obj.data.materials[0] = mat(name + "_m", color, rough=0.4, metal=0.4)
    else:
        obj.data.materials.append(mat(name + "_m", color, rough=0.4, metal=0.4))
    return obj


def set_lighting():
    bpy.ops.object.light_add(type="SUN", location=(8, -10, 12))
    sun = bpy.context.object
    sun.name = "sun"
    sun.data.energy = 4.0
    sun.data.angle = 0.5
    sun.rotation_euler = (0.7, -0.4, -0.3)
    bpy.ops.object.light_add(type="AREA", location=(0, 0, 8))
    fill = bpy.context.object
    fill.name = "fill"
    fill.data.energy = 60.0
    fill.data.size = 6


def cam(name, loc, rot, lens=45):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = name
    cam.rotation_euler = rot
    cam.data.lens = lens
    return cam


def kf(obj, frame, data_path, value):
    """Set value + keyframe."""
    if data_path == "location":
        obj.location = value
    elif data_path == "rotation_euler":
        obj.rotation_euler = value
    elif data_path == "scale":
        obj.scale = value
    obj.keyframe_insert(data_path=data_path, frame=frame)


def build_title_cam(empty_holder=None):
    """Camera for S1: slow push-in on title text."""
    c = cam("cam_title", (0, -8, 1.2), (math.radians(88), 0, 0), lens=50)
    kf(c, 1, "location", (0, -8, 1.2))
    kf(c, 240, "location", (0, -4.5, 1.2))
    return c


def build_colosseum_cam():
    """Orbit camera for S2 flyover."""
    empty = bpy.data.objects.new("orbit_center", None)
    bpy.context.collection.objects.link(empty)
    empty.location = (0, 0, 2.2)
    c = cam("cam_colosseum", (0, -16, 6), (math.radians(75), 0, 0), lens=40)
    c.parent = empty
    kf(empty, 241, "rotation_euler", (0, 0, math.radians(-40)))
    kf(empty, 540, "rotation_euler", (0, 0, math.radians(60)))
    return c


def build_fight_cam():
    """Dolly-in on the two gladiators."""
    c = cam("cam_fight", (0, -9, 1.6), (math.radians(82), 0, 0), lens=50)
    kf(c, 541, "location", (0, -9, 1.6))
    kf(c, 840, "location", (0, -5.2, 1.55))
    return c


def build_hero_cam():
    """Slow push toward hero + bubble."""
    c = cam("cam_hero", (0, -9.5, 1.4), (math.radians(85), 0, 0), lens=55)
    kf(c, 841, "location", (0, -9.5, 1.4))
    kf(c, 1080, "location", (0, -7.0, 1.4))
    return c


# ──────────────────────────── visibility per segment ────────────────────────────

def segment_visibility(segments):
    """Hide objects whose names belong to other segments' sets."""
    s1_names = {"cam_title", "title_text", "subtitle_text", "title_bg"}
    s2_names = {"sand", "wall_11.5", "wall_12.8", "wall_14.0", "emperor_box",
                "emperor_col1", "emperor_col2", "emperor_roof", "emperor_body",
                "emperor_head", "gate_l", "gate_r", "sun", "fill"}
    s3_names = {"g1", "g2", "g1sword", "g2shield"}
    s4_names = {"hero", "herosword", "bubble", "bubble_tail", "this_text", "you_text"}

    for obj in bpy.data.objects:
        if obj.name.startswith("crowd_") or obj.name == "crowd_tpl":
            continue  # crowd visible in colosseum scenes
        nm = obj.name
        seg = None
        if any(nm.startswith(p) for p in ("g1", "g2", "g1sword", "g2shield")):
            seg = 2
        elif any(nm.startswith(p) for p in ("hero", "herosword", "bubble")):
            seg = 3
        elif nm in ("cam_title", "title_text", "subtitle_text", "title_bg"):
            seg = 0
        elif nm.startswith(("wall", "sand", "emperor", "gate", "sun", "fill")):
            seg = 1
        if seg is not None:
            show_from = segments[seg][0]
            show_to = segments[seg][1]
            if seg > 0:
                obj.hide_render = True
                obj.keyframe_insert("hide_render", frame=1)
                obj.keyframe_insert("hide_render", frame=show_from - 1)
                obj.hide_render = False
                obj.keyframe_insert("hide_render", frame=show_from)
                obj.keyframe_insert("hide_render", frame=show_to)
                obj.hide_render = True
                obj.keyframe_insert("hide_render", frame=show_to + 1)


# ──────────────────────────── build everything ────────────────────────────

def build_all():
    clear_scene()
    set_lighting()

    # S1 title
    box("title_bg", 16, 9, 0.1, (0, 0, 2.2), (0.10, 0.10, 0.14))
    t1 = add_text("title_text", "WHY IT SUCKS TO BE A", (0, 0, 3.4), size=1.1, color=GOLD)
    t2 = add_text("subtitle_text", "GLADIATOR", (0, 0, 2.4), size=1.7, color=RED)
    kf(t2, 1, "scale", (0.7, 0.7, 0.7))
    kf(t2, 60, "scale", (1.0, 1.0, 1.0))

    # S2 + S3
    build_scene_sets()
    # S2 idle animation: sword up-down wave
    sw = bpy.data.objects.get("g1sword")
    if sw:
        kf(sw, 241, "location", (-2.5, -0.15, 0.9))
        kf(sw, 390, "location", (-2.5, -0.15, 1.15))
        kf(sw, 540, "location", (-2.5, -0.15, 0.9))

    # S4 text
    add_text("this_text", "THIS IS YOU", (0, -4, 2.2), size=1.0, color=GOLD)
    add_text("you_text", "FIGHTING FOR YOUR LIFE", (0, -4, 1.5), size=0.55, color=WHITE)

    # cameras
    build_title_cam()
    build_colosseum_cam()
    build_fight_cam()
    build_hero_cam()
    bpy.context.scene.camera = bpy.data.objects["cam_title"]

    # visibility
    segment_visibility(SEGMENTS)

    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "scene.blend"))
    print("SCENE_BUILD_DONE →", os.path.join(OUT_DIR, "scene.blend"))
    return True


def render_segments():
    """Render each segment with its own camera → PNG sequences."""
    cams = ["cam_title", "cam_colosseum", "cam_fight", "cam_hero"]
    sc = bpy.context.scene
    sc.render.image_settings.file_format = "PNG"
    for i, (f0, f1) in enumerate(SEGMENTS):
        sc.camera = bpy.data.objects[cams[i]]
        sc.frame_start = f0
        sc.frame_end = f1
        sc.render.filepath = os.path.join(OUT_DIR, f"seg{i+1}", "frame_")
        print(f"RENDERING segment {i+1}: frames {f0}-{f1} cam {cams[i]}")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    import sys
    if "--render-only" in sys.argv:
        # Load existing .blend and render segments
        bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR, "scene.blend"))
        render_segments()
    elif "--build-only" in sys.argv:
        build_all()
    else:
        build_all()
        render_segments()
    print("ALL_RENDER_DONE")
