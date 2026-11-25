import subprocess, re, os, sys, json
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
code = {'Evolution':'EV','Floratta':'FL','Polinésia':'PO','Torres do Glória':'TG','Urban Azaléia':'AZ','Urban Baviera':'BV','Urban Orquideas':'OR'}
MES = {'janeiro':1,'fevereiro':2,'fevereio':2,'março':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}
cur = None; months = []
for l in open('../tools/tree_jv.txt'):
    m = re.match(r'^\[D\] (.+) (\S+)$', l.rstrip())
    if m: cur = code.get(m.group(1)); continue
    m = re.match(r'^  \[D\] (.+) (\S+)$', l.rstrip())
    if m and cur:
        name = m.group(1).lower(); y = re.search(r'20\d\d', name).group(0)
        mo = next(v for k, v in MES.items() if k in name)
        months.append((cur, f'{y}-{mo:02d}', m.group(2)))
print(len(months))
def lst(fid):
    out = subprocess.run(['node', '../tools/list2.js', fid, '1'], capture_output=True, text=True).stdout
    return [l.rsplit(' ', 1) for l in out.splitlines() if ' ' in l and not l.startswith('[D]')]
def dl(args):
    o, fid = args
    if os.path.exists(o): return
    tmp = o + '.tmp'
    subprocess.run(['curl', '-sL', '-o', tmp, f'https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t'])
    try:
        im = Image.open(tmp); im.draft('RGB', (1800, 1800)); im = im.convert('RGB'); im.thumbnail((1800, 1800)); im.save(o, quality=90)
    except Exception as e: print('bad', o, e)
    os.remove(tmp)
index = {}
with ThreadPoolExecutor(8) as ex:
    lists = list(ex.map(lambda m: (m, lst(m[2])), months))
jobs = []
for (c, ym, fid), files in lists:
    d = f'months/{c}_{ym}'; os.makedirs(d, exist_ok=True)
    imgs = [(n, i) for n, i in files if n.lower().endswith(('.jpg', '.jpeg', '.png'))]
    index[f'{c}_{ym}'] = [n for n, _ in imgs]
    for k, (n, i) in enumerate(imgs): jobs.append((f'{d}/{k:02d}.jpg', i))
json.dump(index, open('months_index.json', 'w'), indent=1, ensure_ascii=False)
print('jobs', len(jobs), flush=True)
with ThreadPoolExecutor(10) as ex: list(ex.map(dl, jobs))
print('DONE', flush=True)
