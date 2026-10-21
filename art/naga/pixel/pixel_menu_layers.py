"""Bake the main menu's scene into separate pixel-art layers that share one palette, for the live pixel menu.

    python3 pixel_menu_layers.py <pixel_menu.py work dir> <out dir>

Uses the static page and screenshots pixel_menu.py left in its work dir. Each group of layers is shot alone on a
transparent background (live effects hidden: lanterns, light streak, notebook glow), shrunk to 480x270, given hard
edges, mapped to the shared palette (adaptive colours of the whole scene plus the reserved eye red) and enlarged 4x
back onto the menu's pixel grid. The naga layers from pixel_menu.py are mapped to the same palette plus four colours
kept for the naga alone (its two main golds, bone white and grey), so the rest of the scene keeps all its slots.
"""
import colorsys
import os
import re
import subprocess
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixelize import BONE, hex_rgb  # noqa: E402

WORK, OUT = sys.argv[1:3]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCALE, W, H = 4, 480, 270
COLOURS = 48
EYE = "#E8452A"
os.makedirs(OUT, exist_ok=True)

# layer order in the page: 1 sky, 2 moon, 3 bats, 4 hills, 5 back mist, 6 naga behind, 7 palace, 8 light shafts,
# 9 naga in front, 10 wall, 11 hero, 12 embers, 13 front mist, 14 trees
BAKE = {
    "far": ({1, 2, 4}, ".streak"),
    "palace": ({7}, ".lantern"),
    "wall": ({10}, ".lantern,.pool,[data-live]"),
    "hero": ({11}, ""),
    "tree_r": ({14}, ".sway-l"),
    "tree_l": ({14}, ".sway-r"),
}

page = open(os.path.join(WORK, "static.html"), encoding="utf-8").read()
n = [0]


def tag(m):
    n[0] += 1
    return '<div class="layer" data-layer="%d"' % n[0]


page = re.sub(r'<div class="layer"', tag, page)
assert n[0] == 14, n[0]
glow = '<div style="position: absolute; left: 1314px; top: 800px; width: 240px; height: 120px; border-radius: 50%;'
assert page.count(glow) == 1
page = page.replace(glow, glow.replace("<div ", '<div data-live="1" '))
BASE = ("*{animation:none!important;transition:none!important}.cam{transform:none!important}"
        ".layer{filter:none!important}.mm>*:not(.cam){visibility:hidden!important}"
        ".mm,body{background:transparent!important}")


def naga_golds(n=2):
    """The naga's most used gold tones (collar scales): reserved, or the scene's median cut folds them into moon beige."""
    count = Counter()
    for name in ("front", "back"):
        im = Image.open(os.path.join(WORK, "naga_%s_x4.png" % name)).convert("RGBA").resize((W, H), Image.NEAREST)
        count.update(p[:3] for p in im.get_flattened_data() if p[3])
    golds = []
    for rgb, _ in count.most_common():
        h, s_, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
        if 25 <= h * 360 <= 45 and s_ > 0.45 and v > 0.4:
            golds.append(rgb)
        if len(golds) == n:
            break
    return golds


# shared palette from the whole pixel scene (no text) plus the eye red; the naga also gets its own reserved colours,
# which only its layers may use (the hero's cream robe or red scarf would otherwise snap to them)
scene = Image.open(os.path.join(WORK, "shot_scene.png")).convert("RGB").resize((W, H), Image.BOX)
pal = scene.quantize(colors=COLOURS - 1, method=Image.Quantize.MEDIANCUT,
                     dither=Image.Dither.NONE).getpalette()[:3 * (COLOURS - 1)] + list(hex_rgb(EYE))
naga_only = naga_golds() + [hex_rgb(h) for h in BONE]
print("naga only", ["#%02X%02X%02X" % tuple(rgb) for rgb in naga_only])


def palette(flat):
    p = Image.new("P", (1, 1))
    p.putpalette(flat + flat[:3] * (256 - len(flat) // 3))
    return p


PAL = palette(pal)
PAL_NAGA = palette(pal + [c for rgb in naga_only for c in rgb])


def to_pixels(rgba_small, pal_img=PAL):
    """Hard edges and the shared palette, then 4x onto the grid."""
    alpha = rgba_small.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    flat = rgba_small.convert("RGB").quantize(palette=pal_img, dither=Image.Dither.NONE).convert("RGB")
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(flat, mask=alpha)
    return out.resize((W * SCALE, H * SCALE), Image.NEAREST)


for name, (layers, hide) in BAKE.items():
    keep = ",".join('[data-layer="%d"]' % i for i in sorted(layers))
    css = BASE + ".layer:not(%s){visibility:hidden!important}" % keep
    if hide:
        css += "%s{visibility:hidden!important}" % hide
    f = os.path.join(WORK, "layer_%s.html" % name)
    open(f, "w", encoding="utf-8").write(page.replace("</head>", "<style>%s</style></head>" % css))
    shot = os.path.join(WORK, "layer_%s.png" % name)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--user-data-dir=" + os.path.join(WORK, "chrome"), "--window-size=1920,1080",
                    "--default-background-color=00000000", "--virtual-time-budget=8000",
                    "--screenshot=" + shot, "file://" + f], check=True, capture_output=True)
    small = Image.open(shot).convert("RGBA").convert("RGBa").resize((W, H), Image.BOX).convert("RGBA")
    to_pixels(small).save(os.path.join(OUT, "px_%s.png" % name), optimize=True)
    print("baked", name)

for name in ("front", "back"):
    big = Image.open(os.path.join(WORK, "naga_%s_x4.png" % name)).convert("RGBA")
    to_pixels(big.resize((W, H), Image.NEAREST), PAL_NAGA).save(os.path.join(OUT, "px_naga_%s.png" % name),
                                                                  optimize=True)
    print("mapped naga", name)
