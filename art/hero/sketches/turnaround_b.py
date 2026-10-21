"""Turnaround of the hero in costume B, original colours: front, three-quarter, side and back, on shared height guides,
with each view also shrunk to the in-game size (48 px) on the night colours.

    python3 turnaround_b.py <out.png>
"""
import os
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_figures import option_b, option_b_back, option_b_side, option_b_three_quarter  # noqa: E402

OUT = sys.argv[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
VIEWS = [("Front", option_b), ("Three-quarter", option_b_three_quarter), ("Side", option_b_side), ("Back", option_b_back)]
GUIDES = [(4, "top of the topknot"), (64, "eyes"), (102, "chin"), (132, "shoulders"), (274, "sash"), (500, "hem"),
          (597, "ground")]
W, H = 1920, 1290
S = 1.2           # figure scale on the sheet
TOP = 170         # sheet y of figure y = 0
cols = [330, 760, 1190, 1620]

parts = []
for y, name in GUIDES:
    sy = TOP + y * S
    parts.append('<line x1="150" y1="%g" x2="1830" y2="%g" stroke="#C9BFAE" stroke-width="1.5" stroke-dasharray="6 6"/>' % (sy, sy))
    parts.append('<text x="140" y="%g" text-anchor="end" class="g">%s</text>' % (sy + 5, name))
for (name, fn), cx in zip(VIEWS, cols):
    parts.append('<text x="%d" y="140" text-anchor="middle" class="h">%s</text>' % (cx, name))
    parts.append('<g transform="translate(%d %d) scale(%g)">%s</g>' % (cx, TOP, S, fn(pid="p" + name[:2])))
    parts.append('<rect x="%d" y="1000" width="220" height="200" rx="6" fill="#141A33"/>' % (cx - 110))
    parts.append('<rect x="%d" y="1172" width="220" height="28" fill="#1A1416"/>' % (cx - 110))

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
 .t {{ font: 600 44px Baskerville, Georgia, serif; fill: #2A2420 }}
 .st {{ font: 23px Baskerville, Georgia, serif; fill: #6F655A }}
 .h {{ font: 600 30px Baskerville, Georgia, serif; fill: #2A2420 }}
 .g {{ font: italic 17px Baskerville, Georgia, serif; fill: #8A7F70 }}
 .s {{ font: italic 20px Baskerville, Georgia, serif; fill: #6F655A }}
</style>
<rect width="{W}" height="{H}" fill="#E8E2D5"/>
<text x="60" y="62" class="t">Maung Pauk Kyaing: turnaround</text>
<text x="60" y="96" class="st">Costume B, the Bagan traveller, original colours. Red sash and hair tie, gold ear plugs, satchel on his right hip.</text>
{parts}
<text x="150" y="1240" class="s">In game: 48 px tall, shown at 3x. The side view is what the player sees most in a side-scroller.</text>
</svg>""".format(W=W, H=H, parts="\n".join(parts))

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
for (name, fn), cx in zip(VIEWS, cols):
    one = base + "_" + name[:2]
    fig = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="640"><g transform="translate(160 20)">%s</g></svg>' % fn(pid="q" + name[:2])
    with open(one + ".html", "w", encoding="utf-8") as f:
        f.write("<!doctype html><html><body style='margin:0;background:transparent'>%s</body></html>" % fig)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=320,640",
                    "--default-background-color=00000000", "--user-data-dir=/tmp/claude-chrome-sketch",
                    "--screenshot=" + one + ".png", "file://" + one + ".html"], check=True, capture_output=True)
    im = Image.open(one + ".png").convert("RGBA")
    # keep the ground at the bottom: crop to the figure's own height box (topknot to ground) so views line up
    bb = im.getchannel("A").getbbox()
    im = im.crop((bb[0], 20, bb[2], 20 + 598))
    h = 48
    w = max(1, round(im.width * h / im.height))
    small = im.convert("RGBa").resize((w, h), Image.BOX).convert("RGBA")
    alpha = small.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    flat = small.convert("RGB").quantize(colors=14, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    px = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px.paste(flat, mask=alpha)
    big = px.resize((w * 3, h * 3), Image.NEAREST)
    sheet.paste(big, (cx - big.width // 2, 1172 - big.height), big)
    for ext in (".html", ".png"):
        os.remove(one + ext)
sheet.save(OUT)
print("wrote", OUT)
