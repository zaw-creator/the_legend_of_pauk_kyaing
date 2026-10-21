"""Hero figure drawings (front view, flat colour SVG) shared by the costume sheets.

Coordinates of a figure: x = 0 is the centre line, y runs from 0 (top of the topknot) to 600 (the ground).
option_b(colours) takes a colourway dict; the keys and defaults are in B_DEFAULT.
"""

SKIN, SKIN_D = "#B98A62", "#9A6E4C"
HAIR = "#1A1514"
RED, RED_D = "#A94530", "#7E2F21"
GOLD = "#C9A04A"
LEATHER, LEATHER_D = "#6B4329", "#4A2E1C"
INK = "#2A2420"


def mirror(d):
    """Mirror an SVG path made of absolute M/C/L/Z commands about x = 0."""
    out = []
    for tok in d.replace(",", " ").split():
        out.append(tok)
    res, i = [], 0
    while i < len(out):
        t = out[i]
        if t in "MCLZ":
            res.append(t)
            i += 1
            continue
        x, y = float(out[i]), out[i + 1]
        res.append("%g,%s" % (-x, y))
        i += 2
    return " ".join(res)


def both(d, **attrs):
    a = " ".join('%s="%s"' % (k.replace("_", "-"), v) for k, v in attrs.items())
    return '<path d="%s" %s/><path d="%s" %s/>' % (d, a, mirror(d), a)


def path(d, **attrs):
    a = " ".join('%s="%s"' % (k.replace("_", "-"), v) for k, v in attrs.items())
    return '<path d="%s" %s/>' % (d, a)


# ---- the body, shared by every option -------------------------------------------------------------------------
HEAD = "M -28,60 C -30,30 -18,22 0,22 C 18,22 30,30 28,60 C 27,82 15,100 0,102 C -15,100 -27,82 -28,60 Z"
ARM = "M 50,132 C 62,140 66,190 66,250 C 67,290 68,320 66,346 L 55,346 C 55,320 53,290 51,252 C 49,210 45,175 43,150 Z"
LEG = "M 2,298 L 44,298 C 46,360 40,410 36,450 C 32,500 30,540 30,578 L 12,578 C 12,540 10,500 10,450 C 8,400 4,350 2,298 Z"
FOOT = "M 8,576 L 32,576 C 40,580 43,590 41,597 L 7,597 Z"
TORSO = ("M -12,118 C -30,122 -50,124 -54,138 C -58,170 -50,200 -44,226 C -40,250 -40,270 -44,300 L 44,300 "
         "C 40,270 40,250 44,226 C 50,200 58,170 54,138 C 50,124 30,122 12,118 Z")


def body():
    s = [path("M -11,96 L 11,96 L 13,124 L -13,124 Z", fill=SKIN_D),
         both(LEG, fill=SKIN), both(FOOT, fill=SKIN_D), path(TORSO, fill=SKIN),
         both(ARM, fill=SKIN),
         '<ellipse cx="61" cy="360" rx="9" ry="15" fill="%s"/><ellipse cx="-61" cy="360" rx="9" ry="15" fill="%s"/>' % (SKIN, SKIN),
         '<ellipse cx="29" cy="65" rx="5" ry="9" fill="%s"/><ellipse cx="-29" cy="65" rx="5" ry="9" fill="%s"/>' % (SKIN_D, SKIN_D),
         path(HEAD, fill=SKIN)]
    return "".join(s)


def face():
    return "".join([
        both("M 6,58 C 10,55 16,55 20,58", fill="none", stroke=INK, stroke_width=2.4, stroke_linecap="round"),
        '<ellipse cx="13" cy="64" rx="3.2" ry="2.4" fill="%s"/><ellipse cx="-13" cy="64" rx="3.2" ry="2.4" fill="%s"/>' % (INK, INK),
        path("M 0,66 L -2,78 L 3,79", fill="none", stroke=SKIN_D, stroke_width=2, stroke_linecap="round"),
        path("M -7,88 C -2,90 3,90 8,87", fill="none", stroke="#6E3E2C", stroke_width=2.2, stroke_linecap="round"),
    ])


def sandals():
    return both("M 8,586 L 40,586 M 14,578 L 22,590 M 30,578 L 22,590", fill="none", stroke=LEATHER_D, stroke_width=3,
                stroke_linecap="round") + both("M 6,596 L 42,596", stroke=LEATHER_D, stroke_width=4)


def satchel(side=-1, y=258, color=LEATHER, flap=LEATHER_D, strap_from=(40, 128)):
    x0 = side * 58 - 18
    sx, sy = strap_from
    return "".join([
        path("M %g,%g L %g,%g" % (-side * sx, sy, x0 + 18, y), stroke=color, stroke_width=5, fill="none",
             stroke_linecap="round"),
        '<rect x="%g" y="%g" width="38" height="44" rx="5" fill="%s"/>' % (x0, y, color),
        '<rect x="%g" y="%g" width="38" height="13" rx="4" fill="%s"/>' % (x0, y, flap),
        '<rect x="%g" y="%g" width="5" height="9" fill="%s"/>' % (x0 + 16.5, y + 10, GOLD),
    ])


# ---- option A: Pyu-era scholar ------------------------------------------------------------------------------
def option_a():
    hair = "".join([
        path("M -29,58 C -32,28 -16,18 0,18 C 16,18 32,28 29,58 C 26,44 16,34 0,34 C -16,34 -26,44 -29,58 Z", fill=HAIR),
        '<circle cx="0" cy="11" r="13" fill="%s"/>' % HAIR,
        '<rect x="-15" y="17" width="30" height="7" rx="3.5" fill="#EDE6D6"/>',
    ])
    beads = "".join('<circle cx="%g" cy="%g" r="2.6" fill="%s"/>' % (
        x, 128 + 22 * (1 - (x / 26) ** 2), GOLD if k % 2 else RED) for k, x in enumerate(range(-24, 26, 6)))
    skirt = "".join([
        path("M -48,262 C -50,330 -56,400 -58,452 L 58,452 C 56,400 50,330 48,262 Z", fill="#D9C9A3"),
        path("M 6,270 C 10,330 14,400 16,450", fill="none", stroke="#B9A67E", stroke_width=2.5),
        path("M -22,272 C -24,340 -28,400 -30,450", fill="none", stroke="#B9A67E", stroke_width=2.5),
        path("M -58,452 L 58,452", stroke="#B9A67E", stroke_width=3),
    ])
    sash = "".join([
        path("M -48,256 L 48,256 L 48,276 L -48,276 Z", fill=RED),
        path("M -20,272 C -24,300 -26,330 -30,362 L -17,364 C -15,332 -13,300 -11,274 Z", fill=RED_D),
        path("M -8,274 C -6,300 -4,325 -5,352 L 6,350 C 5,322 3,298 1,274 Z", fill=RED),
        '<circle cx="-12" cy="266" r="9" fill="%s"/>' % RED_D,
    ])
    shawl = "".join([
        path("M -60,140 C -70,190 -72,240 -70,300 L -57,302 C -57,250 -55,200 -49,150 Z", fill="#E2D9C6"),
        path("M -58,126 C -40,116 -24,122 -14,132 C 4,170 26,220 46,262 L 30,272 C 12,232 -10,190 -34,160 "
             "C -44,150 -52,148 -60,152 Z", fill="#EDE6D6"),
        path("M -20,140 C -4,176 14,214 34,258", fill="none", stroke="#CFC5AE", stroke_width=2.5),
    ])
    leaves = ('<g transform="translate(64 352) rotate(-28)"><rect x="-4" y="-5" width="44" height="10" rx="2" fill="#E2CC8E"/>'
              '<rect x="-4" y="-1" width="44" height="2" fill="#B8A06A"/><rect x="16" y="-6" width="3" height="12" fill="%s"/></g>' % RED_D)
    extras = "".join([
        '<circle cx="30" cy="74" r="5" fill="%s"/><circle cx="-30" cy="74" r="5" fill="%s"/>' % (GOLD, GOLD),
        both("M 50,338 L 68,338", stroke=GOLD, stroke_width=4),
    ])
    return body() + hair + face() + beads + skirt + sash + shawl + satchel(side=1, strap_from=(40, 128)) + extras + leaves + sandals()


# ---- option B: Bagan traveller ------------------------------------------------------------------------------
B_DEFAULT = dict(blouse="#E9DFC8", blouse_line="#C9B994", blouse_fold="#D3C6A6", paso="#3D4E78", paso_check="#566A98",
                 paso_panel="#2E3B5E", sash=RED, sash_end=RED_D, tie=RED)


def option_b(c=None, pid="chk"):
    """c: a colourway (keys as in B_DEFAULT); pid: a pattern id unique on the page."""
    c = dict(B_DEFAULT, **(c or {}))
    hair = "".join([
        path("M -29,58 C -32,28 -16,18 0,18 C 16,18 32,28 29,58 C 26,44 16,34 0,34 C -16,34 -26,44 -29,58 Z", fill=HAIR),
        '<circle cx="0" cy="14" r="10" fill="%s"/>' % HAIR,
        path("M -2,8 C -14,0 -20,8 -12,14 Z M 2,8 C 14,0 20,8 12,14 Z", fill=c["tie"]),
        both("M 27,52 L 29,70", stroke=HAIR, stroke_width=4),
    ])
    tunic = "".join([
        path("M -14,118 C -34,122 -54,126 -60,138 L -70,190 L -50,197 L -46,176 C -46,210 -46,240 -48,290 L 48,290 "
             "C 46,240 46,210 46,176 L 50,197 L 70,190 L 60,138 C 54,126 34,122 14,118 C 8,130 -8,130 -14,118 Z",
             fill=c["blouse"]),
        path("M -14,118 C -8,130 8,130 14,118", fill="none", stroke=c["blouse_line"], stroke_width=3),
        both("M 30,180 C 34,220 36,250 34,286", fill="none", stroke=c["blouse_fold"], stroke_width=2.5),
    ])
    lower = "".join([
        '<defs><pattern id="%s" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="%s"/>'
        '<rect width="10" height="2" fill="%s"/><rect width="2" height="10" fill="%s"/></pattern></defs>'
        % (pid, c["paso"], c["paso_check"], c["paso_check"]),
        path("M -50,284 C -54,360 -52,440 -46,500 L -12,500 C -10,440 -6,380 -2,330 Z", fill="url(#%s)" % pid),
        path("M 50,284 C 54,360 52,440 46,500 L 12,500 C 10,440 6,380 2,330 Z", fill="url(#%s)" % pid),
        path("M -14,284 L 14,284 L 9,470 L -9,470 Z", fill=c["paso_panel"]),
        path("M -6,290 L -4,466 M 0,290 L 0,468 M 6,290 L 4,466", fill="none", stroke=c["paso_check"], stroke_width=2),
    ])
    sash = "".join([
        path("M -50,262 L 50,262 L 50,286 L -50,286 Z", fill=c["sash"]),
        path("M 30,278 C 40,320 44,380 46,432 L 60,428 C 56,380 52,320 44,278 Z", fill=c["sash_end"]),
    ])
    extras = '<circle cx="30" cy="76" r="7.5" fill="%s"/><circle cx="-30" cy="76" r="7.5" fill="%s"/>' % (GOLD, GOLD)
    return body() + hair + face() + tunic + lower + sash + satchel(side=-1, y=266, strap_from=(40, 126)) + extras + sandals()


# ---- option C: folk-tale classic (Ava to Konbaung) ------------------------------------------------------------
def option_c():
    wrap = "".join([
        both("M 21,46 L 29,48 L 29,62 L 24,60 Z", fill=HAIR),
        path("M -31,56 C -34,24 -16,12 0,12 C 18,12 34,24 31,56 C 26,46 14,40 0,40 C -14,40 -26,46 -31,56 Z", fill="#F1E3CF"),
        path("M -24,30 C -10,26 10,26 24,30 M -28,42 C -10,36 10,36 28,42", fill="none", stroke="#D9C6A8", stroke_width=2.5),
        path("M -30,40 C -52,28 -60,44 -52,60 C -46,52 -40,50 -32,52 Z", fill="#E6D3B8"),
        path("M -34,50 C -44,70 -46,92 -44,112 L -35,112 C -35,92 -33,72 -27,56 Z", fill="#E6D3B8"),
    ])
    jacket = "".join([
        path("M -14,118 C -34,122 -54,126 -58,140 C -62,200 -58,260 -54,302 L 54,302 C 58,260 62,200 58,140 "
             "C 54,126 34,122 14,118 Z", fill="#F3EEE4"),
        both("M 52,132 C 64,140 70,200 72,250 C 74,290 78,320 82,346 L 56,350 C 56,320 54,290 52,252 C 50,210 46,175 44,150 Z",
             fill="#F3EEE4"),
        path("M -14,118 C -2,160 18,192 42,212 L 40,302", fill="none", stroke="#CFC6B4", stroke_width=3),
        '<circle cx="34" cy="206" r="3" fill="#CFC6B4"/><circle cx="20" cy="190" r="3" fill="#CFC6B4"/>',
    ])
    paso = "".join([
        '<defs><pattern id="pso" width="14" height="14" patternUnits="userSpaceOnUse"><rect width="14" height="14" fill="#6E2A27"/>'
        '<rect width="14" height="3" fill="#8E3F37"/><rect width="3" height="14" fill="#8E3F37"/><rect x="7" width="1.5" height="14" fill="#C8A35A" opacity="0.6"/></pattern></defs>',
        path("M -50,292 C -54,380 -52,480 -46,580 L 46,580 C 52,480 54,380 50,292 Z", fill="url(#pso)"),
        path("M -18,290 C -6,302 6,302 18,290 L 12,334 C 4,346 -4,346 -10,334 Z", fill="#4E1D1B"),
        path("M -7,334 C -9,400 -11,470 -14,566 L 6,566 C 6,470 6,400 7,336 Z", fill="#561F1D"),
        path("M 24,300 C 28,400 30,480 30,576 M -30,300 C -32,400 -34,480 -34,576", fill="none", stroke="#4E1D1B", stroke_width=2.5),
    ])
    scarf = "".join([
        path("M -19,110 C -8,124 8,124 19,110 L 24,122 C 10,136 -10,136 -24,122 Z", fill=RED),
        path("M 8,128 C 11,160 13,190 11,216 L 24,214 C 26,188 23,158 19,125 Z", fill=RED),
        path("M -3,131 C -3,150 -5,168 -7,184 L 4,186 C 6,168 8,150 8,130 Z", fill=RED_D),
    ])
    bag = "".join([
        path("M 40,126 L -60,262", stroke="#8C6A3A", stroke_width=5, fill="none", stroke_linecap="round"),
        '<rect x="-80" y="256" width="38" height="46" rx="4" fill="#B8935A"/>',
        '<rect x="-80" y="266" width="38" height="4" fill="%s"/><rect x="-80" y="280" width="38" height="4" fill="%s"/>' % (RED_D, RED_D),
        '<rect x="-80" y="294" width="38" height="3" fill="#5A4426"/>',
    ])
    book = '<g transform="translate(-74 340) rotate(14)"><rect x="0" y="0" width="22" height="30" rx="1.5" fill="#1C1A1E"/><rect x="0" y="6" width="22" height="1.5" fill="#3A3640"/><rect x="0" y="14" width="22" height="1.5" fill="#3A3640"/><rect x="0" y="22" width="22" height="1.5" fill="#3A3640"/></g>'
    return body() + wrap + face() + paso + jacket + scarf + bag + book + sandals()


# ---- option B turnaround: back, side and three-quarter views (same heights as the front) -------------------------
TOPKNOT = '<circle cx="{x}" cy="{y}" r="10" fill="' + HAIR + '"/>'


def _tie(x, y, colour):
    return path("M {a},{b} C {c},{d} {e},{b2} {f},{g} Z M {h},{b} C {i},{d} {j},{b2} {k},{g} Z".format(
        a=x - 2, b=y - 6, c=x - 14, d=y - 14, e=x - 20, b2=y - 6, f=x - 12, g=y, h=x + 2, i=x + 14, j=x + 20, k=x + 12),
        fill=colour)


def option_b_back(c=None, pid="chkb"):
    c = dict(B_DEFAULT, **(c or {}))
    s = [path("M -11,96 L 11,96 L 13,124 L -13,124 Z", fill=SKIN_D),
         both(LEG, fill=SKIN), both(FOOT, fill=SKIN_D), path(TORSO, fill=SKIN), both(ARM, fill=SKIN),
         '<ellipse cx="61" cy="360" rx="9" ry="15" fill="%s"/><ellipse cx="-61" cy="360" rx="9" ry="15" fill="%s"/>' % (SKIN, SKIN),
         path(HEAD, fill=SKIN),
         '<ellipse cx="29" cy="65" rx="5" ry="9" fill="%s"/><ellipse cx="-29" cy="65" rx="5" ry="9" fill="%s"/>' % (SKIN_D, SKIN_D),
         path("M -28,60 C -30,30 -18,22 0,22 C 18,22 30,30 28,60 C 28,74 24,86 18,94 L -18,94 C -24,86 -28,74 -28,60 Z", fill=HAIR),
         TOPKNOT.format(x=0, y=14), _tie(0, 14, c["tie"])]
    tunic = "".join([
        path("M -14,118 C -34,122 -54,126 -60,138 L -70,190 L -50,197 L -46,176 C -46,210 -46,240 -48,290 L 48,290 "
             "C 46,240 46,210 46,176 L 50,197 L 70,190 L 60,138 C 54,126 34,122 14,118 C 8,123 -8,123 -14,118 Z",
             fill=c["blouse"]),
        path("M -14,118 C -8,123 8,123 14,118", fill="none", stroke=c["blouse_line"], stroke_width=3),
        both("M 26,170 C 30,220 32,250 30,286", fill="none", stroke=c["blouse_fold"], stroke_width=2.5),
    ])
    lower = "".join([
        '<defs><pattern id="%s" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="%s"/>'
        '<rect width="10" height="2" fill="%s"/><rect width="2" height="10" fill="%s"/></pattern></defs>'
        % (pid, c["paso"], c["paso_check"], c["paso_check"]),
        path("M -50,284 C -54,360 -52,440 -46,500 L -12,500 C -10,440 -6,380 -2,330 Z", fill="url(#%s)" % pid),
        path("M 50,284 C 54,360 52,440 46,500 L 12,500 C 10,440 6,380 2,330 Z", fill="url(#%s)" % pid),
        path("M -16,284 L 16,284 L 9,326 L -9,326 Z", fill=c["paso_panel"]),
        path("M -7,326 L 7,326 L 4,480 L -4,480 Z", fill=c["paso_panel"]),
        path("M -10,290 L -6,322 M 0,288 L 0,324 M 10,290 L 6,322", fill="none", stroke=c["paso_check"], stroke_width=2),
    ])
    sash = "".join([
        path("M -50,262 L 50,262 L 50,286 L -50,286 Z", fill=c["sash"]),
        path("M -30,278 C -40,320 -44,380 -46,432 L -60,428 C -56,380 -52,320 -44,278 Z", fill=c["sash_end"]),
    ])
    extras = '<circle cx="30" cy="76" r="7.5" fill="%s"/><circle cx="-30" cy="76" r="7.5" fill="%s"/>' % (GOLD, GOLD)
    heel = both("M 8,590 L 34,590", stroke=LEATHER_D, stroke_width=3) + both("M 6,596 L 42,596", stroke=LEATHER_D, stroke_width=4)
    return "".join(s) + tunic + lower + sash + satchel(side=1, y=266, strap_from=(40, 126)) + extras + heel


def option_b_side(c=None, pid="chks"):
    """Profile facing right: we see his right side, so the satchel is near and the sash's long end is behind him."""
    c = dict(B_DEFAULT, **(c or {}))
    head = ("M 0,22 C 18,22 28,34 29,52 C 30,58 33,64 37,72 C 36,75 33,77 30,77 C 31,79 32,81 31,83 "
            "C 30,85 32,87 31,89 C 31,93 31,97 26,100 C 20,104 12,104 6,100 L -6,96 C -22,94 -30,80 -30,62 "
            "C -30,38 -18,22 0,22 Z")
    hair = ("M 27,44 C 22,30 12,22 0,22 C -18,22 -30,38 -30,62 C -30,78 -24,90 -10,96 L -6,88 C -14,82 -18,72 -16,60 "
            "C -14,48 -4,40 8,38 C 16,37 22,39 27,44 Z")
    torso = ("M -8,96 L 12,100 L 14,122 C 26,130 32,150 31,182 C 30,214 26,244 24,266 L 24,300 L -26,300 "
             "C -24,262 -28,224 -28,184 C -28,150 -22,130 -12,122 Z")
    arm = "M -8,128 C 6,126 10,140 10,180 C 10,220 12,260 13,300 C 14,320 15,332 15,344 L 3,346 C 2,330 0,300 -2,260 C -4,220 -8,170 -10,140 Z"
    legs = "".join([
        path("M -14,296 L 8,296 L 6,450 L 2,578 L -12,578 L -14,450 Z", fill=SKIN_D),       # far leg
        path("M -6,296 L 16,296 L 14,450 L 12,578 L -2,578 L -4,450 Z", fill=SKIN),         # near leg
        path("M -14,578 L 2,578 C 12,580 18,588 18,596 L -14,596 Z", fill=SKIN_D),
        path("M -4,578 L 12,578 C 24,580 30,588 30,597 L -4,597 Z", fill=SKIN),
        path("M -6,586 L 26,586 M -6,596 L 31,596", stroke=LEATHER_D, stroke_width=3.5),
    ])
    tunic = "".join([
        path("M -12,118 C -24,124 -30,142 -30,172 C -30,212 -28,252 -30,292 L 28,292 C 28,252 32,212 33,178 "
             "C 34,148 30,128 16,120 C 8,128 -4,126 -12,118 Z", fill=c["blouse"]),
        path("M -14,124 C -4,122 12,124 18,140 L 20,196 L -10,198 L -14,150 Z", fill=c["blouse"]),
        path("M -10,198 L 20,196", stroke=c["blouse_line"], stroke_width=2.5),
        path("M 14,120 C 8,126 0,126 -6,121", fill="none", stroke=c["blouse_line"], stroke_width=3),
    ])
    lower = "".join([
        '<defs><pattern id="%s" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="%s"/>'
        '<rect width="10" height="2" fill="%s"/><rect width="2" height="10" fill="%s"/></pattern></defs>'
        % (pid, c["paso"], c["paso_check"], c["paso_check"]),
        path("M -28,284 C -38,340 -36,420 -28,500 L 26,500 C 34,420 38,340 30,284 Z", fill="url(#%s)" % pid),
        path("M 22,288 L 32,288 C 36,360 36,420 32,470 L 24,470 Z", fill=c["paso_panel"]),
        path("M -28,286 C -38,296 -38,312 -30,320 L -20,318 L -20,288 Z", fill=c["paso_panel"]),
        path("M 0,300 C 2,380 2,440 0,498 M -24,334 C -10,362 10,362 26,334", fill="none", stroke=c["paso_panel"],
             stroke_width=2.5),
    ])
    sash = path("M -30,262 L 32,262 L 32,286 L -30,286 Z", fill=c["sash"])
    strap = path("M 2,121 C 14,160 18,210 14,266", fill="none", stroke=LEATHER, stroke_width=5, stroke_linecap="round")
    bag = ('<rect x="-8" y="264" width="36" height="44" rx="5" fill="%s"/><rect x="-8" y="264" width="36" height="13" rx="4" fill="%s"/>'
           '<rect x="8" y="274" width="5" height="9" fill="%s"/>' % (LEATHER, LEATHER_D, GOLD))
    face = "".join([
        path("M 16,57 C 20,55 25,55 28,58", fill="none", stroke=INK, stroke_width=2.4, stroke_linecap="round"),
        '<ellipse cx="23" cy="64" rx="3" ry="2.4" fill="%s"/>' % INK,
        path("M 25,84 C 27,85 29,85 30,84", fill="none", stroke="#6E3E2C", stroke_width=2, stroke_linecap="round"),
    ])
    ear = '<ellipse cx="-4" cy="64" rx="6" ry="10" fill="%s"/><circle cx="-3" cy="77" r="7" fill="%s"/>' % (SKIN_D, GOLD)
    hand = '<ellipse cx="10" cy="360" rx="8" ry="15" fill="%s"/>' % SKIN
    return (legs + lower + path(torso, fill=SKIN) + tunic + sash + strap + bag + path(head, fill=SKIN) + path(hair, fill=HAIR)
            + TOPKNOT.format(x=-8, y=15) + _tie(-8, 15, c["tie"]) + ear + face + path(arm, fill=SKIN)
            + path("M -14,124 C -4,122 12,124 18,140 L 20,196 L -10,198 L -14,150 Z", fill=c["blouse"])
            + path("M -10,198 L 20,196", stroke=c["blouse_line"], stroke_width=2.5) + hand)


def option_b_three_quarter(c=None, pid="chkt"):
    """Turned toward the viewer's right: his right side is near, the face sits right of centre."""
    c = dict(B_DEFAULT, **(c or {}))
    head = ("M -26,60 C -28,32 -14,22 4,22 C 20,22 30,32 30,52 C 30,56 33,62 34,68 C 32,70 30,72 30,74 "
            "C 28,86 18,100 4,102 C -12,100 -24,82 -26,60 Z")
    hair = ("M -26,58 C -29,30 -14,20 4,20 C 20,20 31,30 30,50 C 26,42 18,34 6,34 C -6,34 -16,40 -20,50 "
            "C -22,54 -24,58 -26,62 Z")
    torso = ("M -10,118 C -28,122 -48,124 -52,138 C -56,170 -48,200 -42,226 C -38,250 -38,270 -42,300 L 36,300 "
             "C 32,270 32,250 34,226 C 40,200 46,170 44,138 C 40,124 24,122 12,118 Z")
    near_arm = "M -48,132 C -60,140 -64,190 -64,250 C -65,290 -66,320 -64,346 L -53,346 C -53,320 -51,290 -49,252 C -47,210 -43,175 -41,150 Z"
    far_arm = "M 40,134 C 48,142 50,190 50,250 C 51,290 52,320 50,344 L 41,344 C 41,320 40,290 39,252 C 38,210 36,175 34,150 Z"
    near_leg = "M -40,298 L -4,298 C -6,360 -8,410 -10,450 C -12,500 -12,540 -12,578 L -30,578 C -30,540 -32,500 -32,450 C -34,400 -38,350 -40,298 Z"
    far_leg = "M 2,298 L 34,298 C 34,360 30,410 28,450 C 26,500 26,540 26,576 L 10,576 C 10,540 8,500 8,450 C 6,400 4,350 2,298 Z"
    feet = (path("M 8,574 L 28,574 C 38,577 42,586 40,594 L 8,594 Z", fill=SKIN_D)
            + path("M -32,576 L -10,576 C 0,580 6,589 4,597 L -32,597 Z", fill=SKIN)
            + path("M -34,586 L 2,586 M -34,596 L 5,596 M 6,584 L 38,584 M 6,594 L 40,594", stroke=LEATHER_D, stroke_width=3.5))
    tunic = "".join([
        path("M -10,118 C -30,122 -50,126 -56,138 L -66,190 L -46,197 L -42,176 C -42,210 -42,240 -44,290 L 38,290 "
             "C 36,240 36,210 36,176 L 40,194 L 54,190 L 46,138 C 42,126 28,122 14,118 C 10,129 -2,130 -10,118 Z",
             fill=c["blouse"]),
        path("M -10,118 C -2,130 10,129 14,118", fill="none", stroke=c["blouse_line"], stroke_width=3),
        path("M -26,180 C -22,220 -20,250 -22,286 M 22,180 C 24,220 26,250 24,286", fill="none", stroke=c["blouse_fold"], stroke_width=2.5),
    ])
    lower = "".join([
        '<defs><pattern id="%s" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="%s"/>'
        '<rect width="10" height="2" fill="%s"/><rect width="2" height="10" fill="%s"/></pattern></defs>'
        % (pid, c["paso"], c["paso_check"], c["paso_check"]),
        path("M -46,284 C -50,360 -48,440 -42,500 L -8,500 C -6,440 -2,380 2,330 Z", fill="url(#%s)" % pid),
        path("M 40,284 C 44,360 42,440 36,500 L 8,500 C 8,440 6,380 4,330 Z", fill="url(#%s)" % pid),
        path("M -6,284 L 18,284 L 14,470 L -2,470 Z", fill=c["paso_panel"]),
        path("M 2,290 L 4,466 M 8,290 L 8,468 M 14,290 L 12,466", fill="none", stroke=c["paso_check"], stroke_width=2),
    ])
    sash = "".join([
        path("M 30,278 C 36,320 38,370 38,410 L 46,408 C 46,370 44,320 40,278 Z", fill=c["sash_end"]),
        path("M -46,262 L 42,262 L 42,286 L -46,286 Z", fill=c["sash"]),
    ])
    face = "".join([
        path("M -2,58 C 2,55 8,55 11,58 M 20,58 C 23,56 27,56 29,58", fill="none", stroke=INK, stroke_width=2.4, stroke_linecap="round"),
        '<ellipse cx="6" cy="64" rx="3.2" ry="2.4" fill="%s"/><ellipse cx="25" cy="64" rx="2.4" ry="2.2" fill="%s"/>' % (INK, INK),
        path("M 30,66 L 33,76 L 27,79", fill="none", stroke=SKIN_D, stroke_width=2, stroke_linecap="round"),
        path("M 8,88 C 13,90 18,90 22,87", fill="none", stroke="#6E3E2C", stroke_width=2.2, stroke_linecap="round"),
    ])
    ear = '<ellipse cx="-24" cy="65" rx="5" ry="9" fill="%s"/><circle cx="-25" cy="76" r="7.5" fill="%s"/>' % (SKIN_D, GOLD)
    hands = ('<ellipse cx="-59" cy="360" rx="9" ry="15" fill="%s"/><ellipse cx="46" cy="358" rx="7" ry="14" fill="%s"/>'
             % (SKIN, SKIN_D))
    bag = (path("M 36,126 L -50,268", stroke=LEATHER, stroke_width=5, fill="none", stroke_linecap="round")
           + '<rect x="-74" y="266" width="38" height="44" rx="5" fill="%s"/><rect x="-74" y="266" width="38" height="13" rx="4" fill="%s"/>'
             '<rect x="-57.5" y="276" width="5" height="9" fill="%s"/>' % (LEATHER, LEATHER_D, GOLD))
    return (path(far_arm, fill=SKIN_D) + path(far_leg, fill=SKIN_D) + path(near_leg, fill=SKIN) + feet
            + path("M -9,96 L 13,96 L 15,124 L -11,124 Z", fill=SKIN_D) + path(torso, fill=SKIN) + path(near_arm, fill=SKIN)
            + tunic + lower + sash + bag + hands + path(head, fill=SKIN) + path(hair, fill=HAIR)
            + TOPKNOT.format(x=-4, y=13) + _tie(-4, 13, c["tie"]) + ear + face)
