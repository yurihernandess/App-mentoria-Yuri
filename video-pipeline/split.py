"""Modo 'tese de investimento' (tela dividida): visual em cima, corretor(a) embaixo,
legenda palavra a palavra na divisoria, titulo fixo no topo, cartoes de dados.
Uso: python3 split.py <spec.py> <saida.mp4>
"""
import math, subprocess, sys, runpy, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import engine as E
from engine import W, H, FPS, fl, txt, ease, grade, GOLD, GOLD_L, NAVY, WHITE, Reader, interp_frame

TOP_H = 1060
BOT_H = H - TOP_H


def crop_box(im, cx, cy, wfrac, ow, oh):
    """Recorta regiao com aspecto ow:oh; wfrac = largura do recorte / largura da imagem."""
    iw, ih = im.size
    cw = iw * wfrac; ch = cw * oh / ow
    if ch > ih: ch = ih; cw = ch * ow / oh
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw); y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    return im.transform((ow, oh), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)


# ---------------- painel de cima ----------------
def top_video(it):
    res = it.get('res', 'hd'); fps_src = 30 if res == '4k' else 59.94
    r = Reader(f"{E.ROOT}/{E.PROJ}/{it['src']}", it['in'] - it.get('file0', 0), res)
    n = int(it['dur'] * FPS); span = (it['out'] - it['in']) * fps_src
    for f in range(n):
        p = f / max(1, n - 1)
        im = r.get(int(p * (span - 1)))
        z = it.get('z', (1.0, 1.08)); wf = 1 / (z[0] + (z[1] - z[0]) * p)
        yield grade(crop_box(im, it.get('cx', .5), it.get('cy', .5), wf, W, TOP_H), 1.05, 1.08)
    r.close()


def top_photo(it):
    im = Image.open(f"{E.ROOT}/{E.PROJ}/jpg/{it['photo']}.jpg").convert('RGB'); s = 2400 / max(im.size)
    im = grade(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS), 1.06, 1.1)
    n = int(it['dur'] * FPS); a, b = it.get('a', (.5, .5, 1.0)), it.get('b', (.5, .5, 1.12))
    for f in range(n):
        p = ease(f / max(1, n - 1))
        cx, cy, z = (a[i] + (b[i] - a[i]) * p for i in range(3))
        yield crop_box(im, cx, cy, 1 / z, W, TOP_H)


_bg_cache = {}
def card_bg(t):
    if 'bg' not in _bg_cache:
        y = np.linspace(0, 1, TOP_H)[:, None]; x = np.linspace(0, 1, W)[None, :]
        base = np.array(NAVY, float)
        g = (1 - 0.55 * y) * (0.9 + 0.1 * x)
        arr = np.clip(base[None, None, :] * (0.6 + 0.8 * g[..., None]), 0, 255).astype(np.uint8)
        _bg_cache['bg'] = Image.fromarray(arr)
    im = _bg_cache['bg'].copy().convert('RGBA'); d = ImageDraw.Draw(im)
    # linhas douradas animadas (acabamento clean)
    off = int((t * 60) % 120)
    for k in range(-2, 12):
        x0 = k * 120 + off
        d.line((x0, TOP_H, x0 + 500, 0), fill=GOLD + (18,), width=2)
    return im


def top_card(it):
    n = int(it['dur'] * FPS); c = it['card']
    for f in range(n):
        t = f / FPS
        fr = card_bg(t)
        at = lambda d0: ease((t - d0) / 0.3)
        dy = lambda d0: int((1 - at(d0)) * 40)
        cy = TOP_H // 2 + 40
        if c.get('kicker'):
            txt(fr, (W // 2, cy - 230 + dy(0)), c['kicker'], fl('Inter-Bold.otf', 38), GOLD_L, 'mm', at(0), shadow=False)
        if c.get('old'):
            txt(fr, (W // 2, cy - 130 + dy(.1)), c['old'], fl('InterDisplay-Bold.otf', 64), (190, 195, 205), 'mm', at(.1), shadow=False)
            sp = ease((t - .35) / .2)
            if sp > 0:
                d = ImageDraw.Draw(fr); tw = d.textlength(c['old'], font=fl('InterDisplay-Bold.otf', 64))
                d.line((W // 2 - tw / 2 - 10, cy - 128, W // 2 - tw / 2 - 10 + (tw + 20) * sp, cy - 134), fill=(230, 60, 60), width=8)
        s = ease((t - .25) / .35, 'back')
        big = c['big']; longest = max(len(x) for x in big.split('\n'))
        base = c.get('size', 190 if longest <= 6 else (140 if longest <= 10 else 104))
        if t > .25:
            txt(fr, (W // 2, cy + 10), big, fl('InterDisplay-Black.otf', max(10, int(base * (0.7 + 0.3 * s)))), WHITE, 'mm',
                min(1, (t - .25) / .15), spacing=4, shadow=False)
        if c.get('sub'):
            txt(fr, (W // 2, cy + 40 + int(base * 0.6 * (big.count('\n') + 1)) + dy(.55)), c['sub'], fl('Inter-SemiBold.otf', 40), GOLD_L, 'mm', at(.55), shadow=False, spacing=8)
        if c.get('note'):
            txt(fr, (W // 2, TOP_H - 150), c['note'], fl('Inter-Regular.otf', 24), (180, 185, 195), 'mm', at(.6), shadow=False)
        yield fr.convert('RGB')


def top_fit(it):
    im = Image.open(f"{E.ROOT}/{E.PROJ}/{it['fit']}").convert('RGB')
    n = int(it['dur'] * FPS)
    for f in range(n):
        p = ease(f / max(1, n - 1)); fr = card_bg(f / FPS)
        z = 1.0 + 0.06 * p; tw = int((W - 40) * z); th = int(im.height * tw / im.width)
        if th > TOP_H - 260: th = TOP_H - 260; tw = int(im.width * th / im.height)
        sm = im.resize((tw, th), Image.BILINEAR)
        fr.paste(sm, ((W - tw) // 2, (TOP_H - th) // 2 + 60))
        if it.get('label'): txt(fr, (W // 2, (TOP_H - th) // 2 + 20), it['label'], fl('Inter-Bold.otf', 40), GOLD_L, 'mm', ease(f / 10), shadow=False)
        yield fr.convert('RGB')


def top_stream(items):
    for it in items:
        gen = top_card(it) if 'card' in it else (top_photo(it) if 'photo' in it else (top_fit(it) if 'fit' in it else top_video(it)))
        yield from gen


# ---------------- painel de baixo (fala) ----------------
def voice_stream(segs):
    for sg in segs:
        r = Reader(f"{E.ROOT}/{E.PROJ}/{sg['src']}", sg['in'] - sg.get('file0', 0), sg.get('res', '4k'))
        fps_src = 30 if sg.get('res', '4k') == '4k' else 59.94
        n = int(round((sg['out'] - sg['in']) * FPS))
        for f in range(n):
            t = f / FPS
            im = r.get(int(round(t * fps_src)))
            cx, cy, wf = interp_frame(sg['frame'], t)
            yield (grade(crop_box(im, cx, cy, wf, W, BOT_H), 1.04, 1.06) if BOT_H else None), sg['audio'][1] + t, sg
        r.close()


def word_at(words, t):
    for i, (a, b, w) in enumerate(words):
        nxt = words[i + 1][0] if i + 1 < len(words) else b + 0.3
        if a - 0.02 <= t < min(nxt, a + 0.9):
            return w, t - a
    return None, 0


# ---------------- overlays ----------------
def overlays(fr, gt, spec, word, wt):
    # divisoria dourada
    d = ImageDraw.Draw(fr)
    if BOT_H: d.rectangle((0, TOP_H - 3, W, TOP_H + 3), fill=GOLD + (255,))
    cap_y = TOP_H + 4 if BOT_H else 1330
    # titulo fixo no topo
    hd = spec['HEADLINE']
    a = ease(gt / 0.3)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    grad = np.clip(1 - np.arange(330) / 330, 0, 1) ** 1.4 * 170
    gimg = Image.fromarray(np.dstack([np.zeros((330, W, 3), np.uint8), np.repeat(grad[:, None], W, 1).astype(np.uint8)]), 'RGBA')
    fr.alpha_composite(gimg, (0, 0))
    fs1 = 58
    while dl.textlength(hd[0], font=fl('InterDisplay-Black.otf', fs1)) > W - 90 and fs1 > 30: fs1 -= 2
    f1 = fl('InterDisplay-Black.otf', fs1)
    txt(fr, (W // 2, 150), hd[0], f1, WHITE, 'mm', a, stroke=3, spacing=2)
    if len(hd) > 1:
        f2 = fl('Inter-ExtraBold.otf', 34); tw = dl.textlength(hd[1], font=f2)
        x0 = (W - tw) / 2 - 26; y0 = 222
        dl.rounded_rectangle((x0, y0, x0 + tw + 52, y0 + 58), 29, fill=GOLD + (int(245 * a),))
        dl.text((W / 2, y0 + 29), hd[1], font=f2, fill=NAVY + (int(255 * a),), anchor='mm')
        fr.alpha_composite(lay)
    # selo (ex.: DECORADO)
    if spec.get('TAG'):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        t1, t2 = spec['TAG']; fa = fl('Inter-Bold.otf', 22); fb = fl('Inter-Medium.otf', 18)
        w1 = max(dl.textlength(t1, font=fa), dl.textlength(t2, font=fb))
        ty = TOP_H if BOT_H else 1500
        dl.rounded_rectangle((40, ty - 100, 40 + w1 + 32, ty - 30), 12, fill=(0, 0, 0, 150))
        dl.text((56, ty - 92), t1, font=fa, fill=GOLD_L + (255,)); dl.text((56, ty - 62), t2, font=fb, fill=(235, 235, 235, 255))
        fr.alpha_composite(lay)
    fr.alpha_composite(E.ICON, (W - 50 - E.ICON.width, (TOP_H if BOT_H else 1500) - 40 - E.ICON.height))
    # legenda palavra a palavra na divisoria
    if word:
        clean = word.upper().strip('.,!?')
        clean = E.FIX.get(clean, clean)
        pop = ease(wt / 0.09, 'back')
        fs = 92 if len(clean) <= 10 else int(92 * 10 / len(clean)) + 8
        col = GOLD_L if clean in E.EMPH or clean in spec.get('EMPH', set()) else WHITE
        txt(fr, (W // 2, cap_y), clean, fl('InterDisplay-Black.otf', max(30, int(fs * (0.8 + 0.2 * pop)))), col, 'mm', 1.0, stroke=7)


def main(spec_path, out):
    global TOP_H, BOT_H
    spec = runpy.run_path(spec_path)
    E.PROJ = spec['PROJECT']
    if spec.get('FULL'): TOP_H = H; BOT_H = 0; _bg_cache.clear()
    segs = spec['VOICE']
    total_voice = sum(s['out'] - s['in'] for s in segs)
    # completa o painel de cima ate cobrir a fala
    tops = list(spec['TOP']); have = sum(t['dur'] for t in tops)
    if have < total_voice: tops[-1]['dur'] += total_voice - have
    words = {}
    for s in segs:
        words.setdefault(s['audio'][0], E.TRANS[s['audio'][0]]['words'])
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-vf', 'eq=contrast=1.02:saturation=1.03', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
                            out + '.video.mp4'], stdin=subprocess.PIPE)
    top = top_stream(tops); gt = 0; audio = []; t_acc = 0; last_top = None
    for s in segs:
        audio.append((t_acc, s['audio'][2], s['audio'][1], s['out'] - s['in'])); t_acc += s['out'] - s['in']
    for bot, t_orig, sg in voice_stream(segs):
        topf = next(top, None) or last_top
        last_top = topf
        fr = Image.new('RGBA', (W, H)); fr.paste(topf, (0, 0))
        if BOT_H: fr.paste(bot, (0, TOP_H))
        w, wt = word_at([x for x in words[sg['audio'][0]] if sg['in'] - 0.05 <= x[0] < sg['out']], t_orig)
        overlays(fr, gt, spec, w, wt)
        if gt < 0.12: fr = Image.blend(Image.new('RGB', (W, H)), fr.convert('RGB'), gt / 0.12 * 0.9 + 0.1).convert('RGBA')
        enc.stdin.write(fr.convert('RGB').tobytes()); gt += 1 / FPS
    end_t = gt
    for fr in E.end_frames(None, spec['END_CFG']):
        enc.stdin.write(fr.convert('RGB').tobytes()); gt += 1 / FPS
    enc.stdin.close(); enc.wait()
    total = gt
    inputs, filt, labels = [], [], []
    for k, (t0, src, a_in, dur) in enumerate(audio):
        inputs += ['-ss', f'{a_in:.3f}', '-t', f'{dur:.3f}', '-i', f'{E.ROOT}/{E.PROJ}/videos/{src}']
        ms = int(t0 * 1000)
        filt.append(f'[{k}:a]aresample=48000,highpass=f=90,afftdn=nf=-25,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=4,'
                    f'equalizer=f=3500:t=q:w=1.2:g=2.5,afade=t=in:d=0.03,afade=t=out:st={max(0, dur - 0.06):.3f}:d=0.06,adelay={ms}|{ms},apad=whole_dur={total:.2f}[a{k}]')
        labels.append(f'[a{k}]')
    for j, (t, fq, v) in enumerate([(end_t, 50, 1.3), (end_t + 0.8, 60, 1.0), (end_t + 1.5, 70, 0.7)]):
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
