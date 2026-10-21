"""Render the naga in the toon pixel style, built fresh from build_naga.py (never touches art/naga/naga.blend).

    Blender -b -P pixel_render.py -- <output folder> menu|sprites

menu:    the guardian pose at a quarter of the menu's resolution: menu_front.png / menu_back.png (480x270, the parts
         in front of / behind the palace) and menu_marks.json, the same split the full-resolution menu uses.
sprites: the hero pose as small game sprites: full body 320x213, head-and-neck 192x144, head 3/4 160x120.
"""
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
NAGA = os.path.dirname(HERE)
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
MODE = ARGS[1] if len(ARGS) > 1 else "menu"
SCALE = 4  # menu pixels per sprite pixel: 1920x1080 -> 480x270

os.environ["NAGA_POSE"] = "menu" if MODE == "menu" else "hero"
bpy.ops.wm.read_factory_settings(use_empty=True)
g = {"NAGA_LIVE": True, "__name__": "pixel_menu"}
exec(compile(open(os.path.join(NAGA, "build_naga.py")).read(), "build_naga.py", "exec"), g)
g["assemble_all"]()
g["setup_world"]()
sys.path.insert(0, HERE)
import pixel_style  # noqa: E402

pixel_style.apply(g)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.filter_size = 0.0
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
os.makedirs(OUT, exist_ok=True)
sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
if MODE == "sprites":
    head = g["head_root"].matrix_world
    shots = (("sprite_full_320.png", (-0.2, 0.0, 2.2), 12.5, (320, 213), {}),
             ("sprite_bust_192.png", head @ Vector((-0.25, 0, 0.10)), 5.2, (192, 144), {}),
             ("sprite_head3q_160.png", head @ Vector((0.40, 0, 0.30)), 4.2, (160, 120),
              {"key_from": (9, -4, 8), "cam_offset": (16.0, -24.0, 6.0)}))
    for name, center, ortho, res, kw in shots:
        g["setup_camera_and_lights"](center, ortho, res, **kw)
        pixel_style.sun((0.55, 0.45, -0.7), energy=3.2)  # game-sprite light from the top left
        sc.render.filepath = os.path.join(OUT, name)
        bpy.ops.render.render(write_still=True)
    print("PIXEL SPRITES DONE")
    sys.exit(0)
g["setup_camera_and_lights"]((0.0, 0.0, 0.0), 1920 / g["MENU_PPU"], (1920 // SCALE, 1080 // SCALE))
# moonlight: from the moon's side (upper right, a little in front), pale and warm
pixel_style.sun((-0.55, 0.45, -0.7), energy=2.6, color=(0.96, 0.9, 0.76))
cam = sc.camera
for name, (near, far) in (("menu_front.png", (0.1, 30.0)), ("menu_back.png", (30.0, 200.0))):
    cam.data.clip_start, cam.data.clip_end = near, far
    sc.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)

from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

bpy.context.view_layer.update()
marks = {}
for name in ("Gem-1", "Gem1", "ForeheadGem"):
    ob = bpy.data.objects[name]
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    c = sum(vs, Vector()) / len(vs)
    p = world_to_camera_view(sc, cam, c)
    marks[name] = {"x": round(p.x * 1920, 1), "y": round((1 - p.y) * 1080, 1), "front": c.y < 0, "depth": round(c.y, 3)}
json.dump(marks, open(os.path.join(OUT, "menu_marks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "naga_pixel_menu.blend"))
print("PIXEL MENU DONE", marks)
