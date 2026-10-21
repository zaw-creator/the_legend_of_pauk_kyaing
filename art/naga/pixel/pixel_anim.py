"""Render the naga's idle loop in the menu pose, frame by frame, in the toon pixel style.

    Blender -b -P pixel_anim.py -- <output folder> [frames=16]

Each frame rebuilds the naga from build_naga.py with small periodic changes, so every part (scales, spikes, hair)
follows the body:
- a slow wave runs along the coils, a little over 1 art pixel high (smaller would only flicker); the tail on the ground stays put;
- the neck and head bob and nod, and the jaw opens and closes a little;
- the mane, beard, barbels and tail tuft flow.
Every motion completes a whole number of cycles over the loop, so the last frame leads back into the first.
Writes f00_all.png, f00_front.png, f00_back.png ... at 480x270 (the menu's grid, before pixelizing).
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
NAGA = os.path.dirname(HERE)
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
FRAMES = int(ARGS[1]) if len(ARGS) > 1 else 16
SCALE = 4
COIL_BREATH = 5.0  # menu pixels (about 1.25 art pixels): just enough to read as motion, not as flicker
sys.path.insert(0, HERE)
import pixel_style  # noqa: E402

TAU = 2 * math.pi


def spine_length(g):
    pts = g["catmull"](g["SPINE"], 0.06)
    return sum((pts[i] - pts[i - 1]).length for i in range(1, len(pts)))


def animate_globals(g, t):
    """Per-frame values, set after build_naga.py is exec'd and before anything is built."""
    path = g["MENU_PATH_PX"]
    rest_len = spine_length(g)
    n = len(path)
    i_neck = n - len(g["_NECK"]) - 1
    ppu = g["MENU_PPU"]
    spine = []
    for i, (px, py, d) in enumerate(path):
        s = i / (n - 1)
        body = min(1.0, max(0.0, (s - 0.08) / 0.12))            # 0 on the tail lying on the ground
        neck = 0.0 if i < i_neck else (i - i_neck) / (n - 1 - i_neck)
        neck = neck * neck * (3 - 2 * neck)
        # A slow wave runs along the coils from the tail to the neck. Under one art pixel it only makes the scales
        # flicker ("boil") once pixelized, so COIL_BREATH stays above 1 art pixel (4 menu pixels) or is 0.
        dy = COIL_BREATH * body * (1 - neck) * math.sin(TAU * (t - s))
        dy += 9.0 * neck * math.sin(TAU * t)                           # head bob
        dx = 4.0 * neck * math.sin(TAU * t + 0.8)
        spine.append(((px + dx - 960) / ppu, -d, (540 - py - dy) / ppu))
    g["SPINE"] = spine
    g["SPIKE_SHIFT"] = spine_length(g) - rest_len  # dorsal spikes stay put along the still coils
    g["HEAD_PITCH"] = 4 + 2.5 * math.sin(TAU * t + 0.5)
    g["CREST_PUFF"] = 0.07 + 0.03 * math.sin(TAU * t)
    g["CREST_STANDOFF"] = 0.10 + 0.04 * math.sin(TAU * t - 0.9)
    g["TAIL_TUFT"] = [(ang + 9 * math.sin(TAU * (t - 0.15 * k)), ln, w, side)
                      for k, (ang, ln, w, side) in enumerate(g["TAIL_TUFT"])]


def animate_built(g, t):
    """Per-frame changes to parts after they are built."""
    g["jaw_root"].rotation_euler = (0, math.radians(27 + 3 * math.sin(TAU * t + math.pi)), 0)
    for k, ob in enumerate(sorted((o for o in bpy.data.objects if o.name.startswith("Beard")), key=lambda o: o.name)):
        ob.rotation_euler.y += math.radians(4 * math.sin(TAU * (t - 0.06 * k)))


def render_frame(f):
    t = f / FRAMES
    os.environ["NAGA_POSE"] = "menu"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    g = {"NAGA_LIVE": True, "__name__": "pixel_anim", "ANIM_T": t}
    exec(compile(open(os.path.join(NAGA, "build_naga.py")).read(), "build_naga.py", "exec"), g)
    animate_globals(g, t)
    g["assemble_all"]()
    g["setup_world"]()
    pixel_style.apply(g)
    animate_built(g, t)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.filter_size = 0.0
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
    g["setup_camera_and_lights"]((0.0, 0.0, 0.0), 1920 / g["MENU_PPU"], (1920 // SCALE, 1080 // SCALE))
    pixel_style.sun((-0.55, 0.45, -0.7), energy=2.6, color=(0.96, 0.9, 0.76))  # moonlight, as in the menu
    cam = sc.camera
    for name, (near, far) in (("all", (0.1, 200.0)), ("front", (0.1, 30.0)), ("back", (30.0, 200.0))):
        cam.data.clip_start, cam.data.clip_end = near, far
        sc.render.filepath = os.path.join(OUT, "f%02d_%s.png" % (f, name))
        bpy.ops.render.render(write_still=True)
    print("ANIM FRAME", f, "of", FRAMES, flush=True)


os.makedirs(OUT, exist_ok=True)
for f in range(FRAMES):
    render_frame(f)
print("ANIM DONE", FRAMES)
