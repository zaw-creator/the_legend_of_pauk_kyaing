"""Viewport helpers for the live Blender session (exec'd inside the open window)."""
import math

import bpy
from mathutils import Euler, Vector


def view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                return win, area, area.spaces.active
    return None, None, None


def frame(center, dist, yaw=0.0, pitch=0.0, shading="MATERIAL", ortho=True):
    """Aim the 3D viewport at `center`. yaw 0 = looking along +Y from -Y (side view of a head facing +X)."""
    win, area, sp = view3d()
    r3d = sp.region_3d
    sp.shading.type = shading
    sp.overlay.show_overlays = False
    r3d.view_perspective = "ORTHO" if ortho else "PERSP"
    r3d.view_location = Vector(center)
    r3d.view_distance = dist
    r3d.view_rotation = Euler((math.radians(90 - pitch), 0.0, math.radians(yaw)), "XYZ").to_quaternion()


def head_point(local=(0.4, 0.0, 0.3)):
    return bpy.data.objects["HeadRoot"].matrix_world @ Vector(local)


def shot(path):
    win, area, sp = view3d()
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.screen.screenshot_area(filepath=path)
    print("saved", path)


def snap(path, res=(1400, 1000)):
    """Quick viewport capture (offscreen, no Cycles): what the 3D view shows, written to a PNG."""
    win, area, sp = view3d()
    region = next(r for r in area.regions if r.type == "WINDOW")
    sc = bpy.context.scene
    old = (sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    sc.render.film_transparent = False
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.render.opengl(write_still=True, view_context=True)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent = old
    print("saved", path)
