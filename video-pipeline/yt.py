"""Versao YouTube 16:9: corretor a esquerda (vertical), visuais a direita, legenda palavra a palavra.
Uso: python3 yt.py <spec.py> <saida.mp4>
"""
import math, subprocess, sys, runpy, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import engine as E
from engine import fl, txt, ease, grade, GOLD, GOLD_L, NAVY, WHITE, Reader, interp_frame
from split import crop_box

W, H, FPS = 1920, 1080, 30
LW = 608               # painel do corretor (9:16)
RW = W - LW            # painel visual
LOGO = Image.open(f'{E.ROOT}/brand/logo_full_dark.png'); LOGO.thumbnail((420, 320), Image.LANCZOS)
ICON = E.ICON


def bg(t, w=RW, h=H):
    y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    g = (1 - 0.5 * y) * (0.9 + 0.1 * x)
    arr = np.clip(np.array(NAVY, float)[None, None, :] * (0.6 + 0.8 * g[..., None]), 0, 255).astype(np.uint8)
    im = Image.fromarray(arr).convert('RGBA'); d = ImageDraw.Draw(im); off = int((t * 50) % 140)
    for k in range(-3, 16): d.line((k * 140 + off, h, k * 140 + off + 600, 0), fill=GOLD + (16,), width=2)
    return im
_BG = {}
def card_bg(t):
    key = int((t * 50) % 140)
    if key not in _BG: _BG[key] = bg(t)
    return _BG[key].copy()


def v_photo(it):
    im = Image.open(f"{E.ROOT}/{E.PROJ}/{it['photo']}").convert('RGB'); s = 3000 / max(im.size)
    im = grade(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS), 1.05, 1.08)
    n = int(round(it['dur'] * FPS)); a, b = it.get('a', (.5, .5, 1.0)), it.get('b', (.5, .5, 1.1))
    for f in range(n):
        p = ease(f / max(1, n - 1)); cx, cy, z = (a[i] + (b[i] - a[i]) * p for i in range(3))
        yield crop_box(im, cx, cy, 1 / z, RW, H).convert('RGBA')


def v_fit(it):
    im = Image.open(f"{E.ROOT}/{E.PROJ}/{it['fit']}").convert('RGB')
    n = int(round(it['dur'] * FPS))
    for f in range(n):
        t = f / FPS; fr = card_bg(t); z = 1 + 0.04 * ease(f / max(1, n - 1))
        th = int((H - 300) * z); tw = int(im.width * th / im.height)
        if tw > RW - 80: tw = int((RW - 80) * z); th = int(im.height * tw / im.width)
        fr.paste(im.resize((tw, th), Image.BILINEAR), ((RW - tw) // 2, (H - th) // 2 + 70))
        if it.get('label'): txt(fr, (RW // 2, 135), it['label'], fl('InterDisplay-ExtraBold.otf', 44), GOLD_L, 'mm', ease(t / .3), shadow=False)
        yield fr


def v_card(it):
    c = it['card']; n = int(round(it['dur'] * FPS))
    for f in range(n):
        t = f / FPS; fr = card_bg(t)
        at = lambda d0: ease((t - d0) / 0.3); dy = lambda d0: int((1 - at(d0)) * 40); cy = H // 2 - 20
        if c.get('kicker'): txt(fr, (RW // 2, cy - 210 + dy(0)), c['kicker'], fl('Inter-Bold.otf', 42), GOLD_L, 'mm', at(0), shadow=False)
        if c.get('old'):
            fo = fl('InterDisplay-Bold.otf', 60); txt(fr, (RW // 2, cy - 120 + dy(.1)), c['old'], fo, (190, 195, 205), 'mm', at(.1), shadow=False)
            sp = ease((t - .35) / .2)
            if sp > 0:
                d = ImageDraw.Draw(fr); tw = d.textlength(c['old'], font=fo)
                d.line((RW // 2 - tw / 2 - 10, cy - 118, RW // 2 - tw / 2 - 10 + (tw + 20) * sp, cy - 124), fill=(230, 60, 60), width=8)
        big = c['big']; longest = max(len(x) for x in big.split('\n')); base = c.get('size', 200 if longest <= 8 else (150 if longest <= 12 else 110))
        s = ease((t - .25) / .35, 'back')
        if t > .25: txt(fr, (RW // 2, cy + 10), big, fl('InterDisplay-Black.otf', max(10, int(base * (0.7 + 0.3 * s)))), WHITE, 'mm', min(1, (t - .25) / .15), spacing=4, shadow=False)
        if c.get('sub'): txt(fr, (RW // 2, cy + 40 + int(base * 0.6 * (big.count('\n') + 1)) + dy(.55)), c['sub'], fl('Inter-SemiBold.otf', 40), GOLD_L, 'mm', at(.55), shadow=False, spacing=10)
        if c.get('note'): txt(fr, (RW // 2, H - 150), c['note'], fl('Inter-Regular.otf', 24), (180, 185, 195), 'mm', at(.6), shadow=False)
        yield fr


def visual(it):
    if 'card' in it: return v_card(it)
    if 'fit' in it: return v_fit(it)
    return v_photo(it)


def end_frames(c, dur=7.0):
    base = Image.open(f"{E.ROOT}/{E.PROJ}/{c['bg']}").convert('RGB')
    base = crop_box(base, .5, .5, 1.0, W, H)
    n = int(dur * FPS)
    for f in range(n):
        t = f / FPS; fr = base.copy().convert('RGBA')
        fr.alpha_composite(Image.new('RGBA', (W, H), NAVY + (int(222 * ease(t / .5)),)))
        at = lambda d0: ease((t - d0) / 0.35)
        la = at(.2)
        if la > 0:
            lg = LOGO.copy(); lg.putalpha(Image.eval(lg.getchannel('A'), lambda v: int(v * la))); fr.alpha_composite(lg, (140, (H - lg.height) // 2 - 20))
        x = 1180
        d = ImageDraw.Draw(fr)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); a = at(.1)
        bf = fl('InterDisplay-Black.otf', 38); bw = dl.textlength(c['badge'], font=bf) + 70
        dl.rectangle((x - bw / 2, 150, x + bw / 2, 214), fill=(0, 0, 0, int(240 * a)), outline=GOLD + (int(255 * a),), width=3)
        dl.text((x, 182), c['badge'], font=bf, fill=GOLD_L + (int(255 * a),), anchor='mm'); fr.alpha_composite(lay)
        txt(fr, (x, 270), c['kicker'], fl('Inter-SemiBold.otf', 30), GOLD_L, 'mm', at(.25), shadow=False)
        for li, ln in enumerate(c['title'].split('\n')): txt(fr, (x, 335 + li * 66), ln, fl('InterDisplay-ExtraBold.otf', 58), WHITE, 'mm', at(.35))
        txt(fr, (x, 500), c['big'], fl('InterDisplay-Black.otf', 120), WHITE, 'mm', at(.55))
        txt(fr, (x, 590), c['sub'], fl('Inter-Bold.otf', 34), GOLD_L, 'mm', at(.7))
        ab = at(1.0)
        if ab > 0:
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            pulse = 1 + 0.03 * math.sin(max(0, t - 1.5) * 6) * (t > 1.5); bf2 = fl('Inter-ExtraBold.otf', 38); bw2, bh = (dl.textlength(c['cta'], font=bf2) + 120) * pulse, 100 * pulse
            dl.rounded_rectangle((x - bw2 / 2, 700 - bh / 2, x + bw2 / 2, 700 + bh / 2), int(bh / 2), fill=GOLD + (int(255 * ab),))
            dl.text((x, 700), c['cta'], font=bf2, fill=NAVY + (int(255 * ab),), anchor='mm'); fr.alpha_composite(lay)
        txt(fr, (x, 800), f"WhatsApp {E.BRAND['whatsapp']}  ·  {E.BRAND['instagram']}", fl('Inter-SemiBold.otf', 32), WHITE, 'mm', at(1.2))
        txt(fr, (x, 850), E.BRAND['site'], fl('Inter-Medium.otf', 28), (225, 225, 225), 'mm', at(1.3))
        txt(fr, (W // 2, H - 40), f"{E.BRAND['creci']}  ·  {c['legal']}", fl('Inter-Regular.otf', 22), (190, 190, 190), 'mm', at(1.4))
        if f > n - 10: fr = Image.blend(fr.convert('RGB'), Image.new('RGB', (W, H)), (f - (n - 10)) / 10).convert('RGBA')
        yield fr


def word_at(words, t):
    for i, (a, b, w) in enumerate(words):
        nxt = words[i + 1][0] if i + 1 < len(words) else b + 0.3
        if a - 0.02 <= t < min(nxt, a + 0.9): return w, t - a
    return None, 0


def main(spec_path, out):
    spec = runpy.run_path(spec_path); E.PROJ = spec['PROJECT']
    segs = spec['SEGMENTS']
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-vf', 'eq=contrast=1.02:saturation=1.03', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out + '.video.mp4'],
                           stdin=subprocess.PIPE)
    gt = 0; audio = []; hd = spec['HEADLINE']
    for si, (vs, visuals) in enumerate(segs):
        dur = vs['out'] - vs['in']; n = int(round(dur * FPS))
        tot = sum(v.get('w', 1) for v in visuals)
        for v in visuals: v['dur'] = dur * v.get('w', 1) / tot + 0.1
        vis = (fr for v in visuals for fr in visual(v)); last_v = None
        r = Reader(f"{E.ROOT}/{E.PROJ}/{vs['src']}", vs['in'], 'hd')
        words = [x for x in E.TRANS[vs['audio'][0]]['words'] if vs['in'] - 0.05 <= x[0] < vs['out']]
        audio.append((gt, vs['audio'][2], vs['in'], dur))
        for f in range(n):
            t = f / FPS; im = r.get(int(round(t * 59.94)))
            cx, cy, wf = interp_frame(vs['frame'], t)
            left = grade(crop_box(im, cx, cy, wf, LW, H), 1.04, 1.06)
            right = next(vis, None) or last_v; last_v = right
            fr = Image.new('RGBA', (W, H)); fr.paste(right, (LW, 0)); fr.paste(left, (0, 0))
            d = ImageDraw.Draw(fr); d.rectangle((LW - 3, 0, LW + 3, H), fill=GOLD + (255,))
            # barra de titulo
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.rectangle((LW + 3, 0, W, 86), fill=NAVY + (215,)); fr.alpha_composite(lay)
            txt(fr, (LW + 40, 43), hd, fl('InterDisplay-ExtraBold.otf', 36), WHITE, 'lm', 1, shadow=False)
            fr.alpha_composite(ICON, (W - 40 - ICON.width, 6))
            if spec.get('TAG'):
                txt(fr, (LW + 40, H - 34), spec['TAG'], fl('Inter-Medium.otf', 20), (230, 230, 230), 'lm', 0.9)
            w, wt = word_at(words, vs['in'] + t)
            if w:
                cl = w.upper().strip('.,!?'); cl = E.FIX.get(cl, cl); pop = ease(wt / 0.09, 'back')
                col = GOLD_L if cl in E.EMPH or cl in spec.get('EMPH', set()) else WHITE
                fs = 96 if len(cl) <= 10 else int(96 * 10 / len(cl)) + 10
                txt(fr, (LW // 2, H - 170), cl, fl('InterDisplay-Black.otf', max(30, int(fs * (0.8 + 0.2 * pop)))), col, 'mm', 1.0, stroke=7)
            if gt < 0.15: fr = Image.blend(Image.new('RGB', (W, H)), fr.convert('RGB'), gt / 0.15 * 0.9 + 0.1).convert('RGBA')
            enc.stdin.write(fr.convert('RGB').tobytes()); gt += 1 / FPS
        r.close()
        print('seg', si, round(gt, 1), flush=True)
    end_t = gt
    for fr in end_frames(spec['END']):
        enc.stdin.write(fr.convert('RGB').tobytes()); gt += 1 / FPS
    enc.stdin.close(); enc.wait(); total = gt
    inputs, filt, labels = [], [], []
    for k, (t0, src, a_in, dur) in enumerate(audio):
        inputs += ['-ss', f'{a_in:.3f}', '-t', f'{dur:.3f}', '-i', f'{E.ROOT}/{E.PROJ}/videos/{src}']; ms = int(t0 * 1000)
        filt.append(f'[{k}:a]aresample=48000,highpass=f=90,afftdn=nf=-25,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=4,'
                    f'equalizer=f=3500:t=q:w=1.2:g=2.5,afade=t=in:d=0.03,afade=t=out:st={max(0, dur - 0.06):.3f}:d=0.06,adelay={ms}|{ms},apad=whole_dur={total:.2f}[a{k}]')
        labels.append(f'[a{k}]')
    for j, (t, fq, v) in enumerate([(end_t, 50, 1.3), (end_t + 0.8, 60, 1.0)]):
        ms = int(t * 1000); filt.append(f"sine=f={fq}:d=1.0,afade=t=out:d=1.0:curve=exp,volume={v},adelay={ms}|{ms},apad=whole_dur={total:.2f}[b{j}]"); labels.append(f'[b{j}]')
    filt.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,atrim=0:{total:.2f}[aout]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(filt), '-map', '[aout]', '-ac', '2', '-ar', '48000', out + '.wav'], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', out + '.video.mp4', '-i', out + '.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow',
                    '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    print('total', round(total, 2))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
