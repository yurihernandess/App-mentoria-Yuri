import json, re, subprocess, os
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
d = json.load(open('prod_files.json'))
PRI = [('fachada', r'FACHADA.?NOTURN|Fachada noturna|FACHADA_NOTURNO|Fachada_Blue'), ('aerea', r'AEREA 1|AEREA_LAZER|Geral do lazer|LAZER GERAL|VOO_LAZER|HUMANIZADA_GERAL|Fotomontagem|ROGGA_AEREA'),
       ('piscina', r'PISCINA.?ADULTO|Pool_C1|PISCINA-ADULTO|Piscina adulto'), ('lazer', r'GOURMET|Festas|Espaço gourmet|QUIOSQUE'),
       ('living', r'LIVING|Living'), ('fachada2', r'FACHADA.?DI|Fachada diurna|Fachada_Day_C1|FACHADA_DIA')]
jobs = []
for k, files in d.items():
    imgs = [(p, i) for p, i in files if re.search(r'\.(jpe?g|png)$', p, re.I) and '/Logo/' not in p and 'Vistas' not in p]
    for tag, rx in PRI:
        m = next(((p, i) for p, i in imgs if re.search(rx, p)), None)
        if m: jobs.append((f'prod/{k}_{tag}.jpg', m[1], False)); print(k, tag, m[0].split('/')[-1])
        else: print(k, tag, '--')
    lg = next(((p, i) for p, i in files if '/Logo/' in p and p.lower().endswith('.png') and 'branco' not in p.lower()), None)
    if lg: jobs.append((f'prod/{k}_logo.png', lg[1], True))
def dl(a):
    o, fid, logo = a; tmp = o + '.tmp'
    subprocess.run(['curl', '-sL', '-o', tmp, f'https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t'])
    try:
        im = Image.open(tmp)
        if logo: im = im.convert('RGBA'); im.thumbnail((1400, 1400)); im.save(o)
        else: im.draft('RGB', (2600, 2600)); im = im.convert('RGB'); im.thumbnail((2600, 2600)); im.save(o, quality=92)
    except Exception as e: print('bad', o, e)
    os.remove(tmp)
with ThreadPoolExecutor(8) as ex: list(ex.map(dl, jobs))
print('done', len(jobs))
