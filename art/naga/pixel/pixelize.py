"""Turn small Blender renders of the naga into pixel-art sprites.

    python3 pixelize.py <in.png> <out stem> [--colors N | --palette naga] [--punch] [--clean N] [--sel-outline]
                        [--scale 5]

Steps: hard alpha edge (no soft fringe), optional contrast/saturation punch, colour reduction (adaptive N colours or
the fixed naga palette, no dithering), optional clean-up of stray single pixels, a 1 px outline (flat dark, or with
--sel-outline a dark shade of the colour it borders), then <stem>.png (game-ready, 1x, transparent) and
<stem>_x<scale>.png (nearest-neighbour enlargement on a night background, for looking at).
"""
import argparse

from PIL import Image, ImageEnhance

OUTLINE = (14, 11, 20)
BONE = ("#E9E6DE", "#A3A5AD")  # nose horn and teeth: bone white and its cool grey shade
NIGHT = (27, 33, 64)
# A fixed palette sampled from the naga's materials: outline, greens, belly, gold collar, black hair, horn, eyes,
# teeth and tongue.
NAGA_PALETTE = [
    "#0E0B14", "#0F2A22", "#1F4A3B", "#2F6B55", "#4E8F72", "#8C7F5A", "#D9CDA4", "#6B3A14", "#B8742A", "#E8B85A",
    "#15121A", "#2A2530", "#7A6A4C", "#CDB98A", "#E0461F", "#FF9A3C", "#F1E8D2", "#7A2A20",
]


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette_image(colors):
    pal = Image.new("P", (1, 1))
    flat = [c for rgb in colors for c in rgb]
    pal.putpalette(flat + flat[:3] * (256 - len(colors)))
    return pal


def process(im, colors=24, palette=None, punch=False, clean=0, sel_outline=False, glow=None, bone=None):
    """RGBA render -> (pixel sprite RGBA with outline, body mask). See the module notes for the steps.

    glow: hex colour kept for the glowing eyes. bone: (light hex, shade hex) kept for bright near-neutral pixels
    (the white nose horn, teeth), which colour reduction would otherwise fold into the belly's khaki.
    """
    alpha = im.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    rgb = im.convert("RGB")
    if punch:
        rgb = ImageEnhance.Contrast(rgb).enhance(1.18)
        rgb = ImageEnhance.Color(rgb).enhance(1.2)

    # reduce colours using only the sprite's own pixels, so the background does not take palette slots
    bg = Image.new("RGB", rgb.size, (0, 0, 0))
    bg.paste(rgb, mask=alpha)
    if palette == "naga":
        q = bg.quantize(palette=palette_image([hex_rgb(h) for h in NAGA_PALETTE]), dither=Image.Dither.NONE)
    else:
        q = bg.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    flat = q.convert("RGB")
    w, h = flat.size
    A = alpha.load()
    if glow:
        # glowing eyes keep their own red; palette reduction would otherwise merge them with the gold
        G = hex_rgb(glow)
        R, F0 = rgb.load(), flat.load()
        for y in range(h):
            for x in range(w):
                r_, g_, b_ = R[x, y]
                if A[x, y] and r_ > 170 and r_ - g_ > 95 and r_ - b_ > 110:
                    F0[x, y] = G
    if bone:
        light, shade = hex_rgb(bone[0]), hex_rgb(bone[1])
        R, F0 = rgb.load(), flat.load()
        for y in range(h):
            for x in range(w):
                mx, mn = max(R[x, y]), min(R[x, y])
                if A[x, y] and mn > 125 and mx - mn < 0.18 * mx:
                    F0[x, y] = light if mx > 205 else shade
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

    # stray pixels: a pixel that matches none of its neighbours, where 3+ neighbours agree, takes their colour
    for _ in range(clean):
        src = flat.copy()
        F, Sx = flat.load(), src.load()
        for y in range(h):
            for x in range(w):
                if not A[x, y]:
                    continue
                nb = [Sx[x + dx, y + dy] for dx, dy in N4
                      if 0 <= x + dx < w and 0 <= y + dy < h and A[x + dx, y + dy]]
                if len(nb) < 3 or Sx[x, y] in nb:
                    continue
                best = max(set(nb), key=nb.count)
                if nb.count(best) >= 3:
                    F[x, y] = best

    sprite = Image.new("RGBA", flat.size, (0, 0, 0, 0))
    sprite.paste(flat, mask=alpha)
    # 1 px outline round the silhouette (4-neighbours)
    S = sprite.load()
    F = flat.load()
    for y in range(h):
        for x in range(w):
            if A[x, y]:
                continue
            nb = [F[x + dx, y + dy] for dx, dy in N4 if 0 <= x + dx < w and 0 <= y + dy < h and A[x + dx, y + dy]]
            if not nb:
                continue
            if sel_outline:
                c = max(set(nb), key=nb.count)
                S[x, y] = tuple(int(c[i] * 0.4 + OUTLINE[i] * 0.6) for i in range(3)) + (255,)
            else:
                S[x, y] = OUTLINE + (255,)
    return sprite, alpha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("stem")
    ap.add_argument("--colors", type=int, default=24)
    ap.add_argument("--palette", choices=["naga"], default=None)
    ap.add_argument("--punch", action="store_true")
    ap.add_argument("--clean", type=int, default=0, help="passes of stray-pixel clean-up")
    ap.add_argument("--sel-outline", action="store_true", help="outline in a dark shade of the neighbouring colour")
    ap.add_argument("--glow", default=None, help="hex colour reserved for glowing eye pixels (strong red, little green)")
    ap.add_argument("--scale", type=int, default=5)
    a = ap.parse_args()

    sprite, _ = process(Image.open(a.src).convert("RGBA"), a.colors, a.palette, a.punch, a.clean, a.sel_outline,
                        a.glow)
    sprite.save(a.stem + ".png")
    w, h = sprite.size
    big = sprite.resize((w * a.scale, h * a.scale), Image.NEAREST)
    view = Image.new("RGBA", big.size, NIGHT + (255,))
    view.alpha_composite(big)
    view.convert("RGB").save("%s_x%d.png" % (a.stem, a.scale))
    colours = {px[:3] for px in sprite.get_flattened_data() if px[3]}
    print("wrote", a.stem, "size", sprite.size, "colours", len(colours))


if __name__ == "__main__":
    main()
