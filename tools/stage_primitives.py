#!/usr/bin/env python3
"""Stage primitives for code-driven puzzle animation (PIL only). Complements video_core.py.

Implements the vocabulary in templates/stage-layout-spec.md:
  timing:  pop(t,dur) slide(t,dur,dist) fly(t,p0,p1,dur) stagger(i,gap) dim_level(t,t0,hold)
  drawing: dim_overlay(img,alpha,text) stamp(d,xy,text,color) dashed_box(d,box,color) counter_badge(d,xy,value)
           case_tag(d,xy,text) lock_icon(d,xy) label_above(d,xy,text) phrase_lines(text,max_len)
Fonts: set FONT_PATH / FONT_INDEX for CJK (Noto Sans CJK by default). Run this file directly to render a
self-test frame to /tmp/stage-primitives-demo.png. Colours follow the grey stage / red-wrong / green-ok /
yellow-highlight convention; project branding may override the constants.
"""
import math, os, re
from PIL import Image, ImageDraw, ImageFont

STAGE = (189, 189, 189)
INK = (20, 20, 20)
RED = (200, 40, 40)
GREEN = (60, 140, 80)
YELLOW = (240, 200, 40)
WHITE = (255, 255, 255)
FONT_PATH = os.environ.get("FONT_PATH", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
FONT_INDEX = int(os.environ.get("FONT_INDEX", "2"))


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)
    except Exception:
        return ImageFont.load_default()


# ---------- timing (all return values in [0,1] or pixel offsets; t in seconds since the event) ----------
def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def pop(t, dur=0.22, overshoot=1.1):
    """Scale factor for pop-in: 0 -> overshoot -> 1."""
    if t <= 0:
        return 0.0
    if t >= dur:
        return 1.0
    x = t / dur
    return overshoot * math.sin(x * math.pi / 2) if x < 0.7 else overshoot - (overshoot - 1) * ((x - 0.7) / 0.3)


def slide(t, dur=0.3, dist=60):
    """Pixel offset (positive = still below final position) and alpha for slide-up entrance."""
    x = ease_out(t / dur) if dur else 1
    return dist * (1 - x), x


def fly(t, p0, p1, dur=0.6, arc=0.0):
    """Position along a path from p0 to p1 with ease-in-out and optional arc height (pixels)."""
    x = ease_in_out(t / dur) if dur else 1
    px = p0[0] + (p1[0] - p0[0]) * x
    py = p0[1] + (p1[1] - p0[1]) * x - arc * math.sin(x * math.pi)
    return px, py


def stagger(i, gap=0.1):
    return i * gap


def dim_level(t, fade=0.3, hold=2.0, depth=0.55):
    """Darkening amount 0..depth for a think-beat starting at t=0 (fade in, hold, fade out)."""
    if t < 0:
        return 0.0
    if t < fade:
        return depth * t / fade
    if t < fade + hold:
        return depth
    if t < 2 * fade + hold:
        return depth * (1 - (t - fade - hold) / fade)
    return 0.0


# ---------- drawing ----------
def dim_overlay(img, amount, text=None, size=220):
    """Darken the whole frame by `amount` (0..1) and optionally draw a big centred number/'?'."""
    if amount <= 0 and not text:
        return img
    dark = Image.new("RGB", img.size, (0, 0, 0))
    out = Image.blend(img, dark, max(0.0, min(1.0, amount)))
    if text:
        d = ImageDraw.Draw(out)
        f = font(size)
        w, h = d.textbbox((0, 0), text, font=f)[2:]
        d.text(((img.width - w) / 2, (img.height - h) / 2 - size * 0.1), text, fill=WHITE, font=f)
    return out


def stamp(d, xy, text, color=GREEN, size=34, pad=10, scale=1.0):
    """Rounded rectangle stamp (正确/安全/出局). `scale` lets you drive it with pop()."""
    f = font(int(size * scale))
    w, h = d.textbbox((0, 0), text, font=f)[2:]
    x, y = xy
    box = [x - w / 2 - pad, y - h / 2 - pad / 2, x + w / 2 + pad, y + h / 2 + pad / 2]
    d.rounded_rectangle(box, radius=8, outline=color, width=4, fill=(255, 255, 255))
    d.text((x - w / 2, y - h / 2 - 2), text, fill=color, font=f)


def dashed_box(d, box, color=RED, dash=12, width=4):
    x0, y0, x1, y1 = box
    for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        length = math.hypot(bx - ax, by - ay)
        n = max(1, int(length / dash))
        for i in range(0, n, 2):
            t0, t1 = i / n, min(1, (i + 1) / n)
            d.line([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)], fill=color, width=width)


def counter_badge(d, xy, value, size=30, fill=WHITE, ink=INK):
    f = font(size)
    txt = str(value)
    w, h = d.textbbox((0, 0), txt, font=f)[2:]
    x, y = xy
    d.rounded_rectangle([x - w / 2 - 12, y - h / 2 - 6, x + w / 2 + 12, y + h / 2 + 6], radius=6, fill=fill, outline=ink, width=3)
    d.text((x - w / 2, y - h / 2 - 3), txt, fill=ink, font=f)


def case_tag(d, xy, text, size=32):
    """Top-right style case label (情况一 / 情况二)."""
    f = font(size)
    w, h = d.textbbox((0, 0), text, font=f)[2:]
    x, y = xy
    d.rectangle([x - w - 24, y, x, y + h + 14], fill=INK)
    d.text((x - w - 12, y + 5), text, fill=WHITE, font=f)


def lock_icon(d, xy, r=14, color=INK):
    x, y = xy
    d.arc([x - r * 0.6, y - r * 1.6, x + r * 0.6, y - r * 0.2], 180, 360, fill=color, width=4)
    d.rounded_rectangle([x - r, y - r * 0.6, x + r, y + r], radius=4, fill=color)
    d.ellipse([x - 4, y - 2, x + 4, y + 6], fill=WHITE)


def label_above(d, xy, text, size=26, color=INK):
    f = font(size)
    w, h = d.textbbox((0, 0), text, font=f)[2:]
    x, y = xy
    d.rounded_rectangle([x - w / 2 - 8, y - h - 12, x + w / 2 + 8, y - 2], radius=6, fill=WHITE, outline=color, width=2)
    d.text((x - w / 2, y - h - 9), text, fill=color, font=f)


def phrase_lines(text, max_len=12):
    """Split a narration sentence into phrase-level display lines (5–12 chars) at punctuation, then by length."""
    parts = [p for p in re.split(r"[，。；：！？,.;:!?、]", text) if p.strip()]
    lines = []
    for p in parts:
        p = p.strip()
        while len(p) > max_len + 2:  # tolerate +2 so we never strand a 1–2 char tail
            cut = max_len
            for k in range(max_len, max(4, max_len - 5), -1):  # prefer breaking before a particle/conjunction
                if p[k - 1] in "的了是在和就把被到给" and len(p) - k >= 3:
                    cut = k
                    break
            lines.append(p[:cut])
            p = p[cut:]
        if p:
            lines.append(p)
    return lines


def subtitle(d, frame_size, text, size=44, y_ratio=0.84, ink=INK, stroke=WHITE):
    f = font(size)
    w, h = d.textbbox((0, 0), text, font=f)[2:]
    x = (frame_size[0] - w) / 2
    y = frame_size[1] * y_ratio - h / 2
    d.text((x, y), text, fill=ink, font=f, stroke_width=3, stroke_fill=stroke)


# ---------- self-test ----------
if __name__ == "__main__":
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), STAGE)
    d = ImageDraw.Draw(img)
    d.text((40, 30), "墨问", fill=INK, font=font(36))
    case_tag(d, (W - 40, 40), "情况一")
    for i in range(5):  # a row of entities with labels, numbers, one locked, one crossed
        x = 560 + i * 200
        s = pop(0.5 - stagger(i), 0.22)
        r = int(60 * s)
        d.ellipse([x - r, 520 - r, x + r, 520 + r], outline=INK, width=4, fill=WHITE)
        label_above(d, (x, 440), f"{i + 1}号")
        counter_badge(d, (x, 640), 5 - i)
    lock_icon(d, (960, 520))
    d.line([(1340, 500), (1380, 540)], fill=RED, width=8)
    d.line([(1380, 500), (1340, 540)], fill=RED, width=8)
    dashed_box(d, [500, 440, 640, 680])
    stamp(d, (760, 760), "正确", GREEN, scale=pop(0.3))
    stamp(d, (1160, 760), "安全", GREEN)
    px, py = fly(0.3, (300, 300), (960, 300), 0.6, arc=80)
    d.ellipse([px - 20, py - 20, px + 20, py + 20], fill=YELLOW, outline=INK, width=3)
    lines = phrase_lines("每切开一片，就把其中一半放进第一天的盘子，另一半放进第二天的盘子。")
    subtitle(d, (W, H), lines[1])
    img = dim_overlay(img, dim_level(0.5), "2")
    img.save("/tmp/stage-primitives-demo.png")
    print("phrase_lines:", lines)
    print("saved /tmp/stage-primitives-demo.png")
