"""The toon look used for the pixel-art naga, applied to a naga built by build_naga.py.

    g = namespace build_naga.py was exec'd in (NAGA_LIVE = True), after assemble_all() or bind_existing()
    pixel_style.apply(g)

Never run this on art/naga/naga.blend: the 3D naga stays as it is; pixel work lives in its own files.
"""
import math

import bpy
from mathutils import Vector

# Body colours, a little brighter and more saturated than the 3D naga, as the pixel references are. The skin gets a
# regular scale pattern and the belly segmented plates, sized to read at sprite resolution (cells ~0.15 world units).
FLAT = {"NagaSkin": "#2E7A58", "NagaHead": "#317E5D", "NagaBelly": "#DCCFA2"}
PATTERN = {"NagaSkin": ("scales", "#1C4C3A"), "NagaBelly": ("plates", "#A89566")}
SCALE_CELLS = (5.0, 3.5)   # scales around (UV u is 0..1 round the body) and per UV v unit (0.9 world along)
PLATES_PER_V = 7.5         # belly plates per UV v unit
NOSE_HORN = "#F6F3EC"      # bone white; the toon ramp shades it to cool grey on the shadow side
# Shading steps, hue-shifted like the references: cool blue-purple shadows, warm highlights.
RAMP = [(0.0, (0.30, 0.33, 0.48)), (0.22, (0.62, 0.66, 0.74)), (0.62, (1.0, 1.0, 0.94)), (0.9, (1.12, 1.08, 0.9))]


def _lin(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


def toon_materials():
    """Every material shades in three flat steps (Diffuse -> Shader to RGB -> constant ramp x base -> Emission)."""
    for m in bpy.data.materials:
        if not m.use_nodes or m.name == "Gem":
            continue
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if bsdf is None or out is None or any(n.type == "SHADERTORGB" for n in nt.nodes):
            continue
        base_in = bsdf.inputs["Base Color"]
        if m.name in FLAT:
            for link in list(base_in.links):
                nt.links.remove(link)
            base_in.default_value = _lin(FLAT[m.name])
        src = base_in.links[0].from_socket if base_in.links else None
        if m.name in PATTERN:
            src = _pattern(nt, PATTERN[m.name][0], FLAT[m.name], PATTERN[m.name][1])
        diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
        to_rgb = nt.nodes.new("ShaderNodeShaderToRGB")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        e = ramp.color_ramp.elements
        e[0].position, e[0].color = RAMP[0][0], RAMP[0][1] + (1,)
        e[1].position, e[1].color = RAMP[-1][0], RAMP[-1][1] + (1,)
        for pos, col in RAMP[1:-1]:
            el = e.new(pos)
            el.color = col + (1,)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        emis = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(diff.outputs["BSDF"], to_rgb.inputs["Shader"])
        nt.links.new(to_rgb.outputs["Color"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], mix.inputs["A"])
        if src is not None:
            nt.links.new(src, mix.inputs["B"])
        else:
            mix.inputs["B"].default_value = base_in.default_value
        nt.links.new(mix.outputs["Result"], emis.inputs["Color"])
        for link in list(out.inputs["Surface"].links):
            nt.links.remove(link)
        nt.links.new(emis.outputs["Emission"], out.inputs["Surface"])
    gem = bpy.data.materials["Gem"].node_tree.nodes["Principled BSDF"]
    gem.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)  # glow only, so it stays red instead of clipping
    gem.inputs["Specular IOR Level"].default_value = 0.0
    gem.inputs["Roughness"].default_value = 1.0
    gem.inputs["Emission Color"].default_value = (1.0, 0.07, 0.02, 1)
    gem.inputs["Emission Strength"].default_value = 1.0


def _pattern(nt, kind, base_hex, line_hex):
    """Base colour with dark scale outlines (Voronoi cell edges) or belly plate seams (stripes along the body)."""
    uv = nt.nodes.new("ShaderNodeTexCoord")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = _lin(base_hex)
    mix.inputs["B"].default_value = _lin(line_hex)
    test = nt.nodes.new("ShaderNodeMath")
    test.operation = "LESS_THAN"
    if kind == "scales":
        # regular staggered rows, like the tidy scale rows of the pixel references (not random crackle)
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (SCALE_CELLS[0], SCALE_CELLS[1], 1.0)
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.offset, brick.offset_frequency = 0.5, 2
        brick.inputs["Scale"].default_value = 1.0
        brick.inputs["Brick Width"].default_value = 1.0
        brick.inputs["Row Height"].default_value = 1.0
        brick.inputs["Mortar Size"].default_value = 0.09
        brick.inputs["Mortar Smooth"].default_value = 0.0
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], brick.inputs["Vector"])
        test.operation = "GREATER_THAN"
        nt.links.new(brick.outputs["Fac"], test.inputs[0])
        test.inputs[1].default_value = 0.5
    else:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = PLATES_PER_V
        fr = nt.nodes.new("ShaderNodeMath")
        fr.operation = "FRACT"
        nt.links.new(uv.outputs["UV"], sep.inputs["Vector"])
        nt.links.new(sep.outputs["Y"], mul.inputs[0])
        nt.links.new(mul.outputs["Value"], fr.inputs[0])
        nt.links.new(fr.outputs["Value"], test.inputs[0])
        test.inputs[1].default_value = 0.2
    nt.links.new(test.outputs["Value"], mix.inputs["Factor"])
    return mix.outputs["Result"]


def sprite_cleanups(g):
    """Details that turn to noise at sprite size: one thick barbel a side, a bigger bone-white nose horn, fewer
    bigger collar scales, bigger eyes."""
    X, head_root, MAT = g["X"], g["head_root"], g["MAT"]
    g["clear"]("Whisker")
    for side in (-1, 1):
        g["tube"]("Whisker%d_0" % side,
                  [(X(1.02), side * 0.10, 0.12), (X(1.10), side * 0.22, 0.03), (X(1.0), side * 0.36, -0.14),
                   (0.58, side * 0.46, -0.28), (0.18, side * 0.50, -0.26), (-0.22, side * 0.52, -0.10)],
                  0.034, 0.006, MAT["horn"], head_root, n=8, power=0.7)
    # The nose horn: 1.5x long and 1.4x thick so it reads at sprite size, and bone white, so it never merges with the
    # dark barbels that start just in front of it (same colour, they read as one hair going through the nose).
    g["clear"]("NoseHorn")
    bone = g["principled"]("NoseHornBone", NOSE_HORN, rough=0.6)
    g["spike"]("NoseHorn", g["surf"](X(0.97), 90, -0.01), (-0.35, 0.0, 1.0), 0.042, 0.21, bone, head_root,
               curl=0.3, up=(-1, 0, 0))
    g["clear"]("NeckScale")
    at = g["neck_sampler"]()
    me = g["feather_mesh"](0.30, 0.13, cup=0.12)
    rows, per, step = 9, 14, 0.15
    for r in range(rows):
        pt, t, nn, bb, rad = at(0.03 + r * step)
        size = 1.0 - 0.35 * r / (rows - 1)
        for k in range(per):
            ang = 2 * math.pi * (k + 0.5 * (r % 2)) / per
            if r >= 1 and abs(ang - 1.5 * math.pi) < math.radians(44):
                continue
            o = math.cos(ang) * bb + math.sin(ang) * nn
            tilt = math.radians(16 + 1.5 * r)
            g["place_leaf"](me, MAT["collar"], "NeckScale%d_%d" % (r, k), None,
                            -t * math.cos(tilt) + o * math.sin(tilt), o, tuple(pt + o * (rad + 0.006)),
                            solid=0.01, scale=size)
    for side in (-1, 1):
        for name, k in (("Gem%d" % side, 1.6), ("Pupil%d" % side, 1.2)):
            ob = bpy.data.objects[name]
            c = sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
            for v in ob.data.vertices:
                v.co = c + (v.co - c) * k


def sun(direction, energy=3.2, color=(1.0, 1.0, 1.0)):
    """The single toon light. `direction` is where the light travels (from the light toward the subject)."""
    ob = bpy.data.objects.get("PixelSun")
    if ob is None:
        ld = bpy.data.lights.new("PixelSun", "SUN")
        ob = bpy.data.objects.new("PixelSun", ld)
        bpy.context.scene.collection.objects.link(ob)
    ob.data.energy = energy
    ob.data.color = color
    ob.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
    for n in ("Moon", "Rim", "Fill"):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = True
    return ob


def apply(g):
    toon_materials()
    sprite_cleanups(g)
    toon_materials()  # materials the clean-ups added (the nose horn's bone)
