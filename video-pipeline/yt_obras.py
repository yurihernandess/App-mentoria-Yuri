"""Resumao de obras 16:9 (YouTube). Uso: python3 yt_obras.py <spec.py> <saida.mp4>"""
import sys, os, runpy, subprocess, wave, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import engine as E
from engine import fl, txt, ease, grade, GOLD, GOLD_L, NAVY, WHITE
import yt as Y
from evo import cover, ml, mono, synth, SR, MON

W, H, FPS = 1920, 1080, 30
ICON = E.ICON
_c = {}
def load(p):
    if p not in _c: _c[p] = grade(Image.open(f'{E.ROOT}/{E.PROJ}/{p}').convert('RGB'), 1.06, 1.12)
    return _c[p]

class Out:
    def __init__(self, path):
        self.f = 0; self.ev = []; self.chap = []
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path + '.video.mp4'], stdin=subprocess.PIPE)
    def put(self, fr): self.p.stdin.write(fr.convert('RGB').tobytes()); self.f += 1
    def sfx(self, k, dt=0): self.ev.append((self.f / FPS + dt, k))
    @property
    def t(self): return self.f / FPS

_g = np.clip((np.arange(H) - H * 0.55) / (H * 0.45), 0, 1) ** 1.4 * 190
GRAD = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), np.repeat(_g[:, None], W, 1).astype(np.uint8)]), 'RGBA')
_t = np.clip(1 - np.arange(H) / (H * 0.18), 0, 1) ** 1.5 * 140
GTOP = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), np.repeat(_t[:, None], W, 1).astype(np.uint8)]), 'RGBA')

def chrome(fr, spec):
    fr.alpha_composite(GTOP)
    txt(fr, (60, 52), spec['BUG'], fl('Inter-Bold.otf', 26), GOLD_L, 'lm', 0.95, shadow=False)
    fr.alpha_composite(ICON, (W - 60 - ICON.width, 14))

def lower(fr, t, title, sub, badge=None):
    a = ease(t / 0.35); dy = int((1 - a) * 30)
    fr.alpha_composite(GRAD)
    if badge:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); f = fl('InterDisplay-Black.otf', 34); tw = dl.textlength(badge, font=f)
        dl.rounded_rectangle((80, 790 + dy, 80 + tw + 50, 846 + dy), 28, fill=GOLD + (int(255 * a),)); dl.text((105, 818 + dy), badge, font=f, fill=NAVY + (int(255 * a),), anchor='lm'); fr.alpha_composite(lay)
    txt(fr, (80, 870 + dy), title, fl('InterDisplay-Black.otf', 84), WHITE, 'la', a, stroke=3)
    txt(fr, (82, 975 + dy), sub, fl('Inter-SemiBold.otf', 34), GOLD_L, 'la', a, stroke=2)


def intro(out, spec):
    im = load(spec['INTRO_BG']); n = int(5.0 * FPS); out.sfx('boom', 0.2)
    for f in range(n):
        t = f / FPS; fr = cover(im, .5, .5, 1.15 - 0.1 * f / n, W, H).convert('RGBA')
        fr.alpha_composite(Image.new('RGBA', (W, H), NAVY + (int(150 * ease(t / .6)),)))
        a = lambda d: ease((t - d) / .4); dy = lambda d: int((1 - a(d)) * 40)
        txt(fr, (W // 2, 330 + dy(.2)), 'ACOMPANHAMENTO DE OBRA', fl('Inter-Bold.otf', 40), GOLD_L, 'mm', a(.2), shadow=False)
        s = ease((t - .4) / .5, 'back')
        if t > .4: txt(fr, (W // 2, 470), 'OBRAS ROGGA', fl('InterDisplay-Black.otf', int(150 * (0.8 + 0.2 * s))), WHITE, 'mm', min(1, (t - .4) / .2), stroke=4)
        if t > .6: txt(fr, (W // 2, 620), 'EM JOINVILLE', fl('InterDisplay-Black.otf', int(150 * (0.8 + 0.2 * ease((t - .6) / .5, 'back')))), GOLD_L, 'mm', min(1, (t - .6) / .2), stroke=4)
        txt(fr, (W // 2, 770 + dy(1.1)), spec['INTRO_SUB'], fl('Inter-SemiBold.otf', 40), WHITE, 'mm', a(1.1), shadow=False)
        fr.alpha_composite(ICON, (W - 60 - ICON.width, 14))
        if f > n - 8: fr = Image.blend(fr.convert('RGB'), Image.new('RGB', (W, H)), (f - (n - 8)) / 8).convert('RGBA')
        out.put(fr)


def fitimg(im, z, cx=.5):
    if im.width / im.height > 1.3: return cover(im, cx, .5, z, W, H).convert('RGBA')
    bg = cover(im, .5, .5, 1.2, W, H).filter(ImageFilter.GaussianBlur(28)).convert('RGBA'); bg.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 90)))
    h = int(H * 0.96 * z); w = int(im.width * h / im.height); fg = im.resize((w, h), Image.BILINEAR)
    bg.paste(fg, ((W - w) // 2, (H - h) // 2)); return bg

def tag(fr, s, a=1.0):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); f = fl('Inter-ExtraBold.otf', 30); tw = dl.textlength(s, font=f)
    dl.rounded_rectangle((60, 96, 60 + tw + 44, 150), 27, fill=NAVY + (int(220 * a),), outline=GOLD + (int(255 * a),), width=2)
    dl.text((82, 123), s, font=f, fill=GOLD_L + (int(255 * a),), anchor='lm'); fr.alpha_composite(lay)

_lg = {}
def logo(path):
    if path not in _lg:
        im = Image.open(f'{E.ROOT}/{E.PROJ}/{path}').convert('RGBA'); im.thumbnail((560, 300))
        a = im.getchannel('A'); transparent = a.getextrema()[0] < 250
        card = Image.new('RGBA', (im.width + 80, im.height + 60), (255, 255, 255, 255) if transparent else im.getpixel((2, 2))[:3] + (255,))
        card.alpha_composite(im, (40, 30)); m = Image.new('L', card.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0) + card.size, 24, fill=255); card.putalpha(m)
        _lg[path] = card
    return _lg[path]

def chapter(out, spec, i, c):
    out.chap.append((out.t, c['name'])); P = c['picks']; last = load(P[-1][1])
    bg = cover(last, .5, .5, 1.1, W, H).filter(ImageFilter.GaussianBlur(18)).convert('RGBA')
    n = int(2.6 * FPS); out.sfx('whoosh', 0.1)
    for f in range(n):
        t = f / FPS; fr = bg.copy(); fr.alpha_composite(Image.new('RGBA', (W, H), NAVY + (200,)))
        a = lambda d: ease((t - d) / .35); dx = lambda d: int((1 - a(d)) * -60)
        txt(fr, (160 + dx(0), 300), f'{i:02d}', fl('InterDisplay-Black.otf', 260), GOLD, 'la', a(0), shadow=False)
        txt(fr, (170 + dx(.15), 600), c['name'].upper(), fl('InterDisplay-Black.otf', 120), WHITE, 'la', a(.15))
        txt(fr, (174 + dx(.3), 750), c['sub'], fl('Inter-SemiBold.otf', 44), GOLD_L, 'la', a(.3), shadow=False)
        if c.get('badge'):
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); fb = fl('InterDisplay-Black.otf', 44); tw = dl.textlength(c['badge'], font=fb); aa = a(.45)
            dl.rounded_rectangle((174, 830, 174 + tw + 70, 906), 38, fill=GOLD + (int(255 * aa),)); dl.text((209, 868), c['badge'], font=fb, fill=NAVY + (int(255 * aa),), anchor='lm'); fr.alpha_composite(lay)
        if c.get('logo'):
            lg = logo(c['logo']); la = a(.5)
            if la > 0:
                l2 = lg.copy(); l2.putalpha(Image.eval(l2.getchannel('A'), lambda v: int(v * la))); fr.alpha_composite(l2, (W - 120 - lg.width, 140 + int((1 - la) * 30)))
        if f > n - 6: fr = Image.blend(fr.convert('RGB'), Image.new('RGB', (W, H)), (f - (n - 6)) / 6).convert('RGBA')
        out.put(fr)
    # o projeto (renders)
    for q, p in enumerate(c.get('renders', [])):
        im = load(p); m = int(2.3 * FPS); out.sfx('whoosh_s')
        for f in range(m):
            e = ease(f / m); z = (1.0 + 0.1 * e) if q % 2 == 0 else (1.1 - 0.1 * e)
            fr = fitimg(im, z if im.width / im.height > 1.3 else 0.97 + 0.03 * e)
            if f < 5: fr = Image.blend(Image.new('RGB', (W, H)), fr.convert('RGB'), f / 5).convert('RGBA')
            chrome(fr, spec); tag(fr, 'O PROJETO')
            txt(fr, (W - 60, H - 40), 'Imagem ilustrativa', fl('Inter-Medium.otf', 24), (235, 235, 235), 'rm', 0.9)
            out.put(fr)
    # timelapse
    N = len(P); per = c.get('per', max(0.26, min(0.55, 8.0 / N))); tot = int(N * per * FPS); k = 0; last_y = None
    for j, (ym, p) in enumerate(P):
        im = load(p); m = int(per * FPS); out.sfx('tick')
        fl_ = last_y is not None and ym[:4] != last_y; last_y = ym[:4]
        if fl_: out.sfx('flash')
        for f in range(m):
            g = k / max(1, tot); k += 1
            fr = cover(im, .5, .5, 1.0 + 0.15 * g, W, H).convert('RGBA')
            if fl_ and f < 3: fr.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - f / 3)))))
            fr.alpha_composite(GRAD); chrome(fr, spec); tag(fr, 'A OBRA · MÊS A MÊS')
            txt(fr, (80, 900), ml(ym, True), fl('InterDisplay-Black.otf', 110), WHITE, 'la', 1, stroke=4)
            txt(fr, (84, 860), f"{c['name'].upper()}  ·  {j + 1:02d}/{N}", fl('Inter-Bold.otf', 32), GOLD_L, 'la', 1, stroke=2)
            d = ImageDraw.Draw(fr); x0, x1, y = 80, W - 80, 1040; v = (j + f / m) / N
            d.rounded_rectangle((x0, y - 3, x1, y + 3), 3, fill=(255, 255, 255, 80)); d.rounded_rectangle((x0, y - 3, x0 + (x1 - x0) * v, y + 3), 3, fill=GOLD_L)
            out.put(fr)
    # fotos atuais
    out.sfx('thump')
    for q, p in enumerate(c['now']):
        im = load(p); m = int(2.8 * FPS); a0, a1 = [(0.45, 1.12, 0.55, 1.0), (0.5, 1.0, 0.5, 1.12), (0.55, 1.1, 0.45, 1.02)][q % 3][:2], [(0.45, 1.12, 0.55, 1.0), (0.5, 1.0, 0.5, 1.12), (0.55, 1.1, 0.45, 1.02)][q % 3][2:]
        if q: out.sfx('whoosh_s')
        for f in range(m):
            e = ease(f / m); fr = cover(im, a0[0] + (a1[0] - a0[0]) * e, .5, a0[1] + (a1[1] - a0[1]) * e, W, H).convert('RGBA')
            if q == 0 and f < 6: fr = Image.blend(Image.new('RGB', (W, H), (255, 255, 255)), fr.convert('RGB'), f / 6).convert('RGBA')
            chrome(fr, spec); tag(fr, c.get('now_tag', 'HOJE'))
            if q == 0: lower(fr, f / FPS, c['name'].upper(), c['now_sub'], c.get('badge'))
            else:
                fr.alpha_composite(GRAD); txt(fr, (80, 960), c['now_sub'], fl('Inter-Bold.otf', 36), WHITE, 'la', 1, stroke=2)
            out.put(fr)


def main(spec_path, outp):
    spec = runpy.run_path(spec_path); E.PROJ = spec['PROJECT']
    out = Out(outp); intro(out, spec)
    for i, c in enumerate(spec['CHAPTERS'], 1): chapter(out, spec, i, c)
    out.chap.append((out.t, 'Fale com a Hernandes')); out.sfx('boom')
    for fr in Y.end_frames(spec['END'], 8.0): out.put(fr)
    out.p.stdin.close(); out.p.wait(); total = out.f / FPS
    st = synth(out.ev, total)
    with wave.open(outp + '.wav', 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', outp + '.video.mp4', '-i', outp + '.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-af', 'loudnorm=I=-18:TP=-2', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', outp], check=True)
    os.remove(outp + '.video.mp4'); os.remove(outp + '.wav')
    for t, n in out.chap: print('CHAP', '%d:%02d' % divmod(int(t), 60), n)
    print('total', round(total, 2))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
