"""Simple cartoon protagonist ("you") drawn procedurally with PIL.

The figure is intentionally minimal: round head, big eyes, hoodie, stick limbs.
All sizes are relative to `s` (scale, 1.0 = ~520 px tall standing figure).
"""
import math
from PIL import ImageDraw

SKIN = (236, 214, 178)
HOODIE = (196, 64, 40)
HOODIE_DARK = (150, 44, 28)
JEANS = (52, 58, 74)
SHOE = (24, 24, 28)
INK = (14, 12, 14)


def _limb(d, p0, p1, width, color, s):
    o = max(3, int(5 * s))
    d.line([p0, p1], fill=INK, width=int(width + 2 * o))
    d.line([p0, p1], fill=color, width=int(width))
    for p, w in ((p0, width), (p1, width)):
        r = (w + 2 * o) / 2
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=INK)
        r = w / 2
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def draw_character(img, x, feet_y, s=1.0, t=0.0, view="front", expr="neutral",
                   tremble=0.0, turn=1.0, arm_raise=0.0, walk=0.0):
    """Draw the figure onto `img` (RGB PIL image).

    view: "front" or "back"; turn (0..1) blends back->front for head turns.
    expr: "neutral", "scared", "terrified".
    tremble: 0..1 shaking amount. arm_raise: 0..1 lifts the right arm (knocking/peephole).
    walk: walk-cycle phase speed (0 = standing).
    """
    d = ImageDraw.Draw(img)
    jx = math.sin(t * 61) * 6 * tremble * s
    jy = math.cos(t * 47) * 3 * tremble * s
    breathe = math.sin(t * 2.4) * 4 * s
    x += jx
    feet_y += jy

    leg = 190 * s
    hip_y = feet_y - leg
    torso_h = 170 * s + breathe * 0.3
    sh_y = hip_y - torso_h
    head_r = 70 * s
    head_c = (x, sh_y - head_r * 0.92 + breathe * 0.2)
    lw = 30 * s

    # legs (walk cycle swings feet)
    sw = math.sin(t * 7) * 40 * s * walk
    for side, ph in ((-1, sw), (1, -sw)):
        hip = (x + side * 26 * s, hip_y)
        foot = (x + side * 32 * s + ph, feet_y - 14 * s)
        _limb(d, hip, foot, lw, JEANS, s)
        sx = foot[0] + (14 * s if view == "front" else -6 * s) * (1 if side > 0 else -1) * 0.4
        d.rounded_rectangle([sx - 30 * s, feet_y - 30 * s, sx + 30 * s, feet_y + 4 * s], int(12 * s), fill=SHOE, outline=INK, width=max(2, int(4 * s)))

    # arms behind torso when seen from back
    def arms():
        for side in (-1, 1):
            sh = (x + side * 62 * s, sh_y + 26 * s)
            sway = math.sin(t * 2.4 + side) * 6 * s
            if side == 1 and arm_raise > 0:
                a = arm_raise
                hand = (sh[0] + 30 * s * (1 - a) + 10 * s, sh[1] + 150 * s * (1 - a) - 120 * s * a)
            else:
                hand = (sh[0] + side * 18 * s + sway - sw * 0.5 * side, sh[1] + 150 * s)
            _limb(d, sh, hand, lw * 0.92, HOODIE, s)
            r = 19 * s
            d.ellipse([hand[0] - r, hand[1] - r, hand[0] + r, hand[1] + r], fill=SKIN, outline=INK, width=max(2, int(4 * s)))

    if view == "back":
        arms()
    # torso (hoodie)
    d.rounded_rectangle([x - 72 * s, sh_y, x + 72 * s, hip_y + 18 * s], int(36 * s), fill=HOODIE, outline=INK, width=max(3, int(5 * s)))
    if view == "front":
        d.line([x, sh_y + 30 * s, x, hip_y + 10 * s], fill=HOODIE_DARK, width=max(2, int(4 * s)))  # zipper
        d.rounded_rectangle([x - 46 * s, hip_y - 50 * s, x + 46 * s, hip_y - 6 * s], int(14 * s), outline=HOODIE_DARK, width=max(2, int(4 * s)))  # pocket
    else:
        d.chord([x - 70 * s, sh_y - 30 * s, x + 70 * s, sh_y + 80 * s], 0, 180, fill=HOODIE_DARK, outline=INK, width=max(3, int(5 * s)))  # hood
    if view == "front":
        arms()

    # head
    hx, hy = head_c
    d.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=SKIN, outline=INK, width=max(3, int(6 * s)))
    # hair
    d.chord([hx - head_r, hy - head_r, hx + head_r, hy + head_r * 0.7], 180, 360, fill=(54, 38, 30), outline=INK, width=max(3, int(6 * s)))
    if view == "back" and turn <= 0.05:
        d.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=(54, 38, 30), outline=INK, width=max(3, int(6 * s)))
        return
    face_shift = (1 - turn) * head_r * 0.75 if view == "back" else 0
    blink = (t % 3.7) < 0.12 and expr == "neutral"
    eye_w = {"neutral": 15, "scared": 19, "terrified": 22}[expr] * s
    eye_h = {"neutral": 20, "scared": 26, "terrified": 30}[expr] * s
    pupil = {"neutral": 8, "scared": 6, "terrified": 4}[expr] * s
    look = math.sin(t * 0.7) * 3 * s
    for side in (-1, 1):
        if view == "back" and turn < 0.6 and side == -1:
            continue
        ex = hx + side * 27 * s + face_shift
        ey = hy + 4 * s
        if blink:
            d.line([ex - eye_w, ey, ex + eye_w, ey], fill=INK, width=max(2, int(4 * s)))
            continue
        d.ellipse([ex - eye_w, ey - eye_h, ex + eye_w, ey + eye_h], fill=(250, 250, 250), outline=INK, width=max(2, int(4 * s)))
        d.ellipse([ex - pupil + look, ey - pupil, ex + pupil + look, ey + pupil], fill=INK)
    if expr == "neutral":
        d.arc([hx - 18 * s + face_shift, hy + 22 * s, hx + 18 * s + face_shift, hy + 42 * s], 20, 160, fill=INK, width=max(2, int(4 * s)))
    else:
        m = 9 if expr == "scared" else 14
        d.ellipse([hx - m * s + face_shift, hy + 30 * s, hx + m * s + face_shift, hy + (30 + m * 1.8) * s], fill=(60, 20, 20), outline=INK, width=max(2, int(4 * s)))
        if expr == "terrified":  # sweat drop
            d.polygon([(hx + 62 * s, hy - 30 * s), (hx + 70 * s, hy - 6 * s), (hx + 54 * s, hy - 6 * s)], fill=(150, 200, 255))
