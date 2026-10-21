"""Write the pixel-art main-menu artboard (MainMenuPixel.dc.html) from the painted menu's source.

    python3 pixel_menu_board.py <MainMenu.source.dc.html> <out .dc.html> far=<url> palace=<url> wall=<url> hero=<url>
        tree_r=<url> tree_l=<url> naga_front=<url> naga_back=<url>

The scene's vector layers become the baked pixel layers from pixel_menu_layers.py (urls: local files for a preview,
/_blob/... once uploaded). Live parts stay live: lanterns, light shafts, mist, embers, bats, camera moves and all
text, which stays smooth. Motion that would smear pixels (depth blur, idle zoom, sub-pixel drift) is removed or
moved in whole 4 px steps.
"""
import os
import re
import subprocess
import sys

SRC, DST = sys.argv[1:3]
URL = dict(a.split("=", 1) for a in sys.argv[3:])
HERE = os.path.dirname(os.path.abspath(__file__))
MENU = os.path.join(os.path.dirname(HERE), "menu")
LAYER_END = "\n      </div>\n"

# the vector naga gives way to the naga layers first (the same step the painted menu uses), then everything else
tmp = DST + ".tmp"
subprocess.run([sys.executable, "-I", os.path.join(MENU, "menu_integrate.py"), os.path.join(HERE, "menu"), SRC, tmp,
                os.path.join(os.path.dirname(DST), ".unused_assets"), "FRONTURL", "BACKURL"], check=True,
               capture_output=True)
s = open(tmp, encoding="utf-8").read()
os.remove(tmp)


def sub1(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


def block(start, new, end=LAYER_END, after=0):
    """Replace from `start` (searched from `after`) through the next `end` with `new`."""
    global s
    i = s.index(start, after)
    j = s.index(end, i) + len(end)
    s = s[:i] + new + s[j:]
    return i


def px(key, indent=8):
    return " " * indent + '<img class="px" src="%s" alt="">\n' % URL[key]


sub1("<title>Main menu, live and immersive</title>", "<title>Main menu, pixel art</title>")

# styles: pixel layers, square particles and lamps, whole-pixel motion
sub1(".star { position: absolute; border-radius: 50%; background: #E7DCC6; animation: mm-twinkle ease-in-out infinite; }\n",
     ".px { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; image-rendering: pixelated; pointer-events: none; }\n")
s = s.replace(".lantern { position: absolute; width: 8px; height: 8px; margin: -4px 0 0 -4px; border-radius: 50%;",
              ".lantern { position: absolute; width: 8px; height: 8px; margin: -4px 0 0 -4px; border-radius: 0;")
s = s.replace(".ember { position: absolute; width: 4px; height: 4px; border-radius: 50%;",
              ".ember { position: absolute; width: 4px; height: 4px; border-radius: 0;")
s = s.replace(".mote { position: absolute; border-radius: 50%;", ".mote { position: absolute; border-radius: 0;")
s = re.sub(r"\.hero \{[^\n]*\}\n", ".hero-px { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; "
           "animation: mm-breathe-px 4.5s steps(2, jump-none) infinite alternate; }\n", s, count=1)
s = re.sub(r"\.scarf \{[^\n]*\}\n", "", s, count=1)
sub1("@keyframes mm-breathe { from { transform: translate3d(0, 0, 0); } to { transform: translate3d(0, -3px, 0); } }\n",
     "@keyframes mm-breathe-px { from { transform: translate3d(0, 0, 0); } to { transform: translate3d(0, -4px, 0); } }\n")
sub1("animation: mm-naga 7s ease-in-out infinite alternate; }", "animation: mm-naga 7s steps(3, jump-none) infinite alternate; }")
sub1("@keyframes mm-naga { from { transform: translate3d(0, 3px, 0); } to { transform: translate3d(0, -6px, 0); } }",
     "@keyframes mm-naga { from { transform: translate3d(0, 4px, 0); } to { transform: translate3d(0, -4px, 0); } }")
s = re.sub(r"\.naga-img \{[^\n]*\}\n", "", s, count=1)
s = re.sub(r"\.naga-glint \{[^\n]*\}\n", "", s, count=1)

# sky, stars, moon and hills: one baked far layer; the moon's light streak stays live
block('      <div class="layer" style="transform: {{ L.sky }}; filter: blur({{ B.sky }}px)">',
      '      <div class="layer" style="transform: {{ L.moon }}">\n' + px("far") + "      </div>\n")
block('      <div class="layer" style="transform: {{ L.moon }}; filter: blur({{ B.far }}px)">',
      '      <div class="layer" style="transform: {{ L.moon }}">\n'
      '        <div class="streak" style="left: 880px; top: 249px; width: 1200px"></div>\n      </div>\n')
block('      <div class="layer" style="transform: {{ L.hills }}; filter: blur({{ B.far }}px)">', "")
s = s.replace("\n\n\n", "\n\n")

# naga layers: full-frame pixel images, no blur, no soft glints
s = s.replace('<div class="layer" style="transform: {{ L.naga }}; filter: blur({{ B.far }}px)">',
              '<div class="layer" style="transform: {{ L.naga }}">')
s = re.sub(r'<img class="naga-img" src="FRONTURL"[^>]*>', '<img class="px" src="%s" alt="">' % URL["naga_front"], s)
s = re.sub(r'<img class="naga-img" src="BACKURL"[^>]*>', '<img class="px" src="%s" alt="">' % URL["naga_back"], s)
s = re.sub(r'\n\s*<div class="naga-glint"[^>]*></div>', "", s)

# palace, wall (with the notebook), hero and trees
SVG_FULL = '        <svg viewBox="0 0 1920 1080" width="1920" height="1080" style="position: absolute; left: 0; top: 0" aria-hidden="true">'
sub1('      <div class="layer" style="transform: {{ L.palace }}; filter: blur({{ B.far }}px)">',
     '      <div class="layer" style="transform: {{ L.palace }}">')
i = s.index('<div class="layer" style="transform: {{ L.palace }}">')
block(SVG_FULL, px("palace"), end="        </svg>\n", after=i)
sub1('      <div class="layer" style="transform: {{ L.wall }}; filter: blur({{ B.mid }}px)">',
     '      <div class="layer" style="transform: {{ L.wall }}">')
i = s.index('<div class="layer" style="transform: {{ L.wall }}">')
block(SVG_FULL, px("wall"), end="        </svg>\n", after=i)
block('        <svg viewBox="0 0 84 30" width="84" height="30"', "", end="        </svg>\n", after=i)
sub1('      <div class="layer" style="transform: {{ L.hero }}; filter: blur({{ B.mid }}px)">',
     '      <div class="layer" style="transform: {{ L.hero }}">')
block('        <svg class="hero" viewBox="0 0 120 240" aria-hidden="true">',
      '        <div class="hero-px"><img class="px" src="%s" alt=""></div>\n' % URL["hero"], end="        </svg>\n")
sub1('      <div class="layer" style="transform: {{ L.trees }}; filter: blur({{ B.trees }}px)">',
     '      <div class="layer" style="transform: {{ L.trees }}">')
for key, cls in (("tree_r", "sway-r"), ("tree_l", "sway-l")):
    i = s.index('<div class="sway %s">' % cls)
    block('          <svg viewBox="0 0 1920 1080" aria-hidden="true">', px(key, 10), end="          </svg>\n", after=i)

# script: no film grain by default, no idle zoom (keeps pixels square), no star list
sub1('"grain":{"editor":"range","min":0,"max":0.3,"step":0.01,"default":0.12,',
     '"grain":{"editor":"range","min":0,"max":0.3,"step":0.01,"default":0,')
sub1("grain: this.props.grain ?? 0.12,", "grain: this.props.grain ?? 0,")
sub1("const idle = { ox: 960, oy: 560, s: 1.04,", "const idle = { ox: 960, oy: 560, s: 1,")
# the Credits camera frames the naga's head, which rests on the top roof looking left
sub1("{ ox: 1250, oy: 340, s: 1.3,", "{ ox: 1150, oy: 290, s: 1.3,")
s = re.sub(r"\n      stars: range\(46\)\.map\(\(i\) => \(\{.*?\}\)\),", "", s, count=1, flags=re.S)

for gone in ("<svg class=\"hero\"", "L.hills", "L.sky", "naga-glint", "FRONTURL", "BACKURL", "stars:"):
    assert gone not in s, gone
open(DST, "w", encoding="utf-8").write(s)
print("wrote", DST, len(s), "bytes")
