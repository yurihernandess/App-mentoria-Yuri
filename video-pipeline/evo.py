"""Acompanhamento de obra - 7 estilos diferentes (quebra de padrao).
Uso: python3 evo.py <spec.py> <saida.mp4>
spec: STYLE, PROJECT, PICKS=[(ym, path, cx)], NAME, HOOK=(big, sub), END_CFG, extras por estilo.
"""
import math, random, subprocess, sys, os, runpy, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import engine as E
from engine import fl, txt, ease, grade, GOLD, GOLD_L, NAVY, WHITE, W, H, FPS

MON = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
MONO = '/usr/share/fonts/truetype/jetbrains-mono/'
def mono(s, bold=True):
    return ImageFont.truetype(MONO + ('JetBrainsMono-ExtraBold.ttf' if bold else 'JetBrainsMono-Regular.ttf'), s)
def ml(ym, full=False):
    y, m = ym.split('-'); return f"{MON[int(m) - 1]}/{y if full else y[2:]}"

_cache = {}
def load(path):
    if path not in _cache:
        im = Image.open(f'{E.ROOT}/{E.PROJ}/{path}').convert('RGB')
        _cache[path] = grade(im, 1.06, 1.12)
    return _cache[path]

def cover(im, cx, cy, z, w=W, h=H):
    iw, ih = im.size; ar = w / h
    ch = min(ih, iw / ar) / z; cw = ch * ar
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw); y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    return im.transform((w, h), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)


class Out:
    def __init__(self, path):
        self.path = path; self.f = 0; self.ev = []
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path + '.video.mp4'], stdin=subprocess.PIPE)
    def put(self, fr):
        self.p.stdin.write(fr.convert('RGB').tobytes()); self.f += 1
    def sfx(self, kind, dt=0.0): self.ev.append((self.f / FPS + dt, kind))
    @property
    def t(self): return self.f / FPS


# ---------------- audio sintetico ----------------
SR = 48000
def synth(events, total):
    n = int(total * SR) + SR; a = np.zeros(n)
    rng = np.random.default_rng(3)
    def add(t, sig):
        i = int(t * SR); j = min(n, i + len(sig))
        if i < n: a[i:j] += sig[:j - i]
    for t, k in events:
        if k == 'tick':
            tt = np.arange(int(0.03 * SR)) / SR; add(t, 0.35 * np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 180))
        elif k == 'thump':
            tt = np.arange(int(0.25 * SR)) / SR; add(t, 0.7 * np.sin(2 * np.pi * (90 - 40 * tt / 0.25) * tt) * np.exp(-tt * 18))
        elif k == 'boom':
            tt = np.arange(int(1.2 * SR)) / SR; add(t, 0.9 * np.sin(2 * np.pi * 48 * tt) * np.exp(-tt * 3.2))
        elif k in ('whoosh', 'whoosh_s'):
            d = 0.45 if k == 'whoosh' else 0.25; m = int(d * SR); nz = rng.standard_normal(m)
            k1 = np.convolve(nz, np.ones(6) / 6, 'same'); hp = nz - np.convolve(nz, np.ones(40) / 40, 'same')
            env = np.sin(np.pi * np.linspace(0, 1, m)) ** 2
            add(t - d / 2, 0.22 * (k1 + 0.6 * hp) * env)
        elif k == 'tape':
            d = 0.12; m = int(d * SR); nz = rng.standard_normal(m); nz = nz - np.convolve(nz, np.ones(10) / 10, 'same')
            tt = np.arange(m) / SR; add(t, 0.12 * nz * (0.6 + 0.4 * np.sin(2 * np.pi * 60 * tt)))
        elif k == 'flash':
            tt = np.arange(int(0.4 * SR)) / SR; add(t, 0.35 * rng.standard_normal(len(tt)) * np.exp(-tt * 14))
    a = np.tanh(a * 1.2) * 0.8
    st = np.repeat((a * 32767).astype(np.int16)[:, None], 2, 1)
    return st


# ---------------- overlays comuns ----------------
def hook(fr, t, spec, y=None):
    big, sub = spec['HOOK']; E.CHIP = {'big': big, 'sub': sub}
    E.hook_big(fr, t)

def stamp(fr, s, a=1.0, x=80, y=1540, size=130, sub=None):
    if sub: txt(fr, (x, y - 50), sub, fl('Inter-Bold.otf', 36), GOLD_L, alpha=a, stroke=2)
    txt(fr, (x, y), s, fl('InterDisplay-Black.otf', size), WHITE, alpha=a, stroke=4)

def bug(fr): fr.alpha_composite(E.ICON, (W - 70 - E.ICON.width, 150))

def final_hold(out, spec, im, cx, dur=2.6, z0=1.0, z1=1.12, lab=None):
    n = int(dur * FPS)
    for f in range(n):
        t = f / FPS; fr = cover(im, cx, .5, z0 + (z1 - z0) * ease(f / n)).convert('RGBA')
        E.draw_label(fr, t, dur + 1, lab or spec['LABEL'][0], spec['LABEL'][1]); bug(fr); out.put(fr)

def end(out, spec):
    out.sfx('boom')
    for fr in E.end_frames_cfg(spec['END_CFG']): out.put(fr)


# ---------------- estilos ----------------
def s_morph(out, spec):
    P = spec['PICKS']; hold, xf = spec.get('HOLD', 1.35), 0.45; N = len(P)
    for i, (ym, path, cx) in enumerate(P):
        im = load(path); nxt = load(P[i + 1][1]) if i + 1 < N else None
        d = hold + (1.2 if i == 0 else 0); n = int(d * FPS); t0 = out.t; out.sfx('tick')
        if i == N - 1: break
        for f in range(n):
            t = f / FPS; p = f / n
            fr = cover(im, cx, .5, 1.0 + 0.05 * p)
            if nxt is not None and t > d - xf:
                b = cover(nxt, P[i + 1][2], .5, 1.0); fr = Image.blend(fr, b, ease((t - (d - xf)) / xf))
            fr = fr.convert('RGBA'); fr.alpha_composite(E.GRAD)
            if out.t < 2.6: hook(fr, out.t, spec)
            stamp(fr, ml(ym), sub=f'MÊS {i + 1} DE {N}')
            prog(fr, i + min(1, t / d), N); bug(fr); out.put(fr)
    ym, path, cx = P[-1]; out.sfx('thump')
    final_hold(out, spec, load(path), cx, 3.0, lab=f'{ml(ym, True)} · HOJE')

def prog(fr, v, N):
    d = ImageDraw.Draw(fr); x0, x1, y = 80, W - 80, 1730
    d.rounded_rectangle((x0, y - 4, x1, y + 4), 4, fill=(255, 255, 255, 90))
    d.rounded_rectangle((x0, y - 4, x0 + (x1 - x0) * v / N, y + 4), 4, fill=GOLD_L)
    for k in range(N + 1):
        x = x0 + (x1 - x0) * k / N; c = GOLD_L if k <= v else (200, 200, 200)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=c)


def s_slider(out, spec):
    P = spec['PICKS']; (ya, pa, ca), (yb, pb, cb) = P[0], P[-1]
    A = cover(load(pa), ca, .5, 1.05); B = cover(load(pb), cb, .5, 1.05)
    def chip(fr, s, x, y, a=1):
        if a <= 0: return
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); f = fl('InterDisplay-Black.otf', 54); tw = dl.textlength(s, font=f)
        dl.rounded_rectangle((x - tw / 2 - 26, y - 44, x + tw / 2 + 26, y + 44), 44, fill=NAVY + (int(220 * a),), outline=GOLD + (int(255 * a),), width=3)
        dl.text((x, y), s, font=f, fill=WHITE + (int(255 * a),), anchor='mm'); fr.alpha_composite(lay)
    # 1) antes
    for f in range(int(2.2 * FPS)):
        fr = A.convert('RGBA'); hook(fr, f / FPS, spec); chip(fr, 'ANTES · ' + ml(ya), W // 2, 1600, ease((f / FPS - .8) / .3)); bug(fr); out.put(fr)
    # 2) cortina antes/depois
    keys = [(0, W), (1.1, W * .5), (1.9, W * .5), (2.5, W * .15), (3.1, W * .85), (3.7, W * .5), (4.4, W * .5), (5.2, 0)]
    for t_, _ in keys[1::2]: out.sfx('whoosh', t_ - 0.3)
    n = int(keys[-1][0] * FPS)
    for f in range(n):
        t = f / FPS
        for (t0, x0), (t1, x1) in zip(keys, keys[1:]):
            if t0 <= t <= t1: x = x0 + (x1 - x0) * ease((t - t0) / max(1e-3, t1 - t0)); break
        x = int(x); fr = A.copy(); fr.paste(B.crop((x, 0, W, H)), (x, 0)); fr = fr.convert('RGBA')
        d = ImageDraw.Draw(fr); d.rectangle((x - 3, 0, x + 3, H), fill=GOLD_L)
        d.ellipse((x - 44, H // 2 - 44, x + 44, H // 2 + 44), fill=GOLD_L); d.text((x, H // 2), '◀ ▶', font=fl('Inter-Bold.otf', 30), fill=NAVY, anchor='mm')
        if x > 260: chip(fr, ml(ya), min(x / 2, W // 2), 300)
        if W - x > 260: chip(fr, ml(yb), max(x + (W - x) / 2, W // 2), 300)
        bug(fr); out.put(fr)
    # 3) mes a mes com whip
    prev = B
    for i, (ym, path, cx) in enumerate(P):
        cur = cover(load(path), cx, .5, 1.05); n = int(0.5 * FPS); out.sfx('whoosh_s')
        for f in range(n):
            if f < 4:
                sh = int((1 - f / 4) * W * 0.4); fr = Image.fromarray(np.roll(np.asarray(cur), sh, 1)); fr = E.hblur(fr.convert('RGBA'), 40 * (1 - f / 4)).convert('RGB')
            else: fr = cur
            fr = fr.convert('RGBA'); fr.alpha_composite(E.GRAD); stamp(fr, ml(ym), sub=f'MÊS {i + 1} DE {len(P)}'); bug(fr); out.put(fr)
    ym, path, cx = P[-1]; out.sfx('thump')
    final_hold(out, spec, load(path), cx, 2.4, 1.05, 1.15, lab=f'{ml(ym, True)} · HOJE')


def s_hyper(out, spec):
    P = spec['PICKS']; N = len(P); per = spec.get('PER', 0.33)
    # gancho sobre a foto mais recente
    ym, path, cx = P[-1]
    for f in range(int(2.0 * FPS)):
        fr = cover(load(path), cx, .5, 1.1 - 0.05 * f / 60).convert('RGBA'); fr.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 90))); hook(fr, f / FPS, spec); bug(fr); out.put(fr)
    out.sfx('flash'); total = N * per; f_all = int(total * FPS); last_y = None
    for i, (ym, path, cx) in enumerate(P):
        im = load(path); n = int(per * FPS); y = ym[:4]; out.sfx('tick')
        flash = last_y is not None and y != last_y; last_y = y
        if flash: out.sfx('boom')
        for f in range(n):
            g = (i * n + f) / f_all; fr = cover(im, cx, .5, 1.0 + 0.22 * g).convert('RGBA')
            if flash and f < 4: fr.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * (1 - f / 4)))))
            fr.alpha_composite(E.GRAD); fr.alpha_composite(E.GRAD_TOP)
            txt(fr, (W // 2, 330), y, fl('InterDisplay-Black.otf', 230), WHITE, 'mm', 0.95, stroke=5)
            txt(fr, (W // 2, 480), MON[int(ym[5:]) - 1], fl('InterDisplay-Black.otf', 90), GOLD_L, 'mm', 1, stroke=4)
            txt(fr, (80, 1640), f'{i + 1:02d}/{N}', mono(64), WHITE, alpha=0.9, stroke=3)
            txt(fr, (80, 1580), 'MESES DE OBRA', fl('Inter-Bold.otf', 34), GOLD_L, alpha=0.9, stroke=2)
            prog(fr, i + f / n, N); bug(fr); out.put(fr)
    out.sfx('thump'); final_hold(out, spec, load(P[-1][1]), P[-1][2], 3.0, 1.22, 1.3, lab=f'{N} MESES · {ml(P[0][0])} → {ml(P[-1][0])}')


def s_mosaic(out, spec):
    P = spec['PICKS']; N = len(P); cols, rows = spec.get('GRID', (3, 5)); tw, th = W // cols, H // rows
    tiles = [cover(load(p), cx, .5, 1.0, tw - 8, th - 8) for _, p, cx in P]
    ym, path, cx = P[-1]; big = load(path)
    bg = cover(big, cx, .5, 1.0).filter(ImageFilter.GaussianBlur(30)).convert('RGBA'); bg.alpha_composite(Image.new('RGBA', (W, H), NAVY + (200,)))
    for f in range(int(2.0 * FPS)):
        fr = cover(big, cx, .5, 1.08).convert('RGBA'); fr.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 100))); hook(fr, f / FPS, spec); bug(fr); out.put(fr)
    step = spec.get('STEP', 0.26); n = int((N * step + 1.0) * FPS)
    for k in range(N): out.sfx('tick', k * step)
    pos = [((k % cols) * tw + 4, (k // cols) * th + 4) for k in range(N)]
    for f in range(n):
        t = f / FPS; fr = bg.copy()
        for k in range(N):
            s = ease((t - k * step) / 0.22, 'back')
            if s <= 0: continue
            ti = tiles[k] if s >= 0.999 else tiles[k].resize((max(1, int((tw - 8) * s)), max(1, int((th - 8) * s))))
            x, y = pos[k]; fr.paste(ti, (x + ((tw - 8) - ti.width) // 2, y + ((th - 8) - ti.height) // 2))
            if s > 0.9:
                d = ImageDraw.Draw(fr); lab = ml(P[k][0]); f2 = fl('InterDisplay-Black.otf', 34)
                d.rounded_rectangle((x + 12, y + th - 70, x + 24 + d.textlength(lab, font=f2), y + th - 22), 10, fill=NAVY)
                d.text((x + 18, y + th - 46), lab, font=f2, fill=GOLD_L, anchor='lm')
        out.put(fr)
    # zoom do ultimo tile para tela cheia
    out.sfx('whoosh'); x, y = pos[-1]; n = int(0.8 * FPS); full = cover(big, cx, .5, 1.0)
    for f in range(n):
        p = ease(f / n); fr = bg.copy() if p < 1 else None
        x0, y0 = x * (1 - p), y * (1 - p); w_ = (tw - 8) + (W - tw + 8) * p; h_ = (th - 8) + (H - th + 8) * p
        fr = fr if fr else Image.new('RGBA', (W, H))
        fr.paste(cover(big, cx, .5, 1.0, int(w_), int(h_)), (int(x0), int(y0))); out.put(fr)
    out.sfx('thump'); final_hold(out, spec, big, cx, 2.8, 1.0, 1.1, lab=f'{ml(ym, True)} · HOJE')


def s_polaroid(out, spec):
    P = spec['PICKS']; N = len(P); rnd = random.Random(7)
    ym, path, cx = P[-1]; big = load(path)
    bg = cover(big, cx, .5, 1.15).filter(ImageFilter.GaussianBlur(25)).convert('RGBA'); bg.alpha_composite(Image.new('RGBA', (W, H), NAVY + (170,)))
    PW, PH, PB = 780, 930, 32
    cards = []
    for i, (ym, p, c) in enumerate(P):
        card = Image.new('RGBA', (PW, PH), (250, 248, 242, 255)); card.paste(cover(load(p), c, .5, 1.0, PW - 2 * PB, PW - 2 * PB), (PB, PB))
        d = ImageDraw.Draw(card); d.text((PB + 6, PW + 10), ml(ym, True).lower(), font=fl('InterDisplay-BlackItalic.otf', 64), fill=(40, 45, 60))
        d.text((PW - PB - 6, PW + 34), spec['NAME'].lower(), font=fl('Inter-SemiBoldItalic.otf', 30), fill=(120, 120, 130), anchor='ra')
        ang = rnd.uniform(-9, 9) if i < N - 1 else 0
        sh = Image.new('RGBA', (PW + 60, PH + 60), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((30, 40, PW + 30, PH + 40), fill=(0, 0, 0, 120)); sh = sh.filter(ImageFilter.GaussianBlur(14))
        sh.alpha_composite(card, (30, 30)); rc = sh.rotate(ang, Image.BICUBIC, expand=True)
        cards.append((rc, (W // 2 + rnd.randint(-50, 50) if i < N - 1 else W // 2, 900 + rnd.randint(-60, 60) if i < N - 1 else 900)))
    step = spec.get('STEP', 0.7); n = int((N * step + 0.8) * FPS)
    for k in range(N): out.sfx('thump', k * step + 0.32)
    for f in range(n):
        t = f / FPS; fr = bg.copy()
        for k, (rc, (cx_, cy_)) in enumerate(cards):
            p = (t - k * step) / 0.38
            if p <= 0: continue
            e = ease(p, 'out'); y = cy_ - (1 - e) * 1700; s = 1 + 0.25 * (1 - e)
            im = rc if s == 1 else rc.resize((int(rc.width * s), int(rc.height * s)))
            fr.alpha_composite(im, (int(cx_ - im.width / 2), int(y - im.height / 2)))
        if t < 2.6: hook(fr, t, spec)
        bug(fr); out.put(fr)
    # ultimo polaroid vira tela cheia
    out.sfx('whoosh'); n = int(0.7 * FPS); rc, (cx_, cy_) = cards[-1]
    for f in range(n):
        p = ease(f / n); fr = bg.copy()
        ph = cover(big, cx, .5, 1.0, int((PW - 2 * PB) + (W - PW + 2 * PB) * p), int((PW - 2 * PB) + (H - PW + 2 * PB) * p))
        x0 = (W - ph.width) // 2; y0 = int((cy_ - PH / 2 + PB) * (1 - p))
        fr.alpha_composite(rc, (int(cx_ - rc.width / 2), int(cy_ - rc.height / 2))); fr.paste(ph, (x0, y0)); out.put(fr)
    out.sfx('thump'); final_hold(out, spec, big, cx, 2.8, 1.0, 1.1, lab=f'{ml(ym, True)} · HOJE')


def s_triptych(out, spec):
    P = spec['TRI']; pw = (W - 16) // 3; panels = [(load(p), c, ym, tag) for ym, p, c, tag in P]
    n = int(5.2 * FPS)
    for k in range(3): out.sfx('whoosh_s', 0.3 + k * 0.3)
    for f in range(n):
        t = f / FPS; fr = Image.new('RGBA', (W, H), GOLD + (255,))
        for k, (im, c, ym, tag) in enumerate(panels):
            p = ease((t - 0.3 - k * 0.3) / 0.5, 'out')
            if p <= 0: continue
            pan = cover(im, c, .5, 1.12 - 0.08 * min(1, t / 5), pw, H).convert('RGBA')
            pan.alpha_composite(E.GRAD.crop((0, 0, pw, H)))
            d = ImageDraw.Draw(pan)
            d.text((pw // 2, 1560), tag, font=fl('Inter-ExtraBold.otf', 34), fill=GOLD_L, anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
            d.text((pw // 2, 1640), ml(ym), font=fl('InterDisplay-Black.otf', 82), fill=WHITE, anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0))
            off = int((1 - p) * H) * (1 if k % 2 == 0 else -1)
            fr.alpha_composite(pan, (k * (pw + 8), off))
        if t < 2.8: hook(fr, t, spec)
        bug(fr); out.put(fr)
    # painel de hoje expande
    out.sfx('whoosh'); im, c, ym, tag = panels[-1]; n = int(0.7 * FPS)
    for f in range(n):
        p = ease(f / n); w_ = int(pw + (W - pw) * p); x0 = int(2 * (pw + 8) * (1 - p))
        fr = Image.new('RGBA', (W, H), GOLD + (255,))
        for k in range(2):
            pan = cover(panels[k][0], panels[k][1], .5, 1.04, pw, H); fr.paste(pan, (int(k * (pw + 8) - p * W * 0.6), 0))
        fr.paste(cover(im, c, .5, 1.04, w_, H), (x0, 0)); out.put(fr)
    out.sfx('thump'); final_hold(out, spec, im, c, 2.4, 1.0, 1.1, lab=f'{ml(ym, True)} · HOJE')
    for (ym2, p2, c2) in spec.get('EXTRA', []):
        out.sfx('whoosh_s'); n = int(1.8 * FPS)
        for f in range(n):
            fr = cover(load(p2), c2, .5, 1.12 - 0.1 * f / n).convert('RGBA'); fr.alpha_composite(E.GRAD); bug(fr); out.put(fr)


def vhs(fr, t, k=1.0):
    a = np.asarray(fr.convert('RGB')).copy()
    sh = int(6 * k); a[:, :, 0] = np.roll(a[:, :, 0], sh, 1); a[:, :, 2] = np.roll(a[:, :, 2], -sh, 1)
    a[::4] = (a[::4] * 0.78).astype(np.uint8)
    rng = np.random.default_rng(int(t * 1000))
    for _ in range(int(3 * k)):
        y = rng.integers(0, H - 40); h = rng.integers(6, 30); a[y:y + h] = np.roll(a[y:y + h], rng.integers(-60, 60), 1)
    return Image.fromarray(a).convert('RGBA')

def s_rewind(out, spec):
    P = spec['PICKS']; N = len(P); ym, path, cx = P[-1]
    org = (255, 170, 60)
    def osd(fr, s, date, a=1):
        txt(fr, (70, 190), s, mono(60), WHITE, alpha=a, stroke=3)
        txt(fr, (W - 70, 1700), date, mono(64), org, 'ra', a, stroke=3)
    for f in range(int(2.4 * FPS)):
        fr = cover(load(path), cx, .5, 1.05 + 0.05 * f / 72).convert('RGBA'); fr.alpha_composite(E.GRAD); hook(fr, f / FPS, spec)
        txt(fr, (70, 190), '▶ PLAY', mono(60), WHITE, alpha=ease(f / 10), stroke=3); bug(fr); out.put(fr)
    per = spec.get('PER_REW', 0.13)
    for i in range(N - 1, -1, -1):
        ym_, p, c = P[i]; out.sfx('tape')
        for f in range(max(2, int(per * FPS))):
            fr = vhs(cover(load(p), c, .5, 1.05), out.t, 1.6); osd(fr, '◀◀ REW', ml(ym_, True).replace('/', ' ')); out.put(fr)
    out.sfx('thump'); ym0, p0, c0 = P[0]
    for f in range(int(1.8 * FPS)):
        t = f / FPS; fr = vhs(cover(load(p0), c0, .5, 1.05 + 0.04 * t), out.t, 0.5)
        osd(fr, '❚❚ PAUSE', ml(ym0, True).replace('/', ' '), 1 if (f // 12) % 2 == 0 else 0.35)
        txt(fr, (W // 2, 900), 'ASSIM COMEÇOU', fl('InterDisplay-Black.otf', 96), WHITE, 'mm', ease(t / .3), stroke=5); out.put(fr)
    per = spec.get('PER_FF', 0.11)
    for i in range(N):
        ym_, p, c = P[i]; out.sfx('tape')
        for f in range(max(2, int(per * FPS))):
            fr = vhs(cover(load(p), c, .5, 1.05), out.t, 1.0); osd(fr, '▶▶ FF', ml(ym_, True).replace('/', ' ')); out.put(fr)
    out.sfx('flash')
    final_hold(out, spec, load(path), cx, 2.8, 1.05, 1.15, lab=f'{ml(P[0][0])} → {ml(ym)} · {N} REGISTROS')


STYLES = dict(morph=s_morph, slider=s_slider, hyper=s_hyper, mosaic=s_mosaic, polaroid=s_polaroid, triptych=s_triptych, rewind=s_rewind)

def main(spec_path, outp):
    spec = runpy.run_path(spec_path); E.PROJ = spec['PROJECT']
    out = Out(outp); STYLES[spec['STYLE']](out, spec); end(out, spec)
    out.p.stdin.close(); out.p.wait(); total = out.f / FPS
    st = synth(out.ev, total)
    with wave.open(outp + '.wav', 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', outp + '.video.mp4', '-i', outp + '.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-af', 'loudnorm=I=-18:TP=-2', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', outp], check=True)
    os.remove(outp + '.video.mp4'); os.remove(outp + '.wav'); print('total', round(total, 2))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
