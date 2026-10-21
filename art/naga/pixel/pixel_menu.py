"""Pixel-art version of the main menu, for comparing with the current one (nothing is published).

    python3 pixel_menu.py <pixel naga render dir> <MainMenu.source.dc.html> <work dir> <out dir>

1. The naga's back and front passes (480x270) are pixelized together, so no outline cuts across the body where it
   passes from behind the palace to in front, then split again and enlarged 4x onto the menu's own pixel grid.
2. They go into a local copy of the menu (static, animations frozen, idle zoom off so the grid stays aligned).
3. Headless Chrome shoots the scene without text, the text alone, and everything together.
4. The scene is shrunk to 480x270 and its colours reduced; the text is laid over it smooth (the way Burmese stays
   readable), and a second version pixelizes the text too.
"""
import os
import re
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixelize import BONE, hex_rgb, process  # noqa: E402

RDIR, SRC, WORK, OUT = sys.argv[1:5]
MENU = os.path.join(os.path.dirname(HERE), "menu")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCALE, W, H = 4, 480, 270
FRAME_COLOURS = 48
EYE = "#E8452A"  # reserved in every palette so the glowing eyes never merge into the gold
os.makedirs(WORK, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# 1. naga layers -------------------------------------------------------------------------------------------------
back = Image.open(os.path.join(RDIR, "menu_back.png")).convert("RGBA")
front = Image.open(os.path.join(RDIR, "menu_front.png")).convert("RGBA")
both = back.copy()
both.alpha_composite(front)
sprite, body = process(both, colors=24, clean=1, sel_outline=True, glow=EYE, bone=BONE)
front_mask = front.getchannel("A").point(lambda v: 255 if v >= 110 else 0).load()
B, S = body.load(), sprite.load()
layer_f = Image.new("RGBA", (W, H), (0, 0, 0, 0))
layer_b = Image.new("RGBA", (W, H), (0, 0, 0, 0))
LF, LB = layer_f.load(), layer_b.load()
for y in range(H):
    for x in range(W):
        if not S[x, y][3]:
            continue
        if B[x, y]:
            in_front = bool(front_mask[x, y])
        else:  # an outline pixel goes with the body pixel it borders
            in_front = any(0 <= x + dx < W and 0 <= y + dy < H and front_mask[x + dx, y + dy]
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        (LF if in_front else LB)[x, y] = S[x, y]
paths = {}
for name, im in (("front", layer_f), ("back", layer_b)):
    paths[name] = os.path.join(WORK, "naga_%s_x4.png" % name)
    im.resize((W * SCALE, H * SCALE), Image.NEAREST).save(paths[name])

# 2. local menu copy ---------------------------------------------------------------------------------------------
tmp_r = os.path.join(WORK, "integrate_in")
os.makedirs(tmp_r, exist_ok=True)
for name in ("front", "back"):
    Image.open(paths[name]).save(os.path.join(tmp_r, "menu_%s.png" % name))
subprocess.run(["cp", os.path.join(RDIR, "menu_marks.json"), tmp_r], check=True)
dc = os.path.join(WORK, "MainMenu.pixel.dc.html")
subprocess.run([sys.executable, "-I", os.path.join(MENU, "menu_integrate.py"), tmp_r, SRC, dc,
                os.path.join(WORK, "unused_assets"), "FRONTURL", "BACKURL"], check=True, capture_output=True)
html = open(dc, encoding="utf-8").read()
for name, url in (("front", "FRONTURL"), ("back", "BACKURL")):
    html = re.sub(r'src="%s" alt="" style="[^"]*"' % url,
                  'src="%s" alt="" style="left: 0px; top: 0px; width: 1920px; height: 1080px"' % paths[name], html)
html = re.sub(r'\s*<div class="naga-glint"[^>]*></div>', "", html)  # the eyes already glow in the sprite
open(dc, "w", encoding="utf-8").write(html)
static = os.path.join(WORK, "static.html")
subprocess.run([sys.executable, "-I", os.path.join(MENU, "preview_menu.py"), dc, static], check=True,
               capture_output=True)
page = open(static, encoding="utf-8").read()
for start in ('<div style="position: absolute; left: 120px; top: 96px; width: 1100px">',
              '<div style="position: absolute; left: 60px; top: 500px; width: 820px; height: 470px">',
              '<div style="position: absolute; left: 120px; bottom: 44px;',
              '<div style="position: absolute; right: 120px; bottom: 40px;'):
    assert page.count(start) == 1, start
    page = page.replace(start, start.replace("<div ", "<div data-ui=\"1\" "))
page = page.replace("opacity: 0.12; mix-blend-mode: overlay", "opacity: 0; mix-blend-mode: overlay")  # no grain
# frozen, no idle zoom, and no blur or glow on the naga's layers, so its pixels stay on the 4 px grid
FREEZE = ("*{animation:none!important;transition:none!important}.cam{transform:none!important}"
          ".layer:has(.naga-live){filter:none!important}.naga-img{filter:none!important}")
variants = {
    "scene": FREEZE + "[data-ui]{visibility:hidden!important}",
    "ui": FREEZE + ".mm>*:not([data-ui]){visibility:hidden!important}.mm,body{background:transparent!important}",
    "full": FREEZE,
}
shots = {}
for name, css in variants.items():
    f = os.path.join(WORK, "page_%s.html" % name)
    open(f, "w", encoding="utf-8").write(page.replace("</head>", "<style>%s</style></head>" % css))
    shots[name] = os.path.join(WORK, "shot_%s.png" % name)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--user-data-dir=" + os.path.join(WORK, "chrome"), "--window-size=1920,1080",
                    "--default-background-color=00000000", "--virtual-time-budget=8000",
                    "--screenshot=" + shots[name], "file://" + f], check=True, capture_output=True)


# 4. pixelize the frame --------------------------------------------------------------------------------------------
def pixel_frame(path):
    small = Image.open(path).convert("RGB").resize((W, H), Image.BOX)
    q = small.quantize(colors=FRAME_COLOURS - 1, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:3 * (FRAME_COLOURS - 1)] + list(hex_rgb(EYE))  # adaptive colours plus the eye red
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(pal + pal[:3] * (256 - FRAME_COLOURS))
    q = small.quantize(palette=pal_img, dither=Image.Dither.NONE)
    return q.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST)


scene = pixel_frame(shots["scene"]).convert("RGBA")
scene.alpha_composite(Image.open(shots["ui"]).convert("RGBA"))
scene.convert("RGB").save(os.path.join(OUT, "pixel_menu_smooth_text.png"))
pixel_frame(shots["full"]).save(os.path.join(OUT, "pixel_menu_pixel_text.png"))
print("wrote", OUT)
