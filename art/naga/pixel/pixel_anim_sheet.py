"""Pixelize the idle-loop frames from pixel_anim.py together, so every frame shares one palette (no colour flicker).

    python3 pixel_anim_sheet.py <frames dir> <out dir> [fps=8]

All frames are packed into one sheet with transparent gaps and pixelized in one pass (24 colours, eye red and bone
reserved, selective outline), then cut apart again. Writes, in <out dir>:
- idle_00.png ...: the game-ready 480x270 frames (1x, transparent);
- idle_front_00.png / idle_back_00.png ...: the same split at the palace plane, for the menu;
- idle_plain_x3.gif: the dragon alone on a plain background at 3x;
- idle_menu.gif: the loop in the pixel menu (scene layers from pixel/menu/layers), full 1920x1080.
"""
import glob
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixelize import BONE, process  # noqa: E402

SRC, OUT = sys.argv[1:3]
FPS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
EYE = "#E8452A"
W, H, GAP, COLS = 480, 270, 4, 4
os.makedirs(OUT, exist_ok=True)

alls = sorted(glob.glob(os.path.join(SRC, "f*_all.png")))
n = len(alls)
rows = (n + COLS - 1) // COLS
sheet = Image.new("RGBA", (COLS * (W + GAP), rows * (H + GAP)), (0, 0, 0, 0))
for k, p in enumerate(alls):
    sheet.paste(Image.open(p).convert("RGBA"), ((k % COLS) * (W + GAP), (k // COLS) * (H + GAP)))
px_sheet, body = process(sheet, colors=24, clean=1, sel_outline=True, glow=EYE, bone=BONE)

frames = []
for k, p in enumerate(alls):
    box = ((k % COLS) * (W + GAP), (k // COLS) * (H + GAP))
    fr = px_sheet.crop(box + (box[0] + W, box[1] + H))
    fr.save(os.path.join(OUT, "idle_%02d.png" % k))
    frames.append(fr)
    # split at the palace plane the way pixel_menu.py does: outline pixels follow the body pixel they border
    front = Image.open(p.replace("_all", "_front")).convert("RGBA").getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    bmask = body.crop(box + (box[0] + W, box[1] + H)).load()
    F, S = front.load(), fr.load()
    lf, lb = Image.new("RGBA", (W, H), (0, 0, 0, 0)), Image.new("RGBA", (W, H), (0, 0, 0, 0))
    LF, LB = lf.load(), lb.load()
    for y in range(H):
        for x in range(W):
            if not S[x, y][3]:
                continue
            if bmask[x, y]:
                inf = bool(F[x, y])
            else:
                inf = any(0 <= x + dx < W and 0 <= y + dy < H and F[x + dx, y + dy]
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            (LF if inf else LB)[x, y] = S[x, y]
    lf.save(os.path.join(OUT, "idle_front_%02d.png" % k))
    lb.save(os.path.join(OUT, "idle_back_%02d.png" % k))

# the dragon alone, on a plain background, 3x
bbox = None
for fr in frames:
    b = fr.getchannel("A").getbbox()
    bbox = b if bbox is None else (min(bbox[0], b[0]), min(bbox[1], b[1]), max(bbox[2], b[2]), max(bbox[3], b[3]))
bbox = (bbox[0] - 6, bbox[1] - 6, bbox[2] + 6, bbox[3] + 6)
plain = []
for fr in frames:
    bg = Image.new("RGBA", (bbox[2] - bbox[0], bbox[3] - bbox[1]), (120, 126, 136, 255))
    bg.alpha_composite(fr.crop(bbox))
    plain.append(bg.resize((bg.width * 3, bg.height * 3), Image.NEAREST).convert("RGB"))
ms = int(1000 / FPS)
plain[0].save(os.path.join(OUT, "idle_plain_x3.gif"), save_all=True, append_images=plain[1:], duration=ms, loop=0,
              optimize=False, disposal=1)

# the loop in the pixel menu
L = os.path.join(HERE, "menu", "layers", "px_%s.png")
far, palace, wall, hero, tr, tl = (Image.open(L % n_).convert("RGBA") for n_ in
                                   ("far", "palace", "wall", "hero", "tree_r", "tree_l"))
menu = []
for k in range(n):
    m = far.copy()
    m.alpha_composite(Image.open(os.path.join(OUT, "idle_back_%02d.png" % k)).resize((W * 4, H * 4), Image.NEAREST))
    m.alpha_composite(palace)
    m.alpha_composite(Image.open(os.path.join(OUT, "idle_front_%02d.png" % k)).resize((W * 4, H * 4), Image.NEAREST))
    for lay in (wall, hero, tr, tl):
        m.alpha_composite(lay)
    menu.append(m.resize((960, 540), Image.NEAREST).convert("RGB"))
menu[0].save(os.path.join(OUT, "idle_menu.gif"), save_all=True, append_images=menu[1:], duration=ms, loop=0,
             optimize=False, disposal=1)
print("wrote", n, "frames to", OUT, "bbox", bbox)
