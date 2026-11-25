import json, glob, os, numpy as np
from PIL import Image, ImageFilter
idx = json.load(open('months_index.json'))
def sig(p):
    im = Image.open(p); im.draft('L', (200, 200)); im = im.convert('L').resize((64, 36)).filter(ImageFilter.FIND_EDGES)
    a = np.asarray(im, float); a = (a - a.mean()) / (a.std() + 1e-6); return a
REF = {'AZ': '1001', 'BV': '1001', 'EV': '1008', 'FL': '1001', 'PO': '1001', 'TG': '1013', 'OR': None}
out = {}
for c in REF:
    keys = sorted(k for k in idx if k.startswith(c + '_'))
    last = keys[-1]; files = idx[last]
    ri = next((i for i, n in enumerate(files) if REF[c] and REF[c] in n), 0)
    ref = sig(f'months/{last}/{ri:02d}.jpg'); refs = [ref]; picks = []
    for k in reversed(keys):
        cands = sorted(glob.glob(f'months/{k}/*.jpg'))
        if not cands: continue
        best = max(cands, key=lambda p: max((sig(p) * r).mean() for r in refs))
        picks.append((k.split('_')[1], best)); refs = [ref, sig(best)]
    out[c] = list(reversed(picks)); print(c, len(out[c]))
json.dump(out, open('picks.json', 'w'), indent=1)
