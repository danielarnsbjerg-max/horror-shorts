"""Midnight Stories episode renderer.

Usage:  python -m engine.render series/<series>/<epNN>/episode.py [out.mp4] [--preview t1,t2,...]

An episode file defines EPISODE (see series/the-317-knock/ep01/episode.py).
Output: 1080x1920, 30 fps, H.264 + AAC, ready for Reels / TikTok / Shorts.
"""
import importlib.util, math, os, subprocess, sys, tempfile, wave
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from engine.character import draw_character

W, H, FPS, SR = 1080, 1920, 30, 44100
BAND_TOP, BAND_H = 330, 1330
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
YELLOW = (255, 224, 32)
RED = (232, 36, 36)

def font(path, size): return ImageFont.truetype(path, size)
def ease(x): x = max(0.0, min(1.0, x)); return 0.5 - 0.5 * math.cos(math.pi * x)
def lerp(a, b, u): return a + (b - a) * u
def val(v, u):  # value or (start, end) tuple interpolated over beat progress u
    return lerp(v[0], v[1], ease(u)) if isinstance(v, (tuple, list)) else v

# ---------------------------------------------------------------- audio io
def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af",
                          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

def reverb(x, secs=1.0, wet=0.2, seed=1):
    r = np.random.default_rng(seed); m = int(secs * SR)
    ir = r.normal(0, 1, m) * np.exp(-np.arange(m) / SR * 5.0); ir /= np.abs(ir).sum() / 3
    y = np.convolve(x, ir)[: len(x) + m]; y = np.pad(y, (0, len(x) + m - len(y)))
    return np.concatenate([x, np.zeros(m)]) * (1 - wet) + y * wet

# ---------------------------------------------------------------- timeline
class Episode:
    def __init__(self, spec, base):
        self.spec, self.base = spec, base
        self.scenes = spec["scenes"]
        self.beats, self.words, self.knocks, self.rings, self.cuts = [], [], [], [], []
        t, prev = 0.0, None
        for b in spec["beats"]:
            b = dict(b)
            if "knock" in b:
                b.setdefault("scene", prev["scene"] if prev else None)
                for k in range(b["knock"]): self.knocks.append(t + 0.25 + k * 0.36)
                b["start"], b["dur"], b["clip"] = t, 0.5 + b["knock"] * 0.36 + 0.5, None
            elif "ring" in b:  # phone ringing: n rings of ~1.2 s
                b.setdefault("scene", prev["scene"] if prev else None)
                for k in range(b["ring"]): self.rings.append(t + 0.2 + k * 1.3)
                b["start"], b["dur"], b["clip"] = t, 0.4 + b["ring"] * 1.3, None
            else:
                clip = load_audio(os.path.join(base, spec["vo_dir"], b["vo"] + ".mp3"))
                b["clip"] = clip
                d = len(clip) / SR
                b["start"], b["dur"] = t, d + b.get("pad", 0.3) + b.get("hold", 0.0)
                self._words(b, t + 0.05, d)
            if prev is None or b["scene"] != prev["scene"]: self.cuts.append(t)
            t += b["dur"]; self.beats.append(b); prev = b
        self.dur = t + spec.get("tail", 0.8)
        self.beats[-1]["dur"] += spec.get("tail", 0.8)
        # clock: hits target at the first beat flagged clock_hit
        hit = next(b["start"] for b in self.beats if b.get("clock_hit"))
        hh, mm, ss = map(int, spec["clock_target"].split(":"))
        self.clock0 = hh * 3600 + mm * 60 + ss - hit
        self.clock_hit = hit
        self.groups = self._group()

    def _words(self, b, t0, d):
        toks = b["text"].split()
        weights = [len(w.strip("*")) + 2 + (3 if w.endswith(("...", ".", ",", "?")) else 0) for w in toks]
        tot = sum(weights); t = t0
        for w, wt in zip(toks, weights):
            dur = d * 0.97 * wt / tot
            self.words.append({"w": w.replace("*", "").upper(), "hi": "*" in w,
                               "t": t, "end": t + dur, "beat": len(self.beats), "brk": w.endswith(("...", ".", ",", "?"))})
            t += dur

    def _group(self):
        groups, cur = [], []
        for i, w in enumerate(self.words):
            cur.append(w)
            nxt = self.words[i + 1] if i + 1 < len(self.words) else None
            chars = sum(len(x["w"]) for x in cur)
            if nxt is None or w["brk"] or nxt["beat"] != w["beat"] or len(cur) >= 3 or chars + len(nxt["w"]) > 16:
                groups.append(cur); cur = []
        out = []
        for i, g in enumerate(groups):
            end = groups[i + 1][0]["t"] if i + 1 < len(groups) and groups[i + 1][0]["beat"] == g[0]["beat"] else g[-1]["end"] + 0.35
            out.append({"words": g, "t": g[0]["t"], "end": end})
        return out

    def beat_at(self, t):
        for b in self.beats:
            if b["start"] <= t < b["start"] + b["dur"]: return b
        return self.beats[-1]

# ---------------------------------------------------------------- visuals
class Look:
    def __init__(self, ep):
        self.ep = ep
        self.img, self.fill = {}, {}
        for name, sc in ep.scenes.items():
            im = Image.open(os.path.join(ep.base, sc["bg"])).convert("RGB")
            self.img[name] = im
            k = H / im.height; cover = im.resize((int(im.width * k), H), Image.BILINEAR)
            x0 = (cover.width - W) // 2
            f = cover.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(28))
            self.fill[name] = Image.eval(f, lambda v: int(v * 0.33))
        m = np.ones((BAND_H, W), np.float32)
        fe = 150
        ramp = np.linspace(0, 1, fe)[:, None]
        m[:fe] *= ramp; m[-fe:] *= ramp[::-1]
        self.band_mask = Image.fromarray((m * 255).astype(np.uint8), "L")
        yy, xx = np.mgrid[0:H, 0:W]
        self.vign = np.clip(1.35 - 1.05 * np.sqrt(((xx - W / 2) / (W * .7)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2), 0.25, 1)[..., None].astype(np.float32)
        rng = np.random.default_rng(5)
        self.grain = [rng.normal(0, 7, (H, W, 1)).astype(np.float32) for _ in range(6)]
        self.peep = {}
        self.cap_cache, self.hud_cache = {}, {}
        self.f_cap = font(FONT_BLACK, 96)
        self.f_hud = font(FONT_BLACK, 40)
        self.f_clock = font(FONT_BLACK, 92)
        self.f_choice = font(FONT_BLACK, 70)
        self.f_ab = font(FONT_BLACK, 150)
        self.f_q = font(FONT_BLACK, 104)
        self.f_pill = font(FONT_BLACK, 78)
        self.f_handle = font(FONT_XB, 60)

    def band(self, scene, cam, u, shake=(0, 0)):
        im = self.img[scene]
        z = val(cam.get("zoom", 1.0), u); cx = val(cam.get("x", 0.5), u); cy = val(cam.get("y", 0.5), u)
        ch = im.height / z; cw = ch * W / BAND_H
        if cw > im.width: cw = im.width; ch = cw * BAND_H / W
        cx = min(max(cx * im.width, cw / 2), im.width - cw / 2); cy = min(max(cy * im.height, ch / 2), im.height - ch / 2)
        k = cw / W
        box = (cx - cw / 2 + shake[0] * k, cy - ch / 2 + shake[1] * k, cx + cw / 2 + shake[0] * k, cy + ch / 2 + shake[1] * k)
        box = (max(0, box[0]), max(0, box[1]), min(im.width, box[2]), min(im.height, box[3]))
        return im.resize((W, BAND_H), Image.BICUBIC, box=box)

    def peephole(self, scene):
        if scene in self.peep: return self.peep[scene]
        src = np.asarray(self.img[scene].resize((W, int(W * 720 / 1280 * 1.0)), Image.BICUBIC), np.float32)
        sh, sw = src.shape[:2]
        R = 470; cx, cy = W / 2, BAND_TOP + BAND_H / 2
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dx, dy = (xx - cx) / R, (yy - cy) / R
        r = np.sqrt(dx ** 2 + dy ** 2)
        rr = np.where(r < 1, r ** 1.6, r)  # barrel / fisheye
        sx = np.clip(sw / 2 + dx / np.maximum(r, 1e-6) * rr * sw * 0.48, 0, sw - 1).astype(int)
        sy = np.clip(sh / 2 + dy / np.maximum(r, 1e-6) * rr * sw * 0.48, 0, sh - 1).astype(int)
        out = src[sy, sx]
        edge = np.clip((1 - r) * 6, 0, 1)[..., None] * np.clip(1.15 - r ** 2 * 0.6, 0, 1)[..., None]
        out = out * edge
        ring = ((r > 1.0) & (r < 1.07))[..., None]
        out = np.where(ring, np.array([38, 36, 40], np.float32), out)
        self.peep[scene] = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        return self.peep[scene]

    # ---- text
    def caption(self, gi, g):
        if gi in self.cap_cache: return self.cap_cache[gi]
        words = g["words"]
        lines, cur = [], []
        total = sum(len(w["w"]) for w in words) + len(words) - 1
        for w in words:
            cur.append(w)
            if total > 12 and len(lines) == 0 and sum(len(x["w"]) + 1 for x in cur) >= total / 2 and w is not words[-1]:
                lines.append(cur); cur = []
        if cur: lines.append(cur)
        f = self.f_cap; sp = f.getlength(" "); lh = 108
        Wl = int(max(sum(f.getlength(w["w"]) for w in ln) + sp * (len(ln) - 1) for ln in lines)) + 80
        Hl = lh * len(lines) + 60
        txt = Image.new("RGBA", (Wl, Hl), (0, 0, 0, 0)); glow = Image.new("RGBA", (Wl, Hl), (0, 0, 0, 0))
        dt, dg = ImageDraw.Draw(txt), ImageDraw.Draw(glow)
        for li, ln in enumerate(lines):
            lw = sum(f.getlength(w["w"]) for w in ln) + sp * (len(ln) - 1)
            x = (Wl - lw) / 2; y = 30 + li * lh
            for w in ln:
                col = YELLOW if w["hi"] else (255, 255, 255)
                dg.text((x, y), w["w"], font=f, fill=(*col, 170 if w["hi"] else 90))
                dt.text((x, y), w["w"], font=f, fill=(*col, 255), stroke_width=7, stroke_fill=(0, 0, 0, 255))
                x += f.getlength(w["w"]) + sp
        glow = glow.filter(ImageFilter.GaussianBlur(16))
        out = Image.alpha_composite(glow, txt)
        self.cap_cache[gi] = out
        return out

    def hud(self, t):
        ep = self.ep; spec = ep.spec
        secs = int(ep.clock0 + t) % 86400
        clock = f"{secs // 3600:02d}:{secs % 3600 // 60:02d}:{secs % 60:02d}"
        hot = 0 <= t - ep.clock_hit < 4
        key = (clock, int(t * 2) % 2, hot and int(t * 4) % 2)
        if key in self.hud_cache: return self.hud_cache[key]
        im = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        x, y = 44, 30
        if key[1] == 0: d.ellipse([x, y + 12, x + 22, y + 34], fill=RED)
        part = f"PART {spec['part']}/{spec['parts']}"
        d.text((x + 36, y), part, font=self.f_hud, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
        x2 = x + 36 + self.f_hud.getlength(part) + 22
        d.text((x2, y), spec["tag"], font=self.f_hud, fill=YELLOW, stroke_width=3, stroke_fill=(0, 0, 0))
        cy = y + 52
        col = RED if (hot and key[2]) else (255, 255, 255)
        self._digits(d, 40, cy, clock, col)
        # right-hand countdown: before the event "NEXT KNOCK IN 0:18", after it "IT LEAVES IN 16:59"
        cd = spec.get("countdown")
        if cd:
            if "percent" in cd:  # meter, e.g. OXYGEN 92% dropping by `rate` per second
                label = cd["label"]; txt = f"{max(0, int(cd['percent'] - cd.get('rate', 0.2) * t))}%"
            else:
                if "start" in cd: label, rem = cd["label"], max(0, int(cd["start"] - t))
                elif t < ep.clock_hit: label, rem = cd["before"], max(0, math.ceil(ep.clock_hit - t))
                else: label, rem = cd["after"], max(0, cd["after_secs"] - int(t - ep.clock_hit))
                txt = f"{rem // 3600}:{rem % 3600 // 60:02d}:{rem % 60:02d}" if rem >= 3600 else f"{rem // 60}:{rem % 60:02d}"
            d.text((W - 44, y), label, font=self.f_hud, fill=YELLOW, anchor="ra", stroke_width=3, stroke_fill=(0, 0, 0))
            wtxt = sum((self.f_clock.getlength("0") if c.isdigit() else self.f_clock.getlength(c)) + 2 for c in txt)
            self._digits(d, W - 44 - wtxt, cy, txt, (255, 255, 255))
        self.hud_cache[key] = im
        return im

    def _digits(self, d, cx, cy, txt, col):
        adv = self.f_clock.getlength("0")
        for ch in txt:  # fixed advance so digits don't jitter
            wch = adv if ch.isdigit() else self.f_clock.getlength(ch)
            d.text((cx + (wch - self.f_clock.getlength(ch)) / 2, cy), ch, font=self.f_clock, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
            cx += wch + 2

    def choice_card(self, spec, lt, d_vo):
        """End card: question on top, two keyword pills (yellow / red), then FOLLOW FOR PART n+1 + handle."""
        c = spec["choice"]
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        def alpha(t0): return max(0.0, min(1.0, (lt - t0) / 0.2))
        def pop(t0):  # small overshoot bounce
            x = max(0.0, min(1.0, (lt - t0) / 0.25)); return 0.6 + 0.4 * x + 0.12 * math.sin(math.pi * x)
        a = alpha(0.15)
        if a > 0:
            al = int(255 * a)
            d.rectangle([0, 0, W, 820], fill=(0, 0, 0, int(150 * a)))
            fq = self.f_q; sz = 104
            while max(fq.getlength(l) for l in c["question"].split("\n")) > W - 90 and sz > 60:
                sz -= 4; fq = font(FONT_BLACK, sz)
            d.multiline_text((W / 2, 505), c["question"], font=fq, fill=(255, 255, 255, al), anchor="mm", align="center",
                             stroke_width=7, stroke_fill=(0, 0, 0, al), spacing=14)
        for word, bg, fg, cxp, t0 in ((c["a"], YELLOW, (0, 0, 0), 0.27, d_vo * c.get("a_at", 0.4)),
                                      (c["b"], RED, (255, 255, 255), 0.73, d_vo * c.get("b_at", 0.8))):
            if lt < t0: continue
            s = pop(t0); f = self.f_pill
            tw = f.getlength(word); pw, ph = (tw + 90) * s, 130 * s
            cx, cy = W * cxp, 735
            d.rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], int(24 * s), fill=(*bg, 255))
            if s > 0.9: d.text((cx, cy), word, font=f, fill=fg, anchor="mm")
        t_f = d_vo + 0.3
        if lt >= t_f:
            al = int(255 * alpha(t_f))
            d.text((W / 2, 1380), f"FOLLOW FOR PART {spec['part'] + 1}", font=self.f_choice, fill=(*YELLOW, al), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, al))
            d.text((W / 2, 1470), spec.get("handle", ""), font=self.f_handle, fill=(255, 255, 255, al), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, al))
        return im

# ---------------------------------------------------------------- frame
EP = LOOK = None

def knock_amt(t):
    return max([max(0.0, 1 - abs(t - k) / 0.14) for k in EP.knocks] + [0.0])

def render_frame(fi):
    t = fi / FPS; ep, lk = EP, LOOK
    b = ep.beat_at(t); u = (t - b["start"]) / b["dur"]
    scene = b["scene"]; sc = ep.scenes[scene]
    k = knock_amt(t)
    rng = np.random.default_rng(fi)
    shake = (rng.uniform(-14, 14) * k, rng.uniform(-14, 14) * k)
    if sc.get("fx") == "peephole":
        frame = lk.fill[scene].copy()
        frame.paste(lk.peephole(scene), (0, 0))
    else:
        cam = dict(b.get("cam", sc.get("cam", {})))
        if b.get("pulse"):  # "breathing" room: rhythmic zoom
            z = val(cam.get("zoom", 1.0), u); cam["zoom"] = z * (1 + b["pulse"] * math.sin(t * 2.6))
        frame = lk.fill[scene].copy()
        frame.paste(lk.band(scene, cam, u, shake), (0, BAND_TOP), lk.band_mask)
    ch = b.get("char")
    if ch:
        draw_character(frame, val(ch.get("x", 540), u), val(ch.get("feet", 1480), u), s=val(ch.get("s", 1.0), u), t=t,
                       view=ch.get("view", "front"), expr=ch.get("expr", "neutral"), tremble=max(val(ch.get("tremble", 0), u), k),
                       turn=val(ch.get("turn", 1.0), u), arm_raise=val(ch.get("arm", 0.0), u), walk=ch.get("walk", 0))
    a = np.asarray(frame, np.float32)
    light = 1.0
    if sc.get("flicker"): light *= 0.78 + 0.22 * (rng.random() > 0.07)
    light *= 1 - 0.3 * k
    a = a * lk.vign * light + lk.grain[fi % len(lk.grain)]
    # cut dips
    for c0 in ep.cuts:
        if 0 <= t - c0 < 0.12: a *= (t - c0) / 0.12
    if t > ep.dur - 0.5: a *= max(0, (ep.dur - t) / 0.5)
    frame = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    card = b.get("card")
    if card:
        ring = max([max(0.0, 1 - abs(((t - r) % 1.3) - 0.3) / 0.3) if 0 <= t - r < 1.3 else 0 for r in ep.rings] + [0.0])
        frame.alpha_composite(draw_card(card, t - b["start"], u, ring))
    if b.get("choice"):
        frame.alpha_composite(lk.choice_card(ep.spec, t - b["start"], len(b["clip"]) / SR))
    frame.alpha_composite(lk.hud(t), (0, 140))
    if not b.get("choice"):
        for gi, g in enumerate(ep.groups):
            if g["t"] <= t < g["end"]:
                cap = lk.caption(gi, g)
                pop = min(1, (t - g["t"]) / 0.09)
                sc_ = 0.82 + 0.18 * pop
                if sc_ < 1: cap = cap.resize((int(cap.width * sc_), int(cap.height * sc_)), Image.BILINEAR)
                frame.alpha_composite(cap, (int(W / 2 - cap.width / 2), int(1250 - cap.height / 2)))
                break
    return frame.convert("RGB").tobytes()

def draw_card(card, lt, u, ring=0.0):
    """Diegetic overlays: a handwritten rules note, an incoming phone call, or an elevator floor display."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    a = max(0.0, min(1.0, lt / 0.25)); al = int(255 * a)
    if card["type"] == "note":
        paper = Image.new("RGBA", (860, 900), (238, 230, 205, 255)); pd = ImageDraw.Draw(paper)
        for y in range(150, 900, 70): pd.line([40, y, 820, y], fill=(170, 190, 215, 255), width=2)
        pd.line([90, 0, 90, 900], fill=(220, 120, 120, 255), width=3)
        pd.text((430, 80), card.get("title", "HOUSE RULES"), font=font(FONT_BLACK, 64), fill=(30, 30, 40, 255), anchor="mm")
        f = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf", 38)
        shown = card.get("show", len(card["lines"]))
        shown = int(val(shown, u)) if isinstance(shown, (tuple, list)) else shown
        y = 120
        for i, line in enumerate(card["lines"][:shown]):
            col = (190, 20, 20, 255) if i == card.get("hl") else (35, 35, 60, 255)
            for wl in _wrap(line, f, 700):
                pd.text((115, y + 22), wl, font=f, fill=col); y += 70
        paper = paper.rotate(-3, resample=Image.BICUBIC, expand=True)
        paper.putalpha(paper.getchannel("A").point(lambda v: int(v * a)))
        im.alpha_composite(paper, ((W - paper.width) // 2, 470))
    elif card["type"] == "call":
        jx = int(math.sin(lt * 90) * 10 * ring)
        x0, y0 = 250 + jx, 430
        d.rounded_rectangle([x0, y0, x0 + 580, y0 + 1060], 70, fill=(12, 12, 18, al), outline=(70, 70, 80, al), width=8)
        d.text((x0 + 290, y0 + 170), card.get("sub", "incoming call"), font=font(FONT_XB, 40), fill=(170, 170, 180, al), anchor="mm")
        d.text((x0 + 290, y0 + 270), card["name"], font=font(FONT_BLACK, 86), fill=(255, 255, 255, al), anchor="mm")
        r = 120 + 25 * ring
        d.ellipse([x0 + 290 - r, y0 + 520 - r, x0 + 290 + r, y0 + 520 + r], outline=(255, 255, 255, int(al * (0.3 + 0.7 * ring))), width=5)
        d.ellipse([x0 + 200, y0 + 430, x0 + 380, y0 + 610], fill=(40, 40, 52, al))
        d.text((x0 + 290, y0 + 520), "?", font=font(FONT_BLACK, 110), fill=(200, 200, 210, al), anchor="mm")
        for cx, col in ((x0 + 140, RED), (x0 + 440, (40, 200, 90))):
            d.ellipse([cx - 70, y0 + 820, cx + 70, y0 + 960], fill=(*col, al))
    elif card["type"] == "display":
        d.rounded_rectangle([290, 640, 790, 960], 30, fill=(8, 6, 6, int(al * 0.92)), outline=(60, 60, 64, al), width=8)
        flick = 1.0 if (int(lt * 12) % 9) else 0.35
        txt = card["text"]
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).text((540, 800), txt, font=font(FONT_BLACK, 190), fill=(255, 40, 30, int(al * flick)), anchor="mm")
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
        d.text((540, 800), txt, font=font(FONT_BLACK, 190), fill=(255, 70, 50, int(al * flick)), anchor="mm")
    return im

def _wrap(text, f, width):
    out, cur = [], ""
    for w in text.split():
        if f.getlength((cur + " " + w).strip()) > width: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return out + [cur]

def render_chunk(args):
    i0, i1, path = args
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(i0, i1): ff.stdin.write(render_frame(fi))
    ff.stdin.close(); ff.wait()
    return path

# ---------------------------------------------------------------- audio mix
def make_audio(ep, path):
    n = int(ep.dur * SR); t = np.arange(n) / SR; rng = np.random.default_rng(3)
    out = 0.07 * np.sin(2 * np.pi * 55 * t) + 0.05 * np.sin(2 * np.pi * 55.6 * t) + 0.04 * np.sin(2 * np.pi * 82.4 * t + np.sin(t * .3))
    out += np.convolve(rng.normal(0, 1, n), np.ones(400) / 400, "same") * 0.22
    out *= np.clip(t / 2, 0, 1)
    def add(at, s):
        i = int(at * SR)
        if i >= n: return
        out[i:i + len(s)] += s[: n - i]
    def hit(freq=70, dec=18, amp=0.9, ln=0.35):
        tt = np.arange(int(ln * SR)) / SR
        return amp * (np.sin(2 * np.pi * freq * tt * (1 - tt)) + 0.5 * rng.normal(0, 1, len(tt)) * np.exp(-tt * 90)) * np.exp(-tt * dec)
    tick = 0.05 * rng.normal(0, 1, 600) * np.exp(-np.arange(600) / 60)
    first = math.ceil(ep.clock0) - ep.clock0
    for s in np.arange(first, ep.dur, 1.0): add(s, tick * (2.5 if abs(s - ep.clock_hit) < 0.5 else 1))
    for kt in ep.knocks: add(kt, hit())
    tr = np.arange(int(1.0 * SR)) / SR  # classic two-tone phone ring
    ring = 0.12 * (np.sin(2 * np.pi * 440 * tr) + np.sin(2 * np.pi * 480 * tr)) * (np.sin(2 * np.pi * 20 * tr) > 0) * np.clip((1 - tr) * 8, 0, 1)
    for rt in ep.rings: add(rt, ring)
    wl = int(0.45 * SR); w = rng.normal(0, 1, wl) * np.sin(np.linspace(0, np.pi, wl)) ** 2
    w = np.convolve(w, np.ones(30) / 30, "same") * 0.18
    for c in ep.cuts[1:]: add(c - 0.2, w)
    for b in ep.beats:
        if b.get("heartbeat"):
            for x in np.arange(b["start"], b["start"] + b["dur"], 0.75): add(x, hit(50, 22, 0.55)); add(x + 0.22, hit(45, 22, 0.4))
        if b.get("choice"):
            tt = np.arange(int(4 * SR)) / SR
            add(b["start"], sum(np.sin(2 * np.pi * f * tt) for f in (233, 246.9, 311, 466)) * 0.1 * np.exp(-tt * 0.9))
    # narration: clean and dry (no saturation), every line levelled to the same loudness
    vo = np.zeros(n)
    for b in ep.beats:
        if b["clip"] is None: continue
        c = b["clip"] / (np.sqrt(np.mean(b["clip"] ** 2)) + 1e-9) * 0.16
        if b.get("whisper"):
            c = reverb(c, 1.6, 0.3, 3)
        i = int((b["start"] + 0.05) * SR); vo[i:i + len(c)] += c[: max(0, n - i)]
    env = np.convolve(np.abs(vo), np.ones(4410) / 4410, "same")
    bed = out * 0.6 * (1 - 0.65 * np.clip(env * 8, 0, 1))
    fade = np.clip((ep.dur - t) / 0.8, 0, 1)
    st = np.stack([bed + vo, np.roll(bed, 240) + vo], 1) * fade[:, None]
    st *= 0.95 / max(1e-9, np.abs(st).max())  # peak-normalise, never clip
    with wave.open(path, "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((st * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- main
def load(ep_path):
    global EP, LOOK
    spec_mod = importlib.util.spec_from_file_location("episode", ep_path)
    m = importlib.util.module_from_spec(spec_mod); spec_mod.loader.exec_module(m)
    EP = Episode(m.EPISODE, os.path.dirname(os.path.abspath(ep_path)))
    LOOK = Look(EP)
    return EP

def main():
    ep_path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "out.mp4"
    ep = load(ep_path)
    print(f"duration {ep.dur:.1f}s, {len(ep.beats)} beats, clock hit at {ep.clock_hit:.1f}s")
    if "--preview" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
        ims = [Image.frombytes("RGB", (W, H), render_frame(int(x * FPS))).resize((270, 480)) for x in ts]
        sheet = Image.new("RGB", (270 * min(6, len(ims)), 480 * math.ceil(len(ims) / 6)))
        for i, im in enumerate(ims): sheet.paste(im, ((i % 6) * 270, (i // 6) * 480))
        sheet.save(out); print("preview", out); return
    nf = int(ep.dur * FPS); tmp = tempfile.mkdtemp()
    procs = os.cpu_count() or 2
    edges = np.linspace(0, nf, procs + 1).astype(int)
    jobs = [(edges[i], edges[i + 1], os.path.join(tmp, f"c{i}.mp4")) for i in range(procs)]
    with Pool(procs) as p: parts = p.map(render_chunk, jobs)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{x}'\n" for x in parts))
    make_audio(ep, os.path.join(tmp, "a.wav"))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(tmp, "a.wav"),
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("done", out)

if __name__ == "__main__":
    main()
