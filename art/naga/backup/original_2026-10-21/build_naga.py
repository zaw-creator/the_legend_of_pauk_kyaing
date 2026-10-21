"""Builds the Myanmar-style naga (dragon) for The Legend of Maung Pauk Kyaing.

Standalone (headless):
    Blender -b -P build_naga.py -- <output folder> [head|full|both|menu|none]
Environment: NAGA_SAMPLES (render samples, default 96), NAGA_BG=1 (render with a night background),
NAGA_POSE=menu (coil the body around the palace of the main menu; use with "menu"),
NAGA_RES (render resolution percentage, default 100).

Live (inside an open Blender window): set NAGA_LIVE = True in the namespace, exec this file, then call
bind_existing() and any build_*() function to rebuild just that part. Each build_* function first deletes
the objects it made before, so parts can be redone one at a time.

The head follows the shape language of traditional Myanmar naga art: a flame crest of swept-back tongues,
a face shield with a ringed gem eye, a lip with rows of fangs, a curled nose, curling ear flames, a black
beard laid back over the chin and shingle scales running down the neck. Everything is procedural.
Units: 1 Blender unit is about 1 metre; the head is about 1.1 units long before HEAD_SCALE.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

NAGA_LIVE = bool(globals().get("NAGA_LIVE", False))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.getcwd()
WHAT = argv[1] if len(argv) > 1 else "both"
SAMPLES = int(os.environ.get("NAGA_SAMPLES", "96"))
BODY_SCALE = 1.3
HEAD_SCALE = 1.3
HEAD_PITCH = -14  # degrees the head tilts against the neck; negative raises the nose

if not NAGA_LIVE:
    bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = bpy.data.collections.get("Naga")
if col is None:
    col = bpy.data.collections.new("Naga")
    scene.collection.children.link(col)


def link(obj, parent=None):
    col.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def clear(*prefixes):
    """Delete every object whose name starts with one of the prefixes (and its orphaned data)."""
    for ob in list(bpy.data.objects):
        if ob.name.startswith(prefixes):
            bpy.data.objects.remove(ob, do_unlink=True)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (lin(r), lin(g), lin(b), a)


# ------------------------------------------------------------------ materials (reused if they already exist)
def principled(name, color, rough=0.5, metal=0.0, emit=None, emit_strength=0.0, sss=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hexc(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = hexc(emit)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if sss:
        bsdf.inputs["Subsurface Weight"].default_value = sss
        bsdf.inputs["Subsurface Radius"].default_value = (0.3, 0.3, 0.3)
    return m


def scale_skin(name, base, edge, belly=False, scale=8.0):
    """Scales from a Voronoi pattern in UV space (u around, v along)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    uv = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale) if not belly else (2.0, 9.0, 2.0)
    links.new(uv.outputs["UV"], mp.inputs["Vector"])
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    links.new(mp.outputs["Vector"], vor.inputs["Vector"])
    cell = nodes.new("ShaderNodeTexVoronoi")
    cell.feature = "F1"
    links.new(mp.outputs["Vector"], cell.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = hexc(edge)
    ramp.color_ramp.elements[1].position = 0.18
    ramp.color_ramp.elements[1].color = hexc(base)
    links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    vary = nodes.new("ShaderNodeMix")
    vary.data_type = "RGBA"
    vary.blend_type = "MULTIPLY"
    vary.inputs["Factor"].default_value = 0.35
    cr = nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = hexc("#C8D6CF")
    cr.color_ramp.elements[1].color = hexc("#FFFFFF")
    links.new(cell.outputs["Distance"], cr.inputs["Fac"])
    links.new(ramp.outputs["Color"], vary.inputs["A"])
    links.new(cr.outputs["Color"], vary.inputs["B"])
    links.new(vary.outputs["Result"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.7
    bump.inputs["Distance"].default_value = 0.02
    links.new(vor.outputs["Distance"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.inputs["Coat Weight"].default_value = 0.2
    return m


def gold(name, root="#7A4A1E", base="#C9A04A", tip="#E6C778", metal=0.7, rough=0.34):
    """Metal that runs root -> base -> tip along the UV u coordinate."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hexc(root)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = hexc(tip)
    ramp.color_ramp.elements[1].position = 1.0
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = hexc(base)
    nt.links.new(sep.outputs["X"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    return m


MAT = {
    "skin": scale_skin("NagaSkin", "#22503F", "#0A261E", scale=5.0),
    "head": scale_skin("NagaHead", "#265644", "#0B271F", scale=7.0),
    "belly": scale_skin("NagaBelly", "#E2D5AE", "#A19468", belly=True),
    "gold": gold("NagaGold"),
    "flame": gold("NagaFlame", root="#7C3D12", base="#D08A2A", tip="#F2C75E", metal=0.55, rough=0.38),
    "collar": gold("NagaCollar", root="#6E340F", base="#C77A28", tip="#E9AE50", metal=0.5, rough=0.42),
    "hair": gold("NagaHair", root="#A8631F", base="#E1A43C", tip="#F6D56E", metal=0.5, rough=0.4),
    # black hair matching the beard, with a soft sheen so each strand still reads
    "hair_black": gold("NagaHairBlack", root="#060507", base="#121014", tip="#2A252C", metal=0.25, rough=0.32),
    "hair_black2": gold("NagaHairBlack2", root="#0A080B", base="#19161B", tip="#332D36", metal=0.25, rough=0.36),
    "tongue": principled("Tongue", "#5E1F18", rough=0.35, sss=0.2),
    "tooth": principled("Tooth", "#F1E8D2", rough=0.28),
    "eye": principled("Eye", "#0E0C0C", rough=0.1),
    "gem": principled("Gem", "#C2361A", rough=0.15, emit="#FF5A1F", emit_strength=4.0),
    "horn": gold("NagaHorn", root="#1E1812", base="#4F4029", tip="#CDB98A", metal=0.15, rough=0.5),
    "spike": gold("NagaSpike", root="#10140F", base="#2B2A1E", tip="#B8A57A", metal=0.2, rough=0.45),
    "beard": principled("Beard", "#0F0D10", rough=0.55),
}

# ------------------------------------------------------------------ geometry helpers


def catmull(points, step=0.05):
    ext = [points[0]] + list(points) + [points[-1]]
    dense = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = (Vector(p) for p in ext[i - 1:i + 3])
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
        for k in range(30):
            t = k / 30
            u = 1 - t
            dense.append(u**3 * p1 + 3 * u * u * t * c1 + 3 * u * t * t * c2 + t**3 * p2)
    dense.append(Vector(points[-1]))
    out = [dense[0]]
    acc = 0.0
    for a, b in zip(dense, dense[1:]):
        acc += (b - a).length
        if acc >= step:
            out.append(b)
            acc = 0.0
    if (dense[-1] - out[-1]).length > 1e-6:  # the loop may already have ended on the last point
        out.append(dense[-1])
    return out


def make_obj(name, bm, mats, parent=None, smooth=True, subsurf=0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    link(ob, parent)
    if subsurf:
        md = ob.modifiers.new("Subsurf", "SUBSURF")
        md.levels = subsurf
        md.render_levels = subsurf
    return ob


def super_ring(a, bu, bd, p, n):
    pts = []
    for k in range(n):
        th = 2 * math.pi * k / n
        c, s = math.cos(th), math.sin(th)
        y = a * math.copysign(abs(c) ** (2 / p), c)
        z = (bu if s >= 0 else bd) * math.copysign(abs(s) ** (2 / p), s)
        pts.append((y, z))
    return pts


def loft(name, stations, n=28, p=2.4, parent=None, mat=None, tip=True, cap_start=False, subsurf=2):
    """Loft superellipse rings. Each station: dict(x, a, bu, bd, z)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV")
    rings = []
    for st in stations:
        ring = []
        for (y, z) in super_ring(st["a"], st["bu"], st["bd"], st.get("p", p), n):
            ring.append(bm.verts.new((st["x"], y + st.get("y", 0.0), z + st["z"])))
        rings.append(ring)
    total = len(rings) - 1
    for i in range(total):
        for k in range(n):
            k2 = (k + 1) % n
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp, (uu, vv) in zip(f.loops, ((k / n, i / total), ((k + 1) / n, i / total),
                                              ((k + 1) / n, (i + 1) / total), (k / n, (i + 1) / total))):
                lp[uvl].uv = (uu, vv)
    if tip:
        last = stations[-1]
        c = bm.verts.new((last["x"] + last.get("tipx", 0.04), last.get("y", 0.0), last["z"] + last.get("tipz", 0.0)))
        for k in range(n):
            bm.faces.new((rings[-1][k], rings[-1][(k + 1) % n], c))
    if cap_start:
        first = stations[0]
        c = bm.verts.new((first["x"] - 0.03, first.get("y", 0.0), first["z"]))
        for k in range(n):
            bm.faces.new((rings[0][(k + 1) % n], rings[0][k], c))
    bm.normal_update()
    return make_obj(name, bm, [mat or MAT["head"]], parent, subsurf=subsurf)


def sphere(name, r, loc, scale=(1, 1, 1), mat=None, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(loc)
    return make_obj(name, bm, [mat or MAT["head"]], parent)


def cone(name, r, depth, loc, rot=(0.0, 0.0, 0.0), mat=None, parent=None, seg=8):
    """Cone with its base at `loc` pointing along local +Z, then rotated by `rot` (euler)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=0.0, depth=depth)
    rotm = Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
    for v in bm.verts:
        v.co = rotm @ Vector((v.co.x, v.co.y, v.co.z + depth / 2)) + Vector(loc)
    return make_obj(name, bm, [mat or MAT["tooth"]], parent)


def tube(name, pts, r0, r1, mat, parent=None, n=10, step=0.02, power=1.0):
    """Round tube along a smooth path, radius r0 at the root to r1 at the tip; UV u runs root (0) to tip (1)."""
    path = catmull([tuple(p) for p in pts], step)
    m = len(path)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV")
    rings = []
    ref = Vector((0, 0, 1))
    for i, c in enumerate(path):
        t = (path[min(m - 1, i + 1)] - path[max(0, i - 1)]).normalized()
        a = ref - t * ref.dot(t)
        if a.length < 1e-4:
            a = Vector((0, 1, 0)) - t * t.y
        a.normalize()
        b = t.cross(a)
        f = i / (m - 1)
        r = r0 + (r1 - r0) * f ** power
        rings.append([bm.verts.new(c + r * (math.cos(2 * math.pi * k / n) * a + math.sin(2 * math.pi * k / n) * b))
                      for k in range(n)])
    for i in range(m - 1):
        for k in range(n):
            k2 = (k + 1) % n
            face = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp in face.loops:
                lp[uvl].uv = (i / (m - 1), k / n)
    tip = bm.verts.new(path[-1] + (path[-1] - path[-2]).normalized() * r1 * 2)
    for k in range(n):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % n], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return make_obj(name, bm, [mat], parent)


def spike(name, base, direction, r, length, mat, parent=None, curl=0.0, up=None):
    """A slightly curved horn-like spike from `base` along `direction` (bends toward `up` by `curl`)."""
    d = Vector(direction).normalized()
    u = Vector(up) if up is not None else Vector((0, 0, 1))
    u = (u - d * u.dot(d))
    u = u.normalized() if u.length > 1e-4 else Vector((0, 0, 0))
    base = Vector(base)
    pts = [base + d * length * f + u * curl * length * f * f for f in (0.0, 0.35, 0.7, 1.0)]
    return tube(name, pts, r, r * 0.08, mat, parent, n=8, step=max(0.01, length / 10))


def curve_obj(name, pts, radius, mat, parent=None, taper=None, handle="AUTO", res=5, extrude=0.0, cyclic=False):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 12
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = handle
        bp.handle_right_type = handle
    sp.use_cyclic_u = cyclic
    cu.bevel_depth = radius
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    cu.extrude = extrude
    if taper:
        cu.taper_object = taper
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    link(ob, parent)
    return ob


def taper_obj(name, pts):
    ob = bpy.data.objects.get(name)
    if ob:
        return ob
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for pt, (x, y) in zip(sp.points, pts):
        pt.co = (x, y, 0, 1)
    ob = bpy.data.objects.new(name, cu)
    link(ob)
    ob.hide_render = True
    ob.hide_viewport = True
    return ob


TAPER_THIN = taper_obj("TaperThin", [(0, 1.0), (0.35, 0.8), (1, 0.05)])
TAPER_BOTH = taper_obj("TaperBoth", [(0, 0.1), (0.2, 1.0), (0.8, 1.0), (1, 0.1)])


def flame_tongue(name, length, width, curl, thick, mat, parent=None, serr=0.12, nu=30, m=5, hook=0.5):
    """One flame tongue standing along +Z, curling toward -X, lens cross-section, serrated edges.

    UV u runs base (0) to tip (1) so the material can fade root -> tip.
    """
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV")

    def spine(u):
        z = length * u
        x = -curl * length * u ** 2.0 - hook * length * max(0.0, u - 0.72) ** 2 * 2.6
        return Vector((x, 0.0, z))

    rings = []
    for i in range(nu + 1):
        u = i / nu
        c = spine(u)
        t = (spine(min(1.0, u + 0.01)) - spine(max(0.0, u - 0.01))).normalized()
        nrm = Vector((-t.z, 0.0, t.x))
        rise = 0.45 + 0.55 * math.sin(0.5 * math.pi * min(1.0, u / 0.3))
        fall = max(0.0, 1.0 - u ** 2.0) ** 0.8
        w = width * rise * fall
        w *= 1.0 + serr * (abs(((u * 17.0) % 1.0) - 0.5) * 2.0 - 0.5)
        th = thick * (1.0 - 0.5 * u)
        ring = []
        for j in range(m + 1):
            v = -1 + 2 * j / m
            ring.append(c + nrm * (w * v) + Vector((0.0, th * (1 - v * v), 0.0)))
        for j in range(m - 1, 0, -1):
            v = -1 + 2 * j / m
            ring.append(c + nrm * (w * v) - Vector((0.0, th * (1 - v * v), 0.0)))
        rings.append([bm.verts.new(p) for p in ring])
    nr = len(rings[0])
    for i in range(nu):
        for k in range(nr):
            k2 = (k + 1) % nr
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp in f.loops:
                lp[uvl].uv = (i / nu, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return make_obj(name, bm, [mat], parent, smooth=True)


def feather_mesh(length, width, cup=0.12):
    """Pointed leaf, UV u runs base to tip. Used for shingles and petals."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV")
    ns, nw = 8, 4
    grid = []
    for i in range(ns + 1):
        u = i / ns
        w = width * (math.sin(math.pi * min(0.999, u * 0.97)) ** 0.7) * (1.0 - 0.1 * u)
        row = []
        for j in range(nw + 1):
            v = -1 + 2 * j / nw
            row.append(bm.verts.new((u * length, v * w, cup * length * (u * u + 0.4 * v * v * 0.3))))
        grid.append(row)
    for i in range(ns):
        for j in range(nw):
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x / length, (lp.vert.co.y / width + 1) / 2)
    me = bpy.data.meshes.new("Leaf")
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    return me


def place_leaf(me, mat, name, parent, x_axis, z_axis, loc, solid=0.01, scale=1.0):
    x_axis = Vector(x_axis).normalized()
    y_axis = Vector(z_axis).cross(x_axis).normalized()
    z_axis = x_axis.cross(y_axis).normalized()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    link(ob, parent)
    ob.matrix_parent_inverse = Matrix.Identity(4)
    m = Matrix(((x_axis.x, y_axis.x, z_axis.x, loc[0]), (x_axis.y, y_axis.y, z_axis.y, loc[1]),
                (x_axis.z, y_axis.z, z_axis.z, loc[2]), (0, 0, 0, 1)))
    ob.matrix_basis = m @ Matrix.Diagonal((scale, scale, scale, 1.0))
    if solid:
        sol = ob.modifiers.new("Solidify", "SOLIDIFY")
        sol.thickness = solid
    return ob


# ------------------------------------------------------------------ spine and body
SPINE = [(-4.5, 0.0, 0.6), (-3.6, 0.1, -0.05), (-2.3, 0.2, -0.25), (-1.1, 0.15, 0.1), (-0.3, 0.05, 0.9),
         (-0.15, 0.0, 1.8), (-0.55, -0.1, 2.6), (-0.35, -0.15, 3.4), (0.45, -0.1, 3.95), (1.55, 0.0, 4.05),
         (2.25, 0.05, 3.78), (2.9, 0.0, 3.95), (3.35, 0.0, 4.32), (3.8, 0.0, 4.52), (4.25, 0.0, 4.45)]

# Main-menu pose: the body wraps the palace of the 1920x1080 menu. Points are menu pixels (x, y) plus depth d in
# world units (+ = in front of the palace, toward the viewer). The menu render uses an orthographic camera, so a pixel
# maps straight to world X/Z at MENU_PPU pixels per unit.
POSE = os.environ.get("NAGA_POSE", "hero")
MENU_PPU = 120.0
# Depth crossings (d = 0) sit in open sky beside the palace, never over it, or the body seems to pierce the walls.
# The palace in the menu is drawn 1.3x about (1000, 880): hall 727-1273 x 646-828, lowest eave 666-1334 x 578-646,
# upper tiers narrowing to 887-1113 at y 337, spire to y 214.
# A guardian: the tail curls on the ground before the door, the body coils up around the pagoda twice (in front,
# behind, in front, behind) and the head rests on top of the roofs, looking out to the right over the courtyard.
MENU_PATH_PX = [
    (1180, 868, 0.9), (1060, 872, 0.9), (920, 868, 0.85),        # tail tip on the ground in front of the door
    (790, 845, 0.75), (735, 800, 0.6),                           # curls up at the left corner
    (800, 760, 0.55), (960, 745, 0.6), (1120, 740, 0.6), (1260, 726, 0.5), (1360, 700, 0.3),  # across the hall
    (1392, 668, 0.0),                                            # goes behind in the open, right of the eave
    (1384, 636, -0.3), (1332, 600, -0.6),                        # round the right side
    (1200, 612, -0.8), (1040, 618, -0.85), (880, 612, -0.8),     # behind the pagoda, right to left
    (762, 578, -0.6), (750, 530, -0.3),                          # up the left side
    (790, 488, 0.0),                                             # forward in the open, left of the middle tier
    (860, 468, 0.45), (1000, 470, 0.6), (1140, 462, 0.55), (1230, 440, 0.3),  # across the front of the middle tier
    (1262, 410, 0.0),                                            # behind again, right of the upper tiers
    (1240, 372, -0.35), (1150, 352, -0.6), (1040, 350, -0.6),    # behind the top roof, right to left
    (960, 368, -0.5),                                            # out on the left of the top roof
]


def _bezier_px(a, b, c, d, n):
    """n points (skipping the first) along a cubic Bezier between menu pixel points."""
    out = []
    for k in range(1, n + 1):
        t = k / n
        u = 1 - t
        out.append(tuple(u ** 3 * a[i] + 3 * u * u * t * b[i] + 3 * u * t * t * c[i] + t ** 3 * d[i] for i in range(2)))
    return out


# The neck rises from the left of the top roof, arches over it behind the spire, and the head comes forward on the
# right, resting on top of the palace and glaring down over the courtyard.
# It stays well behind the palace plane until past the spire, so the spire is drawn over it.
_NECK = (_bezier_px((960, 368), (935, 315), (990, 292), (1060, 296), 5)
         + _bezier_px((1060, 296), (1110, 300), (1150, 306), (1196, 322), 4))
_NECK_D = [-0.5, -0.5, -0.52, -0.55, -0.55, -0.35, -0.1, 0.12, 0.3]
MENU_PATH_PX += [(round(x), round(y), d) for (x, y), d in zip(_NECK, _NECK_D)]
MENU_NECK_BACK = (-1.0, -0.35, 0.0)  # where the back of a reared neck faces: away from where the head looks
if POSE == "menu":
    SPINE = [((px - 960) / MENU_PPU, -d, (540 - py) / MENU_PPU) for px, py, d in MENU_PATH_PX]
    BODY_SCALE, HEAD_SCALE = 1.6, 1.7  # seen small in the menu, so a heavier serpent body and a big guardian head
    TAIL_FRAC, NECK_FRAC = 0.14, 0.9   # the coiled body is long: keep the taper to the tail and the neck
    HEAD_PITCH = 4                     # the neck already tips the head down over the courtyard


TAIL_FRAC, NECK_FRAC = 0.26, 0.82  # share of the body that tapers to the tail / swells into the neck


def radius(u):
    if u < TAIL_FRAC:
        r = 0.04 + (0.14 - 0.04) * (u / TAIL_FRAC)
    elif u > NECK_FRAC:
        r = 0.14 + (0.2 - 0.14) * ((u - NECK_FRAC) / (1.0 - NECK_FRAC)) ** 1.2
    else:
        r = 0.14 + 0.005 * math.sin(u * 18)
    return r * BODY_SCALE


def compute_spine():
    """Sampled spine points with tangent and 'up' normal frames (rotation minimising)."""
    pts = catmull(SPINE, 0.06)
    n_r = len(pts)
    tang = []
    for i in range(n_r):
        a = pts[max(0, i - 1)]
        b = pts[min(n_r - 1, i + 1)]
        tang.append((b - a).normalized())

    def frames(sign):
        up = Vector((0, 0, 1))
        nrm = (up - tang[0] * up.dot(tang[0])).normalized() * sign
        out = []
        for i in range(n_r):
            t = tang[i]
            nrm = (nrm - t * nrm.dot(t)).normalized()
            out.append(nrm.copy())
        return out

    nrm = frames(1)
    if POSE == "menu":
        # Coils loop back on themselves, so rotation-minimising frames end up belly-up. Instead keep the back facing
        # up, and on near-vertical climbs facing the viewer (belly against the palace), then smooth.
        up, toward, back = Vector((0, 0, 1)), Vector((0, -1, 0)), Vector(MENU_NECK_BACK).normalized()
        guide = []
        for i, t in enumerate(tang):
            v = min(1.0, max(0.0, (abs(t.z) - 0.55) / 0.4))
            # on the reared neck the back faces away from where the head looks, so the throat faces forward
            w = min(1.0, max(0.0, (i / (n_r - 1) - 0.8) / 0.1))
            side = (toward * (1 - w) + back * w).normalized()
            g = up + side * (2.5 * v * v * (3 - 2 * v))
            guide.append((g - t * g.dot(t)).normalized())
        for _ in range(6):
            guide = [((guide[max(0, i - 1)] + guide[i] * 2 + guide[min(n_r - 1, i + 1)]) / 4) for i in range(n_r)]
            guide = [(g - tang[i] * g.dot(tang[i])).normalized() for i, g in enumerate(guide)]
        nrm = guide
    elif nrm[-1].dot(Vector((0, 0, 1))) < 0:
        nrm = frames(-1)
    return pts, tang, nrm


def build_body():
    clear("NagaBody")
    pts, tang, nrm = compute_spine()
    n_r = len(pts)
    n = 24
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV")
    arc = [0.0]
    for i in range(1, n_r):
        arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    rings = []
    for i in range(n_r):
        u = i / (n_r - 1)
        r = radius(u)
        t = tang[i]
        nn = nrm[i]
        bb = t.cross(nn).normalized()
        rings.append([bm.verts.new(pts[i] + r * (math.cos(2 * math.pi * k / n) * bb + math.sin(2 * math.pi * k / n) * nn))
                      for k in range(n)])
    for i in range(n_r - 1):
        for k in range(n):
            k2 = (k + 1) % n
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            th = (2 * math.pi * (k + 0.5) / n) % (2 * math.pi)
            f.material_index = 1 if abs(th - 1.5 * math.pi) < math.radians(48) else 0
            v0, v1 = arc[i] / 0.9, arc[i + 1] / 0.9
            for lp, (uu, vv) in zip(f.loops, ((k / n, v0), ((k + 1) / n, v0), ((k + 1) / n, v1), (k / n, v1))):
                lp[uvl].uv = (uu, vv)
    c = bm.verts.new(pts[0] - tang[0] * 0.05)
    for k in range(n):
        bm.faces.new((rings[0][(k + 1) % n], rings[0][k], c))
    bm.normal_update()
    return make_obj("NagaBody", bm, [MAT["skin"], MAT["belly"]], subsurf=1)


# ------------------------------------------------------------------ head (head-local: +X forward, +Z up)
head_root = None
jaw_root = None
jaw_pivot = Vector((0.12, 0, -0.12))


def X(x):
    """Shorten the snout: positions past the eyes are compressed."""
    return x if x < 0.5 else 0.5 + (x - 0.5) * 0.78


UPPER = [
    dict(x=-0.12, a=0.20, bu=0.21, bd=0.20, z=0.00),
    dict(x=0.05, a=0.28, bu=0.29, bd=0.23, z=0.02),
    dict(x=0.20, a=0.32, bu=0.33, bd=0.21, z=0.05),
    dict(x=0.35, a=0.29, bu=0.31, bd=0.18, z=0.07),
    dict(x=X(0.50), a=0.22, bu=0.22, bd=0.13, z=0.06),
    dict(x=X(0.68), a=0.17, bu=0.16, bd=0.10, z=0.05),
    dict(x=X(0.85), a=0.15, bu=0.14, bd=0.07, z=0.06),
    dict(x=X(0.97), a=0.17, bu=0.15, bd=0.08, z=0.075),          # snout runs straight; no upturned tip
    dict(x=X(1.06), a=0.14, bu=0.12, bd=0.07, z=0.08, tipx=0.05, tipz=0.0),
]
LOWER = [
    dict(x=0.12, a=0.20, bu=0.08, bd=0.12, z=-0.17),
    dict(x=0.35, a=0.20, bu=0.07, bd=0.11, z=-0.20),
    dict(x=X(0.60), a=0.15, bu=0.06, bd=0.08, z=-0.19),
    dict(x=X(0.80), a=0.11, bu=0.05, bd=0.065, z=-0.16),
    dict(x=X(0.93), a=0.08, bu=0.04, bd=0.055, z=-0.13, tipx=0.04, tipz=0.015),
]


def st_at(stations, x):
    for a, b in zip(stations, stations[1:]):
        if a["x"] <= x <= b["x"]:
            t = (x - a["x"]) / (b["x"] - a["x"])
            return {k: a[k] * (1 - t) + b[k] * t for k in ("a", "bu", "bd", "z")}
    st = stations[0] if x < stations[0]["x"] else stations[-1]
    return {k: st[k] for k in ("a", "bu", "bd", "z")}


def surf(x, th_deg, out=0.0, side=1, stations=None):
    """Point on a loft surface at station x, angle th (0 = side, 90 = top, negative = lower)."""
    st = st_at(stations or UPPER, x)
    th = math.radians(th_deg)
    c, s = math.cos(th), math.sin(th)
    y = st["a"] * math.copysign(abs(c) ** (2 / 2.4), c)
    z = st["z"] + (st["bu"] if s >= 0 else st["bd"]) * math.copysign(abs(s) ** (2 / 2.4), s)
    v = Vector((x, y, z))
    if out:
        v += Vector((0.0, y, z - st["z"])).normalized() * out
    v.y *= side
    return v


def surface_top(x):
    st = st_at(UPPER, x)
    return st["z"] + st["bu"]


def jaw_pt(x, y, z):
    return (x - jaw_pivot.x, y, z - jaw_pivot.z)


def bind_existing():
    """Live mode: find the parts of an already built naga."""
    global head_root, jaw_root
    head_root = bpy.data.objects["HeadRoot"]
    jaw_root = bpy.data.objects["JawRoot"]


def build_head_base():
    global head_root, jaw_root
    clear("HeadRoot", "UpperHead", "JawRoot", "LowerJaw")
    head_root = bpy.data.objects.new("HeadRoot", None)
    link(head_root)
    loft("UpperHead", UPPER, parent=head_root, mat=MAT["head"])
    jaw_root = bpy.data.objects.new("JawRoot", None)
    link(jaw_root, head_root)
    jaw_root.location = jaw_pivot
    jaw_root.rotation_euler = (0, math.radians(27), 0)  # a wide snarl
    lower_local = [dict(st, x=st["x"] - jaw_pivot.x, z=st["z"] - jaw_pivot.z) for st in LOWER]
    loft("LowerJaw", lower_local, parent=jaw_root, mat=MAT["head"], cap_start=True)


# ---- parts that can be rebuilt one by one ------------------------------------------------------------
LIP_TH = -40   # angle of the mouth line on the upper head (degrees, negative = below the side)
JAW_TH = 36    # angle of the mouth line on the lower jaw


FANGS_UP = {6: (0.032, 0.24), 2: (0.026, 0.16)}   # upper tooth index: (root radius, length) of the big fangs
FANGS_DOWN = {5: (0.026, 0.17)}                   # lower canine


def build_teeth():
    """Fangs sit along the mouth line, not on the cheek: upper teeth hang from the lip edge, lower ones rise from the jaw.
    Two long sabre fangs a side above and a canine below make the snarl."""
    clear("Tooth", "LTooth")
    for side in (-1, 1):
        n = 9
        for i in range(n):
            t = i / (n - 1)
            x = 0.16 + (X(0.96) - 0.16) * t
            p = surf(x, LIP_TH, -0.008, side)
            r, d = FANGS_UP.get(i, (0.015 + 0.004 * ((i * 7) % 3) / 2, 0.07 + 0.03 * ((i * 5) % 3) / 2))
            cone("Tooth%d_%d" % (side, i), r, d, tuple(p), (math.pi, 0, 0), parent=head_root)
        m = 7
        for i in range(m):
            t = i / (m - 1)
            x = 0.30 + (X(0.88) - 0.30) * t
            q = surf(x, JAW_TH, -0.006, side, stations=LOWER)
            r, d = FANGS_DOWN.get(i, (0.014 + 0.004 * (1 - t), 0.06 + 0.025 * (1 - t)))
            cone("LTooth%d_%d" % (side, i), r, d, jaw_pt(q.x, q.y, q.z), (0, 0, 0), parent=jaw_root)


def build_borders():
    """Gold face-shield borders, lip rims, nose ridge and the curled nose."""
    clear("LipRim", "BrowBorder", "CheekBorder", "NoseRidge", "NoseCurl", "CheekScroll", "BrowScroll")
    for side in (-1, 1):
        curve_obj("LipRim%d" % side, [surf(x, th, 0.014, side) for x, th in
                                      ((X(1.0), -30), (X(0.85), -34), (X(0.62), -37), (0.42, -38), (0.22, -34), (0.08, -26))],
                  0.016, MAT["gold"], parent=head_root, taper=TAPER_THIN)
        curve_obj("BrowBorder%d" % side, [surf(x, th, 0.012, side) for x, th in
                                          ((X(0.98), 30), (X(0.74), 40), (0.5, 46), (0.34, 52), (0.18, 58), (0.04, 60))],
                  0.018, MAT["flame"], parent=head_root, taper=TAPER_BOTH)
        curve_obj("CheekBorder%d" % side, [surf(x, th, 0.012, side) for x, th in
                                           ((0.30, -14), (0.12, -6), (0.02, 14), (0.0, 36), (0.06, 54))],
                  0.016, MAT["flame"], parent=head_root, taper=TAPER_BOTH)
    curve_obj("NoseRidge", [surf(x, 90, 0.01) for x in (0.30, 0.44, X(0.7), X(0.92), X(1.02))],
              0.014, MAT["flame"], parent=head_root, taper=TAPER_THIN)


def build_brows():
    """Heavy brow ridges slanting down toward the snout (a scowl) and a horn on the nose."""
    clear("BrowRidge", "BrowSpike", "NoseHorn", "CheekSpike")
    for side in (-1, 1):
        tube("BrowRidge%d" % side, [surf(x, th, out, side) for x, th, out in
                                    ((0.48, 22, 0.015), (0.41, 29, 0.045), (0.33, 35, 0.06), (0.23, 41, 0.055),
                                     (0.12, 47, 0.03))], 0.046, 0.016, MAT["head"], head_root, n=12)
        for j, (x, th) in enumerate(((0.14, 60), (0.07, 62), (0.0, 58))):
            base = surf(x, th, 0.02, side)
            spike("BrowSpike%d_%d" % (side, j), base, (-1.0, side * 0.45, 0.35), 0.022, 0.13 + 0.04 * j,
                  MAT["spike"], head_root, curl=0.25)
        for j, (x, th) in enumerate(((0.20, -8), (0.12, 2), (0.04, 12), (-0.04, 22))):
            base = surf(x, th, -0.01, side)
            spike("CheekSpike%d_%d" % (side, j), base, (-1.0, side * 0.75, -0.1 + 0.08 * j), 0.024, 0.15 + 0.03 * j,
                  MAT["spike"], head_root, curl=0.2)
    nose = surf(X(0.97), 90, -0.01)
    spike("NoseHorn", nose, (-0.35, 0.0, 1.0), 0.03, 0.14, MAT["horn"], head_root, curl=0.3, up=(-1, 0, 0))


def build_horns():
    """Swept-back horns from the back of the skull, rising out of the hair."""
    clear("Horn")
    for side in (-1, 1):
        tube("Horn%d_0" % side, [surf(0.12, 64, -0.03, side), (-0.06, side * 0.27, 0.40), (-0.30, side * 0.34, 0.52),
                                 (-0.52, side * 0.33, 0.66), (-0.62, side * 0.28, 0.80)],
             0.07, 0.004, MAT["horn"], head_root, n=12, power=0.8)
        tube("Horn%d_1" % side, [surf(0.04, 22, -0.02, side), (-0.16, side * 0.36, 0.16), (-0.36, side * 0.42, 0.22),
                                 (-0.50, side * 0.40, 0.34)],
             0.045, 0.003, MAT["horn"], head_root, n=10, power=0.8)


def build_tongue():
    clear("Tongue")
    curve_obj("Tongue", [jaw_pt(0.15, 0, -0.03), jaw_pt(0.45, 0, -0.02), jaw_pt(X(0.80), 0, -0.07), jaw_pt(X(1.0), 0, -0.20)],
              0.012, MAT["tongue"], parent=jaw_root, taper=TAPER_THIN, extrude=0.05)


def build_beard():
    """Black hair laid back over the chin and along the underside of the jaw."""
    clear("Beard")
    rows = [  # (x along the jaw, strand length, strand width, droop curl)
        (0.80, 0.30, 0.060, 0.30),
        (0.70, 0.39, 0.066, 0.32),
        (0.59, 0.46, 0.070, 0.34),
        (0.48, 0.44, 0.070, 0.36),
        (0.37, 0.37, 0.066, 0.38),
    ]
    k = 0
    for ri, (x, ln, w, curl) in enumerate(rows):
        st = st_at(LOWER, x)
        ys = (-0.10, -0.05, 0.0, 0.05, 0.10) if ri > 0 else (-0.04, 0.0, 0.04)
        for y in ys:
            ln_i = ln * (1.0 - 0.18 * abs(y) / 0.10)
            ob = flame_tongue("Beard%d" % k, ln_i, w, curl, 0.014, MAT["beard"], parent=jaw_root, serr=0.18, hook=0.9)
            ob.location = jaw_pt(x, y, st["z"] - st["bd"] * 0.85)
            ob.rotation_euler = (0, math.radians(-(103 + 5 * ri)), math.radians(y * 90))
            k += 1
    # side tufts hugging the jaw so the hair wraps the chin from both sides
    for side in (-1, 1):
        for j, x in enumerate((0.84, 0.72, 0.60, 0.48, 0.38)):
            st = st_at(LOWER, x)
            ob = flame_tongue("Beard%d" % k, 0.22 + 0.04 * j, 0.05, 0.30, 0.012, MAT["beard"], parent=jaw_root, serr=0.18, hook=0.9)
            ob.location = jaw_pt(x, side * st["a"] * 0.80, st["z"] - st["bd"] * 0.40)
            ob.rotation_euler = (math.radians(side * 28), math.radians(-(104 + 2 * j)), 0)
            k += 1


def build_eyes():
    """Narrow almond eyes set into the head (flush with the skin, not bulging), ringed by a dark lid under the brow."""
    clear("EyeSocket", "Gem", "Pupil", "EyePetal", "NostrilBump", "ForeheadGem")
    for side in (-1, 1):
        eye_c = surf(0.33, 20, -0.012, side)
        d = Vector((0.30, side * 0.93, 0.34)).normalized()
        e1 = (Vector((1, 0, 0)) - d * d.x).normalized()
        e2 = d.cross(e1).normalized()
        sphere("Gem%d" % side, 0.066, tuple(eye_c - d * 0.045), (1.4, 1.0, 0.6), mat=MAT["gem"], parent=head_root)
        sphere("Pupil%d" % side, 0.018, tuple(eye_c + d * 0.012), (0.3, 0.45, 1.0), mat=MAT["eye"], parent=head_root)
        up = (Vector((0, 0, 1)) - d * d.z).normalized()
        # almond lid with pointed corners, the front corner dipping toward the snout: a glare, not a goggle
        lid = []
        for k in range(20):
            a = 2 * math.pi * k / 20
            sa = math.sin(a)
            h = 0.056 * sa * abs(sa) ** 0.35 - 0.02 * math.cos(a)
            lid.append(tuple(eye_c + d * 0.006 + math.cos(a) * 0.1 * e1 + h * up))
        curve_obj("EyeSocket%d" % side, lid, 0.011, MAT["eye"], parent=head_root, cyclic=True)
        sphere("NostrilBump%d" % side, 0.03, tuple(surf(X(1.0), 55, 0.0, side)), (1.2, 1, 0.8), mat=MAT["eye"], parent=head_root)
    sphere("ForeheadGem", 0.04, (0.50, 0.0, surface_top(0.50) + 0.012), (1, 1, 0.9), mat=MAT["gem"], parent=head_root)


def neck_sampler():
    """Returns at(s): spine frame at distance s (world units) back from the head end of the neck."""
    pts, tang, nrm = compute_spine()
    n_r = len(pts)
    arc = [0.0]
    for i in range(1, n_r):
        arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    total = arc[-1]

    def at(s):
        a = max(0.0, min(total, total - s))
        i = max(1, next(k for k in range(n_r) if arc[k] >= a))
        f = (a - arc[i - 1]) / max(1e-9, arc[i] - arc[i - 1])
        pt = pts[i - 1].lerp(pts[i], f)
        t = tang[i - 1].lerp(tang[i], f).normalized()
        nn = nrm[i - 1].lerp(nrm[i], f)
        nn = (nn - t * nn.dot(t)).normalized()
        return pt, t, nn, t.cross(nn).normalized(), radius(a / total)

    return at


def hair_strand(name, ctrl, outs, width, thick, mat, parent=None, serr=0.16, nu=60, m=4, taper=3.2, teeth=24.0,
                belly=0.4):
    """Flame-shaped ribbon that follows a path and lies flat on the surface.

    ctrl: control points (parent space); outs: outward surface direction at each control point.
    UV u runs root (0) to tip (1), like flame_tongue.
    """
    ext = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    pos, out = [], []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1:i + 3]
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
        for k in range(24):
            t = k / 24
            u = 1 - t
            pos.append(u**3 * p1 + 3 * u * u * t * c1 + 3 * u * t * t * c2 + t**3 * p2)
            out.append(outs[i - 1].lerp(outs[i], t))
    pos.append(Vector(ctrl[-1]))
    out.append(outs[-1])
    arc = [0.0]
    for i in range(1, len(pos)):
        arc.append(arc[-1] + (pos[i] - pos[i - 1]).length)

    def sample(frac):
        d = frac * arc[-1]
        i = max(1, next(k for k in range(len(arc)) if arc[k] >= d))
        f = (d - arc[i - 1]) / max(1e-9, arc[i] - arc[i - 1])
        return pos[i - 1].lerp(pos[i], f), out[i - 1].lerp(out[i], f)

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV")
    rings = []
    for i in range(nu + 1):
        u = i / nu
        c, o = sample(u)
        t = (sample(min(1.0, u + 0.01))[0] - sample(max(0.0, u - 0.01))[0]).normalized()
        o = (o - t * o.dot(t)).normalized()
        w = t.cross(o).normalized()
        rise = 0.4 + 0.6 * math.sin(0.5 * math.pi * min(1.0, u / 0.12))
        wd = width * rise * (1.0 - u ** taper) ** 0.8
        wd *= 1.0 + serr * (abs(((u * teeth) % 1.0) - 0.5) * 2.0 - 0.5)
        th = thick * (1.0 - 0.5 * u) * (1.0 - u ** 6) ** 0.5  # thins to a point, no blunt tip
        ring = []
        for j in range(m + 1):
            v = -1 + 2 * j / m
            ring.append(c + w * (wd * v) + o * (th * (1 - v * v)))
        for j in range(m - 1, 0, -1):
            v = -1 + 2 * j / m
            ring.append(c + w * (wd * v) - o * (th * (1 - v * v) * belly))
        rings.append([bm.verts.new(p) for p in ring])
    nr = len(rings[0])
    for i in range(nu):
        for k in range(nr):
            k2 = (k + 1) % nr
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp in f.loops:
                lp[uvl].uv = (i / nu, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return make_obj(name, bm, [mat], parent, smooth=True)


# Separate flame strands like the beard: tapering tongues with gaps between them, long ones with short ones between.
# top strands: (base x on the skull, how far back down the neck the tip reaches in world units, sideways offset,
#               half width in head space)
CREST_TOP = [(0.14, 0.86, 0.0, 0.085), (0.24, 0.50, -0.11, 0.06), (0.24, 0.50, 0.11, 0.06)]
# side strands: (elevation in degrees from the side towards the top, base x, tip reach, half width in head space)
CREST_SIDE = [(6, -0.04, 0.62, 0.085), (34, 0.00, 0.80, 0.085), (62, 0.04, 0.70, 0.085),
              (20, -0.02, 0.40, 0.06), (48, 0.02, 0.46, 0.06), (76, 0.06, 0.40, 0.06)]
CREST_PUFF = 0.07      # how much each strand bows away from the neck in the middle (world units)
CREST_THICK = 0.055    # strand thickness (head space)
CREST_LIFT = 0.15      # how far the hair rides above the neck surface at its root (world units)
CREST_STANDOFF = 0.10  # extra distance it streams away from the neck by the tip


def build_crest():
    """Separate flame hair strands that sweep back off the skull and fan out over the upper half of the neck."""
    clear("Crest")
    bpy.context.view_layer.update()
    inv = head_root.matrix_world.inverted()
    rot = inv.to_3x3()
    at = neck_sampler()
    mats = (MAT["hair_black"], MAT["hair_black2"])  # gold version: (MAT["hair"], MAT["flame"])

    def strand(name, base, base_out, x_base, elev, side, s_tip, width, mat, yoff=0.0, stagger=0.0):
        ctrl = [Vector(base)]
        outs = [Vector(base_out).normalized()]
        if x_base > 0.05:  # run along the skull before dropping onto the neck
            xm = (x_base - 0.08) / 2
            if elev >= 85:
                pm = Vector((xm, base[1], surface_top(xm) + 0.025))
                om = Vector((0, 0, 1))
            else:
                pm = surf(xm, elev, 0.03, side)
                om = pm - Vector((pm.x, 0.0, st_at(UPPER, xm)["z"]))
            ctrl.append(pm)
            outs.append(om.normalized())
        n = max(3, int(s_tip / 0.14))
        for k in range(n + 1):
            f = k / n
            sk = 0.04 + (s_tip - 0.04) * f
            pt, t, nn, bb, rad = at(sk)
            e = elev - (1.0 - elev / 90.0) * 16.0 * f  # lower strands drift down so the gaps open towards the tips
            o = -side * math.cos(math.radians(e)) * bb + math.sin(math.radians(e)) * nn
            lift = (CREST_LIFT + stagger + CREST_STANDOFF * f ** 1.3 + 0.04 * f ** 3  # streams off the neck, flicks at the tip
                    + CREST_PUFF * math.sin(math.pi * f))
            wp = pt + o * (rad + lift) - side * bb * yoff * (0.4 + 0.6 * f)
            ctrl.append(inv @ wp)
            outs.append((rot @ o).normalized())
        hair_strand(name, ctrl, outs, width, CREST_THICK, mat, parent=head_root, m=6, taper=1.5, teeth=12.0, belly=0.75)

    for j, (xb, s_tip, yoff, width) in enumerate(CREST_TOP):
        strand("Crest%d" % j, (xb, yoff * 0.5, surface_top(xb) - 0.03), (0, 0, 1), xb, 90, 1, s_tip, width,
               mats[0], yoff, 0.0 if j == 0 else -0.03)
    for side in (-1, 1):
        for j, (elev, xb, s_tip, width) in enumerate(CREST_SIDE):
            base = surf(xb, elev, -0.02, side)
            short = width < 0.06
            strand("CrestSide%d_%d" % (side, j), base, base - Vector((base.x, 0.0, st_at(UPPER, xb)["z"])),
                   xb, elev, side, s_tip, width, mats[1] if short else mats[0], 0.0, -0.03 if short else 0.0)


def build_ears():
    clear("Ear")
    for side in (-1, 1):
        for j, (ln, ang, yaw) in enumerate(((0.38, -76, 24), (0.30, -56, 38))):
            ob = flame_tongue("Ear%d_%d" % (side, j), ln, 0.07, 0.5, 0.02, MAT["flame"], parent=head_root, serr=0.16)
            ob.location = (0.0 + 0.04 * j, side * (0.27 + 0.01 * j), 0.10 + 0.07 * j)
            ob.rotation_euler = (0, math.radians(ang), math.radians(side * yaw))


def build_neck_scales(rows=18, per=28, first=0.02, step=0.075):
    """Overlapping shingle scales that follow the neck down the spine; the belly stays bare."""
    clear("NeckScale", "Shingle")
    at = neck_sampler()
    me = feather_mesh(0.17, 0.07, cup=0.14)
    for r in range(rows):
        pt, t, nn, bb, rad = at(first + r * step)
        rad += 0.004
        size = 1.0 - 0.40 * (r / max(1, rows - 1))
        for k in range(per):
            ang = 2 * math.pi * (k + 0.5 * (r % 2)) / per
            if r >= 2 and abs(ang - 1.5 * math.pi) < math.radians(40 if r < 10 else 52):
                continue  # keep the cream belly visible
            outward = math.cos(ang) * bb + math.sin(ang) * nn
            tilt = math.radians(15 + 1.2 * r)
            direction = -t * math.cos(tilt) + outward * math.sin(tilt)
            place_leaf(me, MAT["collar"], "NeckScale%d_%d" % (r, k), None, direction, outward,
                       tuple(pt + outward * rad), solid=0.008, scale=size)


def build_whiskers():
    """Long barbels from the snout that stream back past the head like tendrils."""
    clear("Whisker")
    for side in (-1, 1):
        for k, (dz, dy) in enumerate(((0.0, 0.0), (-0.07, 0.06))):
            tube("Whisker%d_%d" % (side, k),
                 [(X(1.02), side * 0.10, 0.12 + dz), (X(1.10), side * (0.22 + dy), 0.03 + dz),
                  (X(1.0), side * (0.36 + dy), -0.14 + dz), (0.58, side * (0.46 + dy), -0.28 + dz),
                  (0.18, side * (0.50 + dy), -0.26 + dz), (-0.22, side * (0.52 + dy), -0.10 + dz)],
                 0.018, 0.002, MAT["horn"], head_root, n=8, power=0.7)


def build_spikes(start=0.16, gap=0.3, stop_from_head=1.5):
    """Bony spikes along the spine, raked back, from near the tail up to where the neck scales begin."""
    clear("DorsalSpike")
    at = neck_sampler()
    pts, tang, nrm = compute_spine()
    total = sum((pts[i] - pts[i - 1]).length for i in range(1, len(pts)))
    s, k = stop_from_head, 0
    while s < total * (1 - start):
        pt, t, nn, bb, rad = at(s)
        u = 1 - s / total
        size = min(1.0, (u - start) / 0.12) * BODY_SCALE / 1.3
        direction = nn * math.cos(math.radians(42)) - t * math.sin(math.radians(42))
        spike("DorsalSpike%d" % k, pt + nn * rad * 0.9, direction, 0.045 * size, 0.24 * size, MAT["spike"],
              curl=0.25, up=-t)
        s += gap
        k += 1


def place_head():
    pts, tang, nrm = compute_spine()
    end, t_end, n_end = pts[-1], tang[-1], nrm[-1]
    x_axis = t_end
    z_axis = (n_end - x_axis * n_end.dot(x_axis)).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    pitch = Matrix.Rotation(math.radians(HEAD_PITCH), 4, "Y")  # about head-local Y: negative lifts the nose
    base = Matrix(((x_axis.x, y_axis.x, z_axis.x, end.x - t_end.x * 0.05),
                   (x_axis.y, y_axis.y, z_axis.y, end.y - t_end.y * 0.05),
                   (x_axis.z, y_axis.z, z_axis.z, end.z - t_end.z * 0.05),
                   (0, 0, 0, 1)))
    head_root.matrix_world = base @ pitch @ Matrix.Scale(HEAD_SCALE, 4)


def build_tail():
    clear("TailRoot", "TailFlame")
    pts, tang, nrm = compute_spine()
    tail_root = bpy.data.objects.new("TailRoot", None)
    link(tail_root)
    tail_root.location = pts[0] - tang[0] * 0.02
    tail_root.rotation_euler = (-tang[0]).to_track_quat("X", "Z").to_euler()
    for i, (lean, ln) in enumerate(((0, 0.9), (50, 0.6), (-50, 0.6))):
        ob = flame_tongue("TailFlame%d" % i, ln, 0.13, 0.4, 0.025, MAT["flame"], parent=tail_root, serr=0.14)
        ob.rotation_euler = (0, math.radians(lean - 90), 0)
        ob.location.y = (i - 1) * 0.03


def assemble_all():
    build_body()
    build_head_base()
    build_teeth()
    build_borders()
    build_tongue()
    build_beard()
    build_eyes()
    build_brows()
    build_horns()
    build_ears()
    build_whiskers()
    place_head()
    build_crest()
    build_neck_scales()
    build_spikes()
    build_tail()


# ------------------------------------------------------------------ lighting, camera, render
def hexlight(name, loc, color, energy, size, target):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = color[:3]
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def setup_camera_and_lights(center, ortho, res, key_from=(7, -6, 9), cam_offset=(0.0, -30.0, 0.0)):
    cam_target = bpy.data.objects.get("CamTarget")
    if cam_target is None:
        cam_target = bpy.data.objects.new("CamTarget", None)
        link(cam_target)
    cam = bpy.data.objects.get("Cam")
    if cam is None:
        cd = bpy.data.cameras.new("Cam")
        cd.type = "ORTHO"
        cam = bpy.data.objects.new("Cam", cd)
        link(cam)
        con = cam.constraints.new("TRACK_TO")
        con.target = cam_target
        con.track_axis = "TRACK_NEGATIVE_Z"
        con.up_axis = "UP_Y"
    cam_target.location = center
    cam.location = Vector(center) + Vector(cam_offset)
    cam.data.ortho_scale = ortho
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = res
    clear("Moon", "Rim", "Fill")
    c = Vector(center)
    hexlight("Moon", c + Vector(key_from), (0.92, 0.84, 0.62), 900, 8, c)
    hexlight("Rim", c + Vector((-8, 6, 6)), (0.55, 0.65, 0.9), 500, 8, c)
    hexlight("Fill", c + Vector((0, -10, -3)), (0.6, 0.7, 0.9), 160, 10, c)


def setup_world():
    if scene.world is None:
        world = bpy.data.worlds.new("Night")
        scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes["Background"]
        bg.inputs["Color"].default_value = hexc("#1B2140")
        bg.inputs["Strength"].default_value = 0.55


if not NAGA_LIVE:
    assemble_all()
    setup_world()
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.film_transparent = os.environ.get("NAGA_BG", "0") != "1"
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = int(os.environ.get("NAGA_RES", "100"))
    os.makedirs(OUT, exist_ok=True)
    head_c = head_root.matrix_world @ Vector((0.40, 0, 0.30))

    def render(path):
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)

    if WHAT in ("head", "both"):
        setup_camera_and_lights(head_c, 4.2, (1600, 1200))
        render(os.path.join(OUT, "naga_head.png"))
        setup_camera_and_lights(head_c, 4.2, (1600, 1200), key_from=(9, -4, 8), cam_offset=(16.0, -24.0, 6.0))
        render(os.path.join(OUT, "naga_head_three_quarter.png"))
    if WHAT in ("full", "both"):
        setup_camera_and_lights((-0.2, 0.0, 2.2), 12.5, (1920, 1280))
        render(os.path.join(OUT, "naga_full.png"))
    if WHAT == "menu":
        # Two passes from the menu's own framing: the part in front of the palace plane (y < 0) and the part behind it.
        # Laid over and under the palace they recombine exactly, because only camera rays are clipped.
        import json
        from bpy_extras.object_utils import world_to_camera_view
        setup_camera_and_lights((0.0, 0.0, 0.0), 1920 / MENU_PPU, (1920, 1080))
        clear("Moon", "Rim", "Fill")
        hexlight("Moon", (4.6, 9.0, 3.4), (0.95, 0.87, 0.68), 2600, 7, (1.2, 0.0, 1.2))       # rim from the moon
        hexlight("Rim", (-7.0, -10.0, 7.0), (0.60, 0.68, 0.95), 700, 10, (0.5, 0.0, 0.5))     # cool sky key
        hexlight("Fill", (0.5, -8.0, -4.5), (0.85, 0.58, 0.30), 380, 9, (0.5, 0.0, -1.5))     # lantern glow below
        cam = scene.camera
        cam.data.clip_start, cam.data.clip_end = 0.1, 30.0
        render(os.path.join(OUT, "menu_front.png"))
        cam.data.clip_start, cam.data.clip_end = 30.0, 200.0
        render(os.path.join(OUT, "menu_back.png"))
        bpy.context.view_layer.update()
        marks = {}
        for name in ("Gem-1", "Gem1", "ForeheadGem", "Pupil-1", "Pupil1"):
            ob = bpy.data.objects[name]
            vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
            c = sum(vs, Vector()) / len(vs)
            p = world_to_camera_view(scene, cam, c)
            marks[name] = {"x": round(p.x * 1920, 1), "y": round((1 - p.y) * 1080, 1), "front": c.y < 0,
                           "depth": round(c.y, 3)}
        with open(os.path.join(OUT, "menu_marks.json"), "w") as fh:
            json.dump(marks, fh, indent=1)
        print("MARKS", marks)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "naga_menu.blend" if WHAT == "menu" else "naga.blend"))
    print("NAGA DONE")
