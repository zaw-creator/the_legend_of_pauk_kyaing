"""Put the Blender naga renders into MainMenu.dc.html in place of the vector naga.

    python3 menu_integrate.py <render dir> <MainMenu.dc.html in> <MainMenu.dc.html out> <assets dir> <front url> <back url>

Crops menu_front.png / menu_back.png to their opaque area, writes them as WebP into <assets dir>, and rewrites the
menu: the back pass sits under the palace, the front pass where the vector naga was, both drifting together.
"""
import json
import os
import re
import sys

from PIL import Image

rdir, src, dst, adir, front_url, back_url = sys.argv[1:7]
os.makedirs(adir, exist_ok=True)


def crop(name, out):
    im = Image.open(os.path.join(rdir, name)).convert("RGBA")
    a = im.getchannel("A").point(lambda v: 255 if v > 2 else 0)
    l, t, r, b = a.getbbox()
    pad = 6
    l, t, r, b = max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)
    im.crop((l, t, r, b)).save(os.path.join(adir, out), "WEBP", quality=90, method=6)
    return dict(x=l, y=t, w=r - l, h=b - t)


front = crop("menu_front.png", "naga_menu_front.webp")
back = crop("menu_back.png", "naga_menu_back.webp")
marks = json.load(open(os.path.join(rdir, "menu_marks.json")))
eye = min((marks["Gem-1"], marks["Gem1"]), key=lambda m: m.get("depth", 0.0))  # the eye nearer the camera
print("front", front, "back", back)

html = open(src, encoding="utf-8").read()


def sub1(old, new):
    global html
    assert html.count(old) == 1, (html.count(old), old[:70])
    html = html.replace(old, new)


# styles: the vector naga's coil and blink give way to a slow drift shared by both passes and a glint on the gems
sub1(".naga-body { animation: mm-coil 13s ease-in-out infinite alternate; }\n"
     ".naga-eye { animation: mm-blink 9s ease-in-out infinite; }\n",
     ".naga-live { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; animation: mm-naga 7s ease-in-out infinite alternate; }\n"
     ".naga-img { position: absolute; display: block; filter: drop-shadow(0 0 10px rgba(205, 182, 122, 0.16)); }\n"
     ".naga-glint { position: absolute; border-radius: 50%; background: radial-gradient(circle, rgba(236, 104, 62, 0.9), rgba(236, 104, 62, 0) 68%); mix-blend-mode: screen; animation: mm-glint 4.6s ease-in-out infinite; }\n")
sub1("@keyframes mm-coil { from { transform: translate3d(0, 8px, 0) rotate(-0.8deg); } to { transform: translate3d(0, -12px, 0) rotate(0.8deg); } }\n"
     "@keyframes mm-blink { 0%, 90%, 100% { opacity: 1; } 94% { opacity: 0.1; } }\n",
     "@keyframes mm-naga { from { transform: translate3d(0, 3px, 0); } to { transform: translate3d(0, -6px, 0); } }\n"
     "@keyframes mm-glint { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.95; } }\n")

img = ('<img class="naga-img" src="{url}" alt="" style="left: {x}px; top: {y}px; width: {w}px; height: {h}px">')
back_layer = (
    '      <div class="layer" style="transform: {{ L.naga }}; filter: blur({{ B.far }}px)">\n'
    '        <div class="naga-live">\n'
    '          ' + img.format(url=back_url, **back) + '\n'
    '        </div>\n'
    '      </div>\n\n')


def glint(m, size, delay):
    return ('          <div class="naga-glint" style="left: {x}px; top: {y}px; width: {s}px; height: {s}px; '
            'animation-delay: {d}s"></div>\n').format(x=round(m["x"] - size / 2), y=round(m["y"] - size / 2), s=size, d=delay)


front_layer = (
    '      <div class="layer" style="transform: {{ L.naga }}; filter: blur({{ B.far }}px)">\n'
    '        <div class="naga-live">\n'
    '          ' + img.format(url=front_url, **front) + '\n'
    + glint(eye, 34, 0) + glint(marks["ForeheadGem"], 22, -2.3) +
    '        </div>\n'
    '      </div>\n\n')

palace_open = '      <div class="layer" style="transform: {{ L.palace }}; filter: blur({{ B.far }}px)">\n'
sub1(palace_open, back_layer + palace_open)

start = html.index('      <div class="layer" style="transform: {{ L.naga }}; filter: blur({{ B.far }}px)">\n        <div class="fill" style="filter: drop-shadow')
end = html.index('      <div class="layer" style="transform: {{ L.wall }}')
html = html[:start] + front_layer + html[end:]
assert "nflame" not in html and "naga-body" not in html
open(dst, "w", encoding="utf-8").write(html)
print("wrote", dst, len(html), "bytes")
