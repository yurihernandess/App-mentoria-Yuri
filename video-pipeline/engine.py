"""Motor de edicao de Reels imobiliario (Hernandes).
Uso: python3 engine.py <spec.py> <saida.mp4>
O spec define TIMELINE (lista de itens), HOOK (nome) e END (variante).
"""
import json, math, subprocess, sys, os, runpy
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
F = '/usr/share/fonts/opentype/inter/'
_fc = {}
def fl(n, s):
    k = (n, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(F + n, s)
    return _fc[k]
GOLD = (179, 144, 88); GOLD_L = (222, 190, 130); NAVY = (9, 26, 54); WHITE = (255, 255, 255)
BRAND = json.load(open(f'{ROOT}/brand/brand.json'))
LOGO = Image.open(f'{ROOT}/brand/logo_full_dark.png'); LOGO.thumbnail((520, 390), Image.LANCZOS)
ICON = Image.open(f'{ROOT}/brand/logo_icon_dark.png'); ICON.thumbnail((74, 84), Image.LANCZOS)
_g = np.clip((np.arange(H) - H * 0.48) / (H * 0.52), 0, 1) ** 1.5 * 170
GRAD = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), np.repeat(_g[:, None], W, 1).astype(np.uint8)]), 'RGBA')
_t = np.clip(1 - np.arange(H) / (H * 0.22), 0, 1) ** 1.6 * 120
GRAD_TOP = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), np.repeat(_t[:, None], W, 1).astype(np.uint8)]), 'RGBA')

FIX = {'CARREIRO': 'CARRERO', 'SACADO': 'SACADA', 'PRAIA.': 'PRAIA', 'COSTES': 'COSTA', 'SWITCH': 'SUÍTE', 'ESTÚDIO': 'STUDIO', 'MANTENCE': 'MANTÉM'}
EMPH = {'RENTABILIZAR', 'APROVEITAR', 'USUFRUIR', 'VERÃO', 'PRAIA', 'CARRERO', 'AIRBNB', 'PRONTO', 'PENHA',
        'CHURRASQUEIRA', 'INTEGRADO', 'DORMITÓRIOS', 'MAR', 'FAMÍLIA', 'LANAI', 'PIÇARRAS', '120', 'VEZES', 'FRENTE',
        'SUÍTE', 'CONSTRUTORA', 'LITORAL', 'BALNEÁRIO', 'COMPLETO', 'PERSONALIZADO', 'DECORADO'}
TRANS = {}
import glob as _glob
for p in _glob.glob(f'{ROOT}/*/transcript*.json'):
    TRANS.update(json.load(open(p)))
PROJ = 'verdemar'


def ease(t, k='io'):
    t = min(1, max(0, t))
    if k == 'out': return 1 - (1 - t) ** 3
    if k == 'back':
        c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
    return 0.5 - 0.5 * math.cos(math.pi * t)


def crop_zoom(im, cx, cy, z):
    iw, ih = im.size
    ch = min(ih, iw * 16 / 9) / z; cw = ch * 9 / 16
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw); y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    return im.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)


def grade(im, c=1.06, s=1.10):
    return ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(c)).enhance(s)


def txt(base, xy, s, font, fill, anchor='la', alpha=1.0, spacing=4, shadow=True, stroke=0):
    if alpha <= 0.01: return
    lay = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if shadow:
        d.multiline_text((xy[0] + 3, xy[1] + 5), s, font=font, fill=(0, 0, 0, int(150 * alpha)), anchor=anchor, spacing=spacing, stroke_width=stroke)
        lay = lay.filter(ImageFilter.GaussianBlur(8)); d = ImageDraw.Draw(lay)
    d.multiline_text(xy, s, font=font, fill=tuple(fill) + (int(255 * alpha),), anchor=anchor, spacing=spacing,
                     stroke_width=stroke, stroke_fill=(0, 0, 0, int(210 * alpha)))
    base.alpha_composite(lay)


class Reader:
    def __init__(self, path, start, kind):
        self.w, self.h = (2160, 3840) if kind == '4k' else (1080, 1920)
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{start:.3f}', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.i, self.cur = -1, None

    def get(self, idx):
        n = self.w * self.h * 3
        while self.i < idx:
            buf = self.p.stdout.read(n)
            if len(buf) < n: break
            self.cur = buf; self.i += 1
        return Image.frombytes('RGB', (self.w, self.h), self.cur)

    def close(self):
        try: self.p.kill()
        except Exception: pass


def interp_frame(keys, t):
    """keys: [(t, cx, cy, z), ...] -> enquadramento suavizado no tempo t."""
    if t <= keys[0][0]: return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            p = ease((t - t0) / max(1e-6, t1 - t0))
            return tuple(a[i] + (b[i] - a[i]) * p for i in range(3))
    return keys[-1][1:]


# ---------------- legendas ----------------
def make_groups(key, t_from, t_to):
    ws = []
    for a, b, w in TRANS[key]['words']:
        if a >= t_from - 0.05 and a < t_to:
            u = w.upper()
            clean = u.strip('.,!?')
            clean = FIX.get(clean, clean)
            ws.append([a, b, clean, u[-1] in '.,!?'])
    groups, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) == 3 or w[3] or w[2] in EMPH:
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups


def draw_captions(fr, groups, t_orig, y=None):
    y = STYLE['cap_y'] if y is None else y
    maxw = STYLE['cap_maxw']
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0][0] if gi + 1 < len(groups) else g[-1][1] + 0.35
        if g[0][0] - 0.05 <= t_orig < g_end:
            words = [w[2] for w in g]
            fs = 84; fc = fl('InterDisplay-Black.otf', fs)
            d = ImageDraw.Draw(fr)
            widths = [d.textlength(w, font=fc) for w in words]; sp = 24
            total = sum(widths) + sp * (len(words) - 1)
            if total > maxw:
                fs = int(fs * maxw / total); fc = fl('InterDisplay-Black.otf', fs)
                widths = [d.textlength(w, font=fc) for w in words]; sp = 20; total = sum(widths) + sp * (len(words) - 1)
            x = (W - total) / 2
            pop = ease((t_orig - g[0][0] + 0.05) / 0.12, 'out')
            if STYLE['cap'] == 'box':
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
                dl.rounded_rectangle((x - 30, y - 22, x + total + 30, y + fs + 26), 22, fill=NAVY + (int(225 * pop),))
                fr.alpha_composite(lay)
                for (a, b, w, _), ww in zip(g, widths):
                    active = t_orig >= a - 0.03
                    col = GOLD_L if (active and w in EMPH) else WHITE
                    txt(fr, (x, y), w, fc, col, alpha=(1 if active else 0.45) * pop, shadow=False)
                    x += ww + sp
                return
            for (a, b, w, _), ww in zip(g, widths):
                active = t_orig >= a - 0.03
                col = GOLD_L if active and (w in EMPH or t_orig < b + 0.12) else WHITE
                txt(fr, (x, y + (1 - pop) * 28), w, fc, col, alpha=(1 if active else 0.5) * pop, stroke=5)
                x += ww + sp
            return


def draw_label(fr, t, dur, lab, title):
    fr.alpha_composite(GRAD)
    a_in = ease((t - 0.08) / 0.28); a = a_in * min(1, max(0, (dur - t) / 0.15))
    dy = int((1 - a_in) * 50)
    ly = STYLE['label_y']
    if lab: txt(fr, (80, ly - 55 + dy), ' '.join(lab), fl('Inter-SemiBold.otf', 32), GOLD_L, alpha=a)
    longest = max(len(x) for x in title.split('\n'))
    txt(fr, (80, ly + dy), title, fl('InterDisplay-Black.otf', 100 if longest < 13 else 80), WHITE, alpha=a)


def brand_bug(fr):
    fr.alpha_composite(ICON, (W - 70 - ICON.width, 150))
    if STYLE.get('tag'):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        f1 = fl('Inter-Bold.otf', 26); f2 = fl('Inter-Medium.otf', 20)
        t1, t2 = STYLE['tag']; w1 = max(dl.textlength(t1, font=f1), dl.textlength(t2, font=f2))
        dl.rounded_rectangle((60, 150, 60 + w1 + 40, 150 + 78), 14, fill=(0, 0, 0, 150))
        dl.text((80, 162), t1, font=f1, fill=GOLD_L + (255,)); dl.text((80, 196), t2, font=f2, fill=(235, 235, 235, 255))
        fr.alpha_composite(lay)


# ---------------- ganchos ----------------
def hook_black(fr, t):
    fr.alpha_composite(GRAD_TOP)
    d = ImageDraw.Draw(fr)
    a = ease(t / 0.25)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    bw = 520; bx = (W - bw) // 2; by = 250 - int((1 - a) * 40)
    dl.rectangle((bx, by, bx + bw, by + 96), fill=(0, 0, 0, int(235 * a)))
    dl.rectangle((bx, by, bx + bw, by + 96), outline=GOLD + (int(255 * a),), width=3)
    dl.text((W // 2, by + 48), 'BLACK FRIDAY', font=fl('InterDisplay-Black.otf', 58), fill=GOLD_L + (int(255 * a),), anchor='mm')
    fr.alpha_composite(lay)
    # preco antigo riscado
    a2 = ease((t - 0.25) / 0.25)
    txt(fr, (W // 2, 470), 'DE R$ 550 MIL', fl('InterDisplay-ExtraBold.otf', 70), (235, 235, 235), 'mm', a2, stroke=3)
    sp = ease((t - 0.55) / 0.25)
    if sp > 0:
        x0 = W // 2 - 250; d.line((x0, 472, x0 + 500 * sp, 466), fill=(230, 50, 50), width=9)
    # preco novo com impacto
    s = ease((t - 0.85) / 0.3, 'back')
    if t > 0.85:
        f = fl('InterDisplay-Black.otf', max(20, int(112 * (0.6 + 0.4 * s))))
        txt(fr, (W // 2, 640), 'POR R$ 530 MIL', f, WHITE, 'mm', min(1, (t - 0.85) / 0.15), stroke=4)
    a3 = ease((t - 1.3) / 0.3)
    txt(fr, (W // 2, 770), 'APÊ PRONTO EM PENHA/SC', fl('Inter-Bold.otf', 40), GOLD_L, 'mm', a3, stroke=2)


def hook_verao(fr, t):
    fr.alpha_composite(GRAD_TOP)
    a = ease(t / 0.3); s = ease(t / 0.45, 'back')
    f = fl('InterDisplay-Black.otf', int(128 * (0.75 + 0.25 * s)))
    txt(fr, (W // 2, 420), 'PRONTO PRA\nESTE VERÃO', f, WHITE, 'mm', a, spacing=0, stroke=4)
    a2 = ease((t - 0.5) / 0.3)
    txt(fr, (W // 2, 620), 'PERTO DA PRAIA  ·  PENHA/SC', fl('Inter-Bold.otf', 40), GOLD_L, 'mm', a2, stroke=2)


def hook_chip(fr, t):
    a = ease(t / 0.3) * min(1, max(0, (3.2 - t) / 0.3))
    if a <= 0: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    s = CHIP['text']
    f = fl('Inter-ExtraBold.otf', 38); tw = dl.textlength(s, font=f)
    x0 = (W - tw) / 2 - 34; y0 = 230
    dl.rounded_rectangle((x0, y0, x0 + tw + 68, y0 + 84), 42, fill=GOLD + (int(240 * a),))
    dl.text((W / 2, y0 + 42), s, font=f, fill=NAVY + (int(255 * a),), anchor='mm')
    fr.alpha_composite(lay)


CHIP = {'text': 'APÊ PRONTO PERTO DA PRAIA'}
STYLE = {'look': 'cine', 'cap': 'karaoke', 'cap_y': 1300, 'cap_maxw': W - 140, 'label_y': 1450, 'tag': None}


def hook_big(fr, t):
    """Gancho generico: linha grande + linha de apoio (CHIP['big'], CHIP['sub'])."""
    fr.alpha_composite(GRAD_TOP)
    a = ease(t / 0.25); s = ease(t / 0.45, 'back')
    big = CHIP['big']; longest = max(len(x) for x in big.split('\n'))
    base = 150 if longest <= 6 else (120 if longest <= 11 else 96)
    f = fl('InterDisplay-Black.otf', int(base * (0.75 + 0.25 * s)))
    txt(fr, (W // 2, 400), big, f, WHITE, 'mm', a, spacing=0, stroke=4)
    a2 = ease((t - 0.45) / 0.3)
    txt(fr, (W // 2, 400 + int(base * 0.62 * (big.count('\n') + 1)) + 30), CHIP.get('sub', ''), fl('Inter-Bold.otf', 40), GOLD_L, 'mm', a2, stroke=2)


HOOKS = {'black': hook_black, 'verao': hook_verao, 'chip': hook_chip, 'big': hook_big}


# ---------------- cartela ----------------
def end_frames(variant, cfg=None, dur=4.8):
    if cfg:
        yield from end_frames_cfg(cfg, dur); return
    im = Image.open(f'{ROOT}/verdemar/jpg/IMG_5088.jpg').convert('RGB'); s = 2700 / max(im.size)
    im = grade(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS))
    n = int(dur * FPS)
    for f in range(n):
        t = f / FPS
        fr = crop_zoom(im, 0.5, 0.58, 1.05 + 0.1 * ease(f / n)).filter(ImageFilter.GaussianBlur(3)).convert('RGBA')
        fr.alpha_composite(Image.new('RGBA', (W, H), NAVY + (int(212 * ease(t / 0.45)),)))
        at = lambda d0: ease((t - d0) / 0.35)
        dy = lambda d0: int((1 - at(d0)) * 36)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        a = at(0.1)
        if a > 0:
            bw = 400; bx = (W - bw) // 2; by = 200 + dy(0.1)
            dl.rectangle((bx, by, bx + bw, by + 74), fill=(0, 0, 0, int(240 * a)), outline=GOLD + (int(255 * a),), width=3)
            dl.text((W // 2, by + 37), 'OFERTA BLACK', font=fl('InterDisplay-Black.otf', 44), fill=GOLD_L + (int(255 * a),), anchor='mm')
            fr.alpha_composite(lay)
        txt(fr, (W // 2, 350 + dy(.2)), 'V E R D E   M A R   B E A C H   C L U B  ·  P E N H A / S C', fl('Inter-SemiBold.otf', 24), GOLD_L, 'mm', at(.2), shadow=False)
        txt(fr, (W // 2, 455 + dy(.3)), 'APARTAMENTO\n2 DORMITÓRIOS', fl('InterDisplay-ExtraBold.otf', 66), WHITE, 'mm', at(.3), spacing=10)
        txt(fr, (W // 2, 590 + dy(.45)), 'DE R$ 550 MIL', fl('InterDisplay-Bold.otf', 46), (200, 200, 205), 'mm', at(.45))
        sp = ease((t - .65) / .2)
        if sp > 0:
            d = ImageDraw.Draw(fr); d.line((W // 2 - 165, 592, W // 2 - 165 + 330 * sp, 588), fill=(230, 60, 60), width=6)
        sc = ease((t - .8) / .3, 'back')
        if t > .8:
            txt(fr, (W // 2, 700), 'POR R$ 530 MIL', fl('InterDisplay-Black.otf', max(20, int(112 * (0.7 + 0.3 * sc)))), WHITE, 'mm', min(1, (t - .8) / .15))
        ab = at(1.1)
        if ab > 0:
            bw, bh = 680, 112; by = 820 + dy(1.1)
            pulse = 1 + 0.03 * math.sin(max(0, t - 1.6) * 6) * (t > 1.6)
            ew, eh = bw * pulse, bh * pulse
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.rounded_rectangle((W / 2 - ew / 2, by + bh / 2 - eh / 2, W / 2 + ew / 2, by + bh / 2 + eh / 2), int(eh / 2), fill=GOLD + (int(255 * ab),))
            dl.text((W // 2, by + bh // 2), 'CHAME NO WHATSAPP', font=fl('Inter-ExtraBold.otf', 40), fill=NAVY + (int(255 * ab),), anchor='mm')
            fr.alpha_composite(lay)
        txt(fr, (W // 2, 1010 + dy(1.25)), BRAND['whatsapp'], fl('InterDisplay-Bold.otf', 52), WHITE, 'mm', at(1.25))
        txt(fr, (W // 2, 1075 + dy(1.35)), BRAND['instagram'], fl('Inter-Medium.otf', 32), GOLD_L, 'mm', at(1.35))
        la = at(1.5)
        if la > 0:
            lg = LOGO.copy(); lg.putalpha(Image.eval(lg.getchannel('A'), lambda v: int(v * la)))
            fr.alpha_composite(lg, ((W - lg.width) // 2, 1260 + dy(1.5)))
        txt(fr, (W // 2, 1745), BRAND['site'], fl('Inter-Medium.otf', 28), (230, 230, 230), 'mm', at(1.6))
        txt(fr, (W // 2, 1825), f"{BRAND['creci']}  ·  Oferta sujeita a alteração e disponibilidade.", fl('Inter-Regular.otf', 21), (190, 190, 190), 'mm', at(1.6))
        if f > n - 8: fr = Image.blend(fr.convert('RGB'), Image.new('RGB', (W, H)), (f - (n - 8)) / 8).convert('RGBA')
        yield fr


def end_frames_cfg(c, dur=4.8):
    im = Image.open(f"{ROOT}/{PROJ}/{c['bg']}").convert('RGB'); s = 2700 / max(im.size)
    im = grade(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS))
    n = int(dur * FPS)
    for f in range(n):
        t = f / FPS
        fr = crop_zoom(im, 0.5, 0.5, 1.05 + 0.1 * ease(f / n)).filter(ImageFilter.GaussianBlur(3)).convert('RGBA')
        fr.alpha_composite(Image.new('RGBA', (W, H), NAVY + (int(212 * ease(t / 0.45)),)))
        at = lambda d0: ease((t - d0) / 0.35)
        dy = lambda d0: int((1 - at(d0)) * 36)
        a = at(0.1)
        if a > 0:
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            bf = fl('InterDisplay-Black.otf', 44); bw = dl.textlength(c['badge'], font=bf) + 80; bx = (W - bw) // 2; by = 200 + dy(0.1)
            dl.rectangle((bx, by, bx + bw, by + 74), fill=(0, 0, 0, int(240 * a)), outline=GOLD + (int(255 * a),), width=3)
            dl.text((W // 2, by + 37), c['badge'], font=bf, fill=GOLD_L + (int(255 * a),), anchor='mm')
            fr.alpha_composite(lay)
        txt(fr, (W // 2, 350 + dy(.2)), '  '.join(' '.join(w) for w in c['kicker'].split(' ')), fl('Inter-SemiBold.otf', 24), GOLD_L, 'mm', at(.2), shadow=False)
        txt(fr, (W // 2, 460 + dy(.3)), c['title'], fl('InterDisplay-ExtraBold.otf', 66), WHITE, 'mm', at(.3), spacing=10)
        sc = ease((t - .6) / .3, 'back')
        if t > .6:
            txt(fr, (W // 2, 650), c['big'], fl('InterDisplay-Black.otf', max(20, int(c.get('big_size', 120) * (0.7 + 0.3 * sc)))), WHITE, 'mm', min(1, (t - .6) / .15))
        txt(fr, (W // 2, 745 + dy(.8)), c['sub'], fl('Inter-Bold.otf', 36), GOLD_L, 'mm', at(.8))
        ab = at(1.1)
        if ab > 0:
            bw, bh = 680, 112; by = 830 + dy(1.1)
            pulse = 1 + 0.03 * math.sin(max(0, t - 1.6) * 6) * (t > 1.6)
            ew, eh = bw * pulse, bh * pulse
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.rounded_rectangle((W / 2 - ew / 2, by + bh / 2 - eh / 2, W / 2 + ew / 2, by + bh / 2 + eh / 2), int(eh / 2), fill=GOLD + (int(255 * ab),))
            dl.text((W // 2, by + bh // 2), c.get('cta', 'CHAME NO WHATSAPP'), font=fl('Inter-ExtraBold.otf', 40), fill=NAVY + (int(255 * ab),), anchor='mm')
            fr.alpha_composite(lay)
        txt(fr, (W // 2, 1020 + dy(1.25)), BRAND['whatsapp'], fl('InterDisplay-Bold.otf', 52), WHITE, 'mm', at(1.25))
        txt(fr, (W // 2, 1085 + dy(1.35)), BRAND['instagram'], fl('Inter-Medium.otf', 32), GOLD_L, 'mm', at(1.35))
        la = at(1.5)
        if la > 0:
            lg = LOGO.copy(); lg.putalpha(Image.eval(lg.getchannel('A'), lambda v: int(v * la)))
            fr.alpha_composite(lg, ((W - lg.width) // 2, 1260 + dy(1.5)))
        txt(fr, (W // 2, 1745), BRAND['site'], fl('Inter-Medium.otf', 28), (230, 230, 230), 'mm', at(1.6))
        txt(fr, (W // 2, 1825), f"{BRAND['creci']}  ·  {c['legal']}", fl('Inter-Regular.otf', 21), (190, 190, 190), 'mm', at(1.6))
        if f > n - 8: fr = Image.blend(fr.convert('RGB'), Image.new('RGB', (W, H)), (f - (n - 8)) / 8).convert('RGBA')
        yield fr


# ---------------- itens ----------------
def clip_frames(it):
    """Gera (frame RGBA, t_orig_audio) para um item de video."""
    kind = it.get('res', 'hd')
    real = it.get('speed', 'real') == 'real'
    src_fps = 30 if kind == '4k' else 59.94
    if real:
        n = int(round((it['out'] - it['in']) * FPS))
    else:
        n = int(round(it['dur'] * FPS))
    r = Reader(f"{ROOT}/{PROJ}/{it['src']}", it['in'] - it.get('file0', 0), kind)
    span = (it['out'] - it['in']) * src_fps
    keys = it.get('frame', [(0, 0.5, 0.5, 1.0)])
    cut_readers = {}
    for f in range(n):
        t = f / FPS
        p = f / max(1, n - 1)
        if real:
            idx = int(round(t * src_fps))
        else:
            q = p - math.sin(2 * math.pi * p) / (2 * math.pi) * it.get('ramp', 0.85)
            idx = int(q * (span - 1))
        im = r.get(idx)
        cx, cy, z = interp_frame(keys, t)
        fr = crop_zoom(im, cx, cy, z)
        # cutaway: troca a imagem mantendo o audio
        for ci, c in enumerate(it.get('cutaways', [])):
            if c['t0'] <= t < c['t1']:
                if ci not in cut_readers:
                    cut_readers[ci] = (Reader(f"{ROOT}/{PROJ}/{c['src']}", c['in'], c.get('res', 'hd')), f)
                cr, f0 = cut_readers[ci]
                cfps = 30 if c.get('res', 'hd') == '4k' else 59.94
                cn = (c['t1'] - c['t0']) * FPS
                pp = (f - f0) / max(1, cn - 1)
                cidx = int(pp * (c['out'] - c['in']) * cfps * 0.999)
                cim = cr.get(cidx)
                k2 = c.get('frame', [(0, 0.5, 0.5, 1.0), (c['t1'] - c['t0'], 0.5, 0.5, 1.12)])
                fr = crop_zoom(cim, *interp_frame(k2, t - c['t0']))
                if c.get('label'):
                    fr = fr.convert('RGBA'); draw_label(fr, t - c['t0'], c['t1'] - c['t0'], *c['label'])
        g = (1.03, 1.04) if STYLE['look'] == 'natural' else (1.06, 1.10)
        yield grade(fr.convert('RGB'), *g).convert('RGBA'), (it['audio'][1] + t if it.get('audio') else None), t, n
    r.close()
    for cr, _ in cut_readers.values(): cr.close()


def photo_frames(it):
    im = Image.open(f"{ROOT}/{PROJ}/jpg/{it['photo']}.jpg").convert('RGB'); s = 2700 / max(im.size)
    im = grade(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS), 1.07, 1.12)
    n = int(it['dur'] * FPS); a, b = it['a'], it['b']
    for f in range(n):
        p = ease(f / (n - 1))
        yield crop_zoom(im, *(a[i] + (b[i] - a[i]) * p for i in range(3))).convert('RGBA'), None, f / FPS, n


def hblur(fr, amount):
    if amount < 2: return fr
    k = max(1, int(W / amount))
    return fr.resize((k, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)


def main(spec_path, out):
    global PROJ
    spec = runpy.run_path(spec_path)
    PROJ = spec.get('PROJECT', 'verdemar')
    if spec.get('END') == 'cfg' and not spec.get('END_CFG'): raise SystemExit('END_CFG ausente')
    CHIP.update(spec.get('CHIP', {}))
    STYLE.update(spec.get('STYLE', {}))
    TL = spec['TIMELINE']; hook = HOOKS.get(spec.get('HOOK'))
    hook_until = spec.get('HOOK_UNTIL', 2.6)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-vf', ('eq=contrast=1.02:saturation=1.03,vignette=PI/9' if STYLE['look'] == 'natural' else 'colorbalance=rs=-0.02:bs=0.04:rh=0.04:bh=-0.03,vignette=PI/6,noise=alls=3:allf=t'),
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out + '.video.mp4'], stdin=subprocess.PIPE)
    gt = 0; audio = []; whooshes = []; WH = 4
    for ii, it in enumerate(TL):
        whip_in = it.get('trans', 'whip') == 'whip' and ii > 0
        whip_out = ii + 1 < len(TL) and TL[ii + 1].get('trans', 'whip') == 'whip'
        if whip_in: whooshes.append(gt)
        gen = clip_frames(it) if 'src' in it else photo_frames(it)
        groups = make_groups(it['audio'][0], it['audio'][1], it['audio'][1] + (it['out'] - it['in'])) if it.get('audio') and it.get('captions', True) else []
        if it.get('audio'):
            audio.append((gt, it['audio'][2], it['audio'][1], it['out'] - it['in']))
        direction = 1 if ii % 2 == 0 else -1
        for f, (fr, t_orig, t, n) in enumerate(gen):
            blur = 0
            if whip_in and f < WH: blur = 45 * (1 - f / WH)
            if whip_out and f >= n - WH: blur = max(blur, 45 * (f - (n - WH) + 1) / WH)
            if blur:
                off = int((blur / 45) * 90 * direction * (1 if f >= n - WH else -1))
                fr = hblur(Image.fromarray(np.roll(np.asarray(fr), off, axis=1)).convert('RGB'), blur).convert('RGBA')
            in_cut = any(c['t0'] <= t < c['t1'] for c in it.get('cutaways', []))
            if it.get('label') and not in_cut:
                draw_label(fr, t, n / FPS, *it['label'])
            elif groups and t_orig is not None:
                if not in_cut or not any(c.get('label') for c in it['cutaways'] if c['t0'] <= t < c['t1']):
                    fr.alpha_composite(GRAD); draw_captions(fr, groups, t_orig)
            if hook and gt < hook_until:
                hook(fr, gt)
            brand_bug(fr)
            if ii == 0 and f < 3:
                fr = Image.blend(Image.new('RGB', (W, H)), fr.convert('RGB'), (f + 1) / 4).convert('RGBA')
            enc.stdin.write(fr.convert('RGB').tobytes()); gt += 1 / FPS
        print('ok', ii, round(gt, 2), flush=True)
    end_t = gt; whooshes.append(gt)
    for fr in end_frames(spec.get('END', 'black'), spec.get('END_CFG')):
        enc.stdin.write(fr.convert('RGB').tobytes()); gt += 1 / FPS
    enc.stdin.close(); enc.wait()
    total = gt
    # ---------- audio ----------
    inputs, filt, labels = [], [], []
    for k, (t0, src, a_in, dur) in enumerate(audio):
        inputs += ['-ss', f'{a_in:.3f}', '-t', f'{dur:.3f}', '-i', f'{ROOT}/{PROJ}/videos/{src}']
        ms = int(t0 * 1000)
        filt.append(f'[{k}:a]aresample=48000,highpass=f=90,afftdn=nf=-25,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=4,'
                    f'equalizer=f=3500:t=q:w=1.2:g=2.5,afade=t=in:d=0.03,afade=t=out:st={max(0, dur - 0.06):.3f}:d=0.06,adelay={ms}|{ms},apad=whole_dur={total:.2f}[a{k}]')
        labels.append(f'[a{k}]')
    for i, t in enumerate(whooshes):
        st = max(0, t - 0.28); ms = int(st * 1000)
        filt.append(f"anoisesrc=d=0.5:c=pink:a=0.6:seed={i + 3},bandpass=f={1800 if i % 2 else 2600}:width_type=o:w=2.2,afade=t=in:d=0.28:curve=exp,"
                    f"afade=t=out:st=0.28:d=0.22,volume=0.5,adelay={ms}|{ms},apad=whole_dur={total:.2f}[w{i}]")
        labels.append(f'[w{i}]')
    for j, (t, fq, v) in enumerate([(0.85, 48, 1.3)] * (spec.get('HOOK') == 'black') + [(end_t, 50, 1.3), (end_t + 0.8, 60, 1.0), (end_t + 1.5, 70, 0.7)]):
        ms = int(t * 1000)
        filt.append(f"sine=f={fq}:d=1.0,afade=t=out:d=1.0:curve=exp,volume={v},adelay={ms}|{ms},apad=whole_dur={total:.2f}[b{j}]")
        labels.append(f'[b{j}]')
    filt.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,atrim=0:{total:.2f}[aout]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(filt), '-map', '[aout]', '-ac', '2', '-ar', '48000', out + '.wav'], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', out + '.video.mp4', '-i', out + '.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow',
                    '-crf', '20', '-maxrate', '12M', '-bufsize', '24M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    print('total', round(total, 2))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
