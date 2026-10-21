"""Turn MainMenu.dc.html into a static HTML page (idle state) so headless Chrome can screenshot it.

    python3 preview_menu.py <MainMenu.dc.html> <out.html> [url=localpath ...]
Each url=localpath pair swaps an asset url for a local file for the preview.
"""
import json
import math
import re
import sys

src_path, out_path = sys.argv[1], sys.argv[2]
swaps = [a.split("=", 1) for a in sys.argv[3:]]
html = open(src_path, encoding="utf-8").read()
for a, b in swaps:
    html = html.replace(a, b)


def rnd(n):
    x = math.sin(n * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def points(name):
    """A [[x, y], ...] list declared in the component script, so the preview follows edits to it."""
    return json.loads(re.search(r"const %s = (\[.*?\]\]);" % name, html).group(1))


def r(x):
    return int(math.floor(x + 0.5))


lists = {
    "stars": [dict(x=r(rnd(i + 1) * 1920), y=r(rnd(i + 101) * 520), s=1 + r(rnd(i + 201) * 2),
                   t="%.2f" % (3 + rnd(i + 301) * 4), d="%.2f" % (-rnd(i + 401) * 6)) for i in range(46)],
    "bats": [dict(y=150 + r(rnd(i + 1300) * 170), t="%.1f" % (34 + rnd(i + 1400) * 18),
                  d="%.1f" % (-rnd(i + 1500) * 40)) for i in range(3)],
    "palaceLanterns": [dict(x=x, y=y, t="%.2f" % (2.6 + rnd(i + 500) * 1.8), d="%.2f" % (-rnd(i + 600) * 4))
                       for i, (x, y) in enumerate(points("palacePts"))],
    "wallLanterns": [dict(x=x, y=y, t="%.2f" % (2.6 + rnd(i + 520) * 1.8), d="%.2f" % (-rnd(i + 620) * 4))
                     for i, (x, y) in enumerate(points("wallPts"))],
    "embers": [dict(x=r(560 + rnd(i + 700) * 900), y=r(760 + rnd(i + 800) * 180), dx=r((rnd(i + 900) - 0.5) * 90),
                    t="%.2f" % (7 + rnd(i + 1000) * 6), d="%.2f" % (-rnd(i + 1100) * 12)) for i in range(20)],
    "motes": [dict(x=r(300 + rnd(i + 2000) * 1400), y=r(160 + rnd(i + 2100) * 740), s="%.1f" % (1 + rnd(i + 2200) * 1.8),
                   dx=r((rnd(i + 2300) - 0.5) * 120), dy=r((rnd(i + 2400) - 0.5) * 90),
                   o="%.2f" % (0.2 + rnd(i + 2500) * 0.35), t="%.1f" % (16 + rnd(i + 2600) * 18),
                   d="%.1f" % (-rnd(i + 2700) * 30)) for i in range(60)],
    "items": [dict(label=lab, cap=cap, x=60 + r(math.sin(i * 0.9) * 34), y=48 + i * 84, color="rgba(231, 220, 198, 0.8)",
                   rule=0, capOp=0, capY=-6)
              for i, (lab, cap) in enumerate(zip(["New Game", "Continue", "Options", "Credits", "Quit"],
                                                 ["Leave the academy and take the road", "Return to your notebook",
                                                  "Light, sound and controls", "The people behind the legend",
                                                  "Leave the city for now"]))],
}
scalars = {"cam.ox": 960, "cam.oy": 560, "cam.s": "1.040", "cam.tx": 0, "cam.ty": 0, "B.sky": "0.2", "B.far": 0.6,
           "B.mid": 0, "B.trees": 2.2, "lampOp": "1.00", "nbOp": 0.3, "dimOp": 0, "leaveOp": 0, "grain": 0.12,
           "dusk": 0.6}


def expand_for(m):
    lst, var, body = m.group(1), m.group(2), m.group(3)
    out = []
    for item in lists[lst]:
        out.append(re.sub(r"\{\{\s*%s\.(\w+)\s*\}\}" % var, lambda k: str(item.get(k.group(1), "")), body))
    return "".join(out)


html = re.sub(r'<sc-for list="\{\{\s*(\w+)\s*\}\}" as="(\w+)"[^>]*>(.*?)</sc-for>', expand_for, html, flags=re.S)
html = re.sub(r'\s(on[A-Z]\w*)="\{\{[^}]*\}\}"', "", html)
html = re.sub(r"\{\{\s*L\.\w+\s*\}\}", "translate3d(0px, 0px, 0)", html)
for k, v in scalars.items():
    html = re.sub(r"\{\{\s*%s\s*\}\}" % re.escape(k), str(v), html)
left = re.findall(r"\{\{[^}]*\}\}", html)
if left:
    print("unfilled holes:", sorted(set(left)))
helmet = re.search(r"<helmet>(.*?)</helmet>", html, flags=re.S).group(1)
html = re.sub(r"<helmet>.*?</helmet>", "", html, flags=re.S)
html = html.replace('<script src="./support.js"></script>', helmet)
html = re.sub(r'<script type="text/x-dc".*?</script>', "", html, flags=re.S)
html = html.replace("<x-dc>", "").replace("</x-dc>", "")
open(out_path, "w", encoding="utf-8").write(html)
print("wrote", out_path)
