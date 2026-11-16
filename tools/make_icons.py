#!/usr/bin/env python3
"""Render the cute chihuahua app icon for the family record PWA.

The character is drawn from the same geometry as faceSVG() / avatarSVG('haram')
inside family-record/index.html, scaled into 512 and 192 px app icons.
"""
import math
import os
import re
from PIL import Image, ImageDraw, ImageFilter

S = 2048          # master canvas size
K = S * 0.0082    # one unit of the 100-unit character space, in px
INK = (92, 74, 60, 255)
CREAM = (255, 252, 246, 255)
BLUSH = (255, 213, 223, 255)
EYE = (61, 48, 41, 255)
ACC = (255, 143, 177, 255)      # haram accent pink (bow)
EAR_IN = (255, 217, 228, 255)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)


def T(x, y):
    return (S / 2 + (x - 50) * K, S / 2 + (y - 53.75) * K)


def cubic(p0, p1, p2, p3, n=90):
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        out.append((
            mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
            mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1],
        ))
    return out


NUM = re.compile(r"-?\d*\.?\d+")


def parse_path(d):
    """Parse M/L/C/H/V/Z (absolute and relative) into a polyline."""
    toks = re.findall(r"[MCLHVSZmclhvsz]|-?\d*\.?\d+", d)
    i = 0
    cmd = None
    cur = (0.0, 0.0)
    start = cur
    prev_c2 = None
    pts = []

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if t in "MCLHVSZmclhvsz":
            cmd = t
            i += 1
            if cmd in "Zz":
                pts.append(start)
                cur = start
                continue
        rel = cmd.islower()
        C = cmd.upper()
        base = cur
        if C == "M":
            x, y = num(), num()
            cur = (base[0] + x, base[1] + y) if rel else (x, y)
            start = cur
            pts.append(cur)
            cmd = "l" if rel else "L"
        elif C == "L":
            x, y = num(), num()
            cur = (base[0] + x, base[1] + y) if rel else (x, y)
            pts.append(cur)
        elif C == "H":
            x = num()
            cur = (base[0] + x, base[1]) if rel else (x, base[1])
            pts.append(cur)
        elif C == "V":
            y = num()
            cur = (base[0], base[1] + y) if rel else (base[0], y)
            pts.append(cur)
        elif C == "C":
            c1 = (num(), num())
            c2 = (num(), num())
            e = (num(), num())
            if rel:
                p1 = (base[0] + c1[0], base[1] + c1[1])
                p2 = (base[0] + c2[0], base[1] + c2[1])
                p3 = (base[0] + e[0], base[1] + e[1])
            else:
                p1, p2, p3 = c1, c2, e
            pts += cubic(base, p1, p2, p3)[1:]
            cur = p3
            prev_c2 = p2
        elif C == "S":
            c2 = (num(), num())
            e = (num(), num())
            p1 = ((2 * base[0] - prev_c2[0], 2 * base[1] - prev_c2[1])
                  if prev_c2 else base)
            if rel:
                p2 = (base[0] + c2[0], base[1] + c2[1])
                p3 = (base[0] + e[0], base[1] + e[1])
            else:
                p2, p3 = c2, e
            pts += cubic(base, p1, p2, p3)[1:]
            cur = p3
            prev_c2 = p2
    return pts


def xform(pts, translate=(0, 0), rotate=0.0, scale=1.0, origin=(0, 0)):
    """translate + rotate(deg) + scale about origin, matching SVG transform order."""
    a = math.radians(rotate)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for (x, y) in pts:
        x = (x - origin[0]) * scale
        y = (y - origin[1]) * scale
        out.append((x * ca - y * sa + origin[0] + translate[0],
                    x * sa + y * ca + origin[1] + translate[1]))
    return out


def sp(pts):
    return [T(x, y) for (x, y) in pts]


def fill(draw, pts, color):
    draw.polygon(sp(pts), fill=color)


def stroke(draw, pts, color, w, close=True):
    p = sp(pts)
    if close and p[0] != p[-1]:
        p = p + [p[0]]
    draw.line(p, fill=color, width=max(1, int(round(w * K))), joint="curve")


def shape(draw, pts, fill_color, stroke_color=None, stroke_w=None):
    fill(draw, pts, fill_color)
    if stroke_color:
        stroke(draw, pts, stroke_color, stroke_w)


def ellipse(draw, cx, cy, rx, ry, fill_color=None, stroke_color=None, stroke_w=None):
    x0, y0 = T(cx - rx, cy - ry)
    x1, y1 = T(cx + rx, cy + ry)
    draw.ellipse([x0, y0, x1, y1], fill=fill_color, outline=stroke_color,
                 width=int(round(stroke_w * K)) if stroke_w else 0)


# ---------------- character geometry (from faceSVG) ----------------
EARS = [
    "M45 37.5C35.6 33 23.6 26.6 18.2 21.6C14.9 19 11.7 22 13.5 25.5L25.4 46Z",
    "M55 37.5C64.4 33 76.4 26.6 81.8 21.6C85.1 19 88.3 22 86.5 25.5L74.6 46Z",
]
EAR_INNER = [
    "M41.5 36C33 32 23.6 26.8 19.9 23.4C17.4 21.2 15.8 23.2 17.2 25.7L26.4 43Z",
    "M58.5 36C67 32 76.4 26.8 80.1 23.4C82.6 21.2 84.2 23.2 82.8 25.7L73.6 43Z",
]
MOUTH = "M45.2 64.2c1.6 2.8 3.2 2.8 4.8 0c1.6 2.8 3.2 2.8 4.8 0"
STRAWBERRY = ("M50 83.5c-5.8 0-9.6-3.6-9.6-7.6c0-2.2 1.8-3.6 4.3-3.6h10.6"
              "c2.5 0 4.3 1.4 4.3 3.6c0 4-3.8 7.6-9.6 7.6Z")
STRAW_LEAF = "M44.8 72.6c1.6-2.8 3.4-4.4 5.2-4.4c1.8 0 3.6 1.6 5.2 4.4"
STRAW_STEM = "M50 68.2v-2.4"
BOW_A = "M0 0c-6-5-11-3-11 2s5 7 11 2Z"
BOW_B = "M0 0c6-5 11-3 11 2s-5 7-11 2Z"


def draw_character(d, with_extras=True):
    for p in EARS:
        shape(d, parse_path(p), CREAM, INK, 2.7)
    for p in EAR_INNER:
        fill(d, parse_path(p), EAR_IN)
    ellipse(d, 50, 58, 29, 26.5, CREAM, INK, 2.7)
    ellipse(d, 30.5, 66.5, 7.2, 4.4, BLUSH)
    ellipse(d, 69.5, 66.5, 7.2, 4.4, BLUSH)
    ellipse(d, 39.5, 56.5, 2.9, 3.7, EYE)
    ellipse(d, 60.5, 56.5, 2.9, 3.7, EYE)
    ellipse(d, 38.5, 55.1, 0.95, 1.05, (255, 255, 255, 240))
    ellipse(d, 59.5, 55.1, 0.95, 1.05, (255, 255, 255, 240))

    mouth = parse_path(MOUTH)
    p = sp(mouth)
    d.line(p, fill=INK, width=int(round(2.0 * K)), joint="curve")
    for q in (p[0], p[-1]):
        rr = K * 1.0
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=INK)

    ellipse(d, 41.5, 83.5, 7, 5, CREAM, INK, 2.2)
    ellipse(d, 58.5, 83.5, 7, 5, CREAM, INK, 2.2)

    if not with_extras:
        return
    # strawberry held in the paws
    shape(d, parse_path(STRAWBERRY), (255, 126, 146, 255), INK, 1.9)
    stroke(d, parse_path(STRAW_LEAF), (123, 201, 143, 255), 1.7, close=False)
    stroke(d, parse_path(STRAW_STEM), INK, 1.7, close=False)
    for (cx, cy) in ((46.4, 76.6), (53.6, 76.6), (50, 79.4)):
        ellipse(d, cx, cy, 0.95, 0.95, (255, 227, 234, 255))
    # bow on the right ear
    for bow, rot in ((BOW_A, 12), (BOW_B, 12)):
        pts = xform(parse_path(bow), translate=(70, 17), rotate=rot)
        shape(d, pts, ACC, INK, 1.7)
    knot = xform([(-2.6, -0.6), (2.6, -0.6), (2.6, 4.6), (-2.6, 4.6)],
                 translate=(70, 17), rotate=12)
    shape(d, knot, (255, 211, 223, 255), INK, 1.6)


def build(with_extras=True):
    top = (255, 214, 230)
    bot = (255, 236, 206)
    grad = Image.new("RGB", (1, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / (S - 1)
        gd.point((0, y), tuple(int(top[c] + (bot[c] - top[c]) * t) for c in range(3)))
    img = grad.resize((S, S), Image.BICUBIC).convert("RGBA")

    r = S * 0.35
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([S / 2 - r, S / 2 - r + S * 0.014, S / 2 + r, S / 2 + r + S * 0.014],
               fill=(190, 145, 125, 62))
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.014))
    img = Image.alpha_composite(img, shadow)

    disc = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(disc).ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r],
                                 fill=(255, 253, 247, 255))
    img = Image.alpha_composite(img, disc)

    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_character(ImageDraw.Draw(layer), with_extras=with_extras)
    return Image.alpha_composite(img, layer).convert("RGB")


if __name__ == "__main__":
    master = build(with_extras=True)
    master.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "icon-512.png"), optimize=True)
    master.resize((192, 192), Image.LANCZOS).save(os.path.join(OUT, "icon-192.png"), optimize=True)
    master.resize((180, 180), Image.LANCZOS).save(os.path.join(OUT, "apple-touch-icon.png"), optimize=True)
    print("wrote icon-512.png icon-192.png apple-touch-icon.png")
