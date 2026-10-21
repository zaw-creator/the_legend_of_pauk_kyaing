"""Costume sketches for the hero, Maung Pauk Kyaing: three options from the research, side by side.

    python3 costume_sheet.py <out.png>

Writes an SVG sheet (front views, flat colour) and renders it with headless Chrome.
The figures are drawn in hero_figures.py.
"""
import os
import subprocess
import sys

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

from hero_figures import option_a, option_b, option_c  # noqa: E402


OPTIONS = [
    ("A", "Pyu-era scholar", "faithful to the oldest sources", option_a, [
        "Hair in a topknot, tied with white cotton",
        "Bare chest; cotton shawl over one shoulder (old Indian antariya and uttariya)",
        "Knee-length wrapped cloth, red sash knotted at the waist",
        "Ear plugs, bead necklace, bracelets; palm-leaf books"]),
    ("B", "Bagan traveller", "from the temple murals, 11th to 13th century", option_b, [
        "Small topknot with a red tie; large round ear plugs",
        "Short-sleeved upper blouse",
        "Dhoti-like paso, hitched for walking, in an indigo check",
        "Wide red sash with a long trailing end"]),
    ("C", "Folk-tale classic", "the look most Burmese readers picture (Ava to Konbaung)", option_c, [
        "Gaung baung head wrap with its knot and trailing end",
        "White jacket fastened at the side (eingyi)",
        "Paso to the ankles, wrapped and knotted at the front",
        "Red scarf as his mark; cloth bag; black folding book (parabaik)"]),
]

W, H = 1920, 1400
cols = [320, 960, 1600]
figs, labels = [], []
for (key, name, basis, fn, notes), cx in zip(OPTIONS, cols):
    figs.append('<g transform="translate(%d 190) scale(1.18)">%s</g>' % (cx, fn()))
    figs.append('<ellipse cx="%d" cy="900" rx="80" ry="9" fill="#000" opacity="0.12"/>' % cx)
    labels.append('<text x="%d" y="150" text-anchor="middle" class="h">%s. %s</text>' % (cx, key, name))
    labels.append('<text x="%d" y="178" text-anchor="middle" class="s">%s</text>' % (cx, basis))
    for k, line in enumerate(notes):
        labels.append('<text x="%d" y="%d" class="n">• %s</text>' % (cx - 270, 950 + 30 * k, line))

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
 .t {{ font: 600 46px Baskerville, Georgia, serif; fill: #2A2420 }}
 .st {{ font: 24px Baskerville, Georgia, serif; fill: #6F655A }}
 .h {{ font: 600 32px Baskerville, Georgia, serif; fill: #2A2420 }}
 .s {{ font: italic 21px Baskerville, Georgia, serif; fill: #6F655A }}
 .n {{ font: 19px Baskerville, Georgia, serif; fill: #3B342D }}
</style>
<rect width="{W}" height="{H}" fill="#E8E2D5"/>
<text x="60" y="66" class="t">Maung Pauk Kyaing: costume sketches</text>
<text x="60" y="100" class="st">A young commoner and scholar, back from his teachers and on the road to Tagaung. Red cloth is his mark in every option.</text>
<line x1="640" y1="130" x2="640" y2="1360" stroke="#CFC6B4" stroke-width="2"/>
<line x1="1280" y1="130" x2="1280" y2="1360" stroke="#CFC6B4" stroke-width="2"/>
<text x="60" y="1110" class="s">In game: 48 px tall, shown at 4x (quick automatic shrink):</text>
{figs}
{labels}
</svg>""".format(W=W, H=H, figs="\n".join(figs), labels="\n".join(labels))

html_path = os.path.splitext(OUT)[0] + ".html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;background:#E8E2D5}</style></head><body>%s</body></html>" % svg)
with open(os.path.splitext(OUT)[0] + ".svg", "w", encoding="utf-8") as f:
    f.write(svg)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=%d,%d" % (W, H),
                "--user-data-dir=/tmp/claude-chrome-sketch", "--screenshot=" + OUT, "file://" + html_path],
               check=True, capture_output=True)

from PIL import Image  # noqa: E402

sheet = Image.open(OUT).convert("RGB")
for (key, _, _, fn, _), cx in zip(OPTIONS, cols):
    one = os.path.splitext(OUT)[0] + "_fig%s" % key
    fig = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="640"><g transform="translate(160 20)">%s</g></svg>' % fn()
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
    big = px.resize((w * 4, h * 4), Image.NEAREST)
    sheet.paste(big, (cx - big.width // 2, 1140), big)
    for ext in (".html", ".png"):
        os.remove(one + ext)
sheet.save(OUT)
print("wrote", OUT)
