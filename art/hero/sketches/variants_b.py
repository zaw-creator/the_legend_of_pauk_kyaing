"""Colourways for costume option B (Bagan traveller), with each one shown small on the game's night colours.

    python3 variants_b.py <out.png>
"""
import os
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_figures import option_b  # noqa: E402

OUT = sys.argv[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RED, RED_D = "#A94530", "#7E2F21"
INDIGO, INDIGO_D = "#3D4E78", "#2E3B5E"
TURMERIC, TURMERIC_D = "#D9A441", "#B88430"

# name, dyes, colourway
WAYS = [
    ("1. Original", "undyed cotton, indigo, red", {}),
    ("2. Turmeric and indigo", "turmeric yellow top, deep indigo check",
     dict(blouse=TURMERIC, blouse_line=TURMERIC_D, blouse_fold="#C4923A", paso=INDIGO_D, paso_check="#44557F",
          paso_panel="#232D4A")),
    ("3. Undyed and cutch", "cutch brown check, indigo sash",
     dict(blouse="#E3D6BC", blouse_line="#C2B38F", blouse_fold="#CFC0A0", paso="#6B4A33", paso_check="#8A6446",
          paso_panel="#523826", sash=INDIGO, sash_end=INDIGO_D, tie=INDIGO)),
    ("4. Leaf green", "white top, green check (indigo over yellow)",
     dict(blouse="#F2EEE6", blouse_line="#CFC8B8", blouse_fold="#DDD6C8", paso="#2F5D4A", paso_check="#4A7A62",
          paso_panel="#234737")),
    ("5. Indigo top", "indigo top, red-brown check, yellow sash",
     dict(blouse=INDIGO, blouse_line=INDIGO_D, blouse_fold="#34436A", paso="#7A2E2A", paso_check="#9A4A3E",
          paso_panel="#5E2220", sash=TURMERIC, sash_end=TURMERIC_D, tie=TURMERIC)),
    ("6. Charcoal and lac", "pale grey top, charcoal check, lac crimson",
     dict(blouse="#C9CFD8", blouse_line="#A8B0BC", blouse_fold="#B8C0CB", paso="#2A2628", paso_check="#46404A",
          paso_panel="#1E1B1D", sash="#9E2A3A", sash_end="#7A1E2C", tie="#9E2A3A")),
    ("7. Sky and plum", "pale indigo top, plum check, cream sash",
     dict(blouse="#9FB2CF", blouse_line="#7F93B3", blouse_fold="#8EA2C2", paso="#5E2433", paso_check="#7D3445",
          paso_panel="#46192A", sash="#E9DFC8", sash_end="#CFC0A0", tie="#E9DFC8")),
    ("8. Night-proof", "bright cream, teal check, vermilion",
     dict(blouse="#F1E6CC", blouse_line="#D3C39E", blouse_fold="#E0D2B2", paso="#2F5F6E", paso_check="#46808F",
          paso_panel="#234850", sash="#C2452C", sash_end="#933220", tie="#C2452C")),
]

W, H = 1920, 1500
CW, CH = 480, 680
TOP = 140
cells, previews = [], []
for k, (name, dyes, way) in enumerate(WAYS):
    cx = (k % 4) * CW + CW // 2
    y0 = TOP + (k // 4) * CH
    cells.append('<text x="%d" y="%d" text-anchor="middle" class="h">%s</text>' % (cx, y0 + 30, name))
    cells.append('<text x="%d" y="%d" text-anchor="middle" class="s">%s</text>' % (cx, y0 + 56, dyes))
    cells.append('<g transform="translate(%d %d) scale(0.62)">%s</g>' % (cx, y0 + 76, option_b(way, "p%d" % k)))
    cells.append('<rect x="%d" y="%d" width="300" height="170" rx="6" fill="#141A33"/>' % (cx - 150, y0 + 470))
    cells.append('<rect x="%d" y="%d" width="300" height="24" fill="#1A1416"/>' % (cx - 150, y0 + 616))
    previews.append((way, k, cx, y0 + 470 + 8))

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
 .t {{ font: 600 44px Baskerville, Georgia, serif; fill: #2A2420 }}
 .st {{ font: 23px Baskerville, Georgia, serif; fill: #6F655A }}
 .h {{ font: 600 26px Baskerville, Georgia, serif; fill: #2A2420 }}
 .s {{ font: italic 19px Baskerville, Georgia, serif; fill: #6F655A }}
</style>
<rect width="{W}" height="{H}" fill="#E8E2D5"/>
<text x="60" y="62" class="t">Option B, the Bagan traveller: colourways</text>
<text x="60" y="96" class="st">Plant and insect dyes long used in the region: indigo, turmeric, cutch, lac, and undyed cotton. Each is also shown at in-game size on the night colours.</text>
{cells}
</svg>""".format(W=W, H=H, cells="\n".join(cells))

base = os.path.splitext(OUT)[0]
with open(base + ".svg", "w", encoding="utf-8") as f:
    f.write(svg)
with open(base + ".html", "w", encoding="utf-8") as f:
    f.write("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0}</style></head><body>%s</body></html>" % svg)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=%d,%d" % (W, H),
                "--user-data-dir=/tmp/claude-chrome-sketch", "--screenshot=" + OUT, "file://" + base + ".html"],
               check=True, capture_output=True)
os.remove(base + ".html")

sheet = Image.open(OUT).convert("RGB")
for way, k, cx, top in previews:
    one = base + "_fig%d" % k
    fig = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="640"><g transform="translate(160 20)">%s</g></svg>' % option_b(way, "q%d" % k)
    with open(one + ".html", "w", encoding="utf-8") as f:
        f.write("<!doctype html><html><body style='margin:0;background:transparent'>%s</body></html>" % fig)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=320,640",
                    "--default-background-color=00000000", "--user-data-dir=/tmp/claude-chrome-sketch",
                    "--screenshot=" + one + ".png", "file://" + one + ".html"], check=True, capture_output=True)
    im = Image.open(one + ".png").convert("RGBA")
    im = im.crop(im.getchannel("A").getbbox())
    h = 48
    w = max(1, round(im.width * h / im.height))
    small = im.convert("RGBa").resize((w, h), Image.BOX).convert("RGBA")
    alpha = small.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    flat = small.convert("RGB").quantize(colors=14, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    px = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px.paste(flat, mask=alpha)
    big = px.resize((w * 3, h * 3), Image.NEAREST)
    sheet.paste(big, (cx - big.width // 2, top), big)
    for ext in (".html", ".png"):
        os.remove(one + ext)
sheet.save(OUT)
print("wrote", OUT)
