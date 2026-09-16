#!/usr/bin/env python3
import argparse,csv,hashlib
from pathlib import Path
ap=argparse.ArgumentParser(description='Verify local archive files against inventory.csv SHA256')
ap.add_argument('--root',required=True,type=Path); ap.add_argument('--limit',type=int,default=0)
a=ap.parse_args(); root=a.root.expanduser().resolve(); inv=root/'99_Metadata'/'inventory.csv'
rows=list(csv.DictReader(inv.open(encoding='utf-8-sig'))); rows=rows[:a.limit] if a.limit else rows
bad=[]; ok=0
for i,r in enumerate(rows,1):
    p=root/r['path']
    if not p.exists(): bad.append((r['path'],'missing')); continue
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    if h.hexdigest()!=r['sha256']: bad.append((r['path'],'hash mismatch'))
    else: ok+=1
    if i%100==0: print(f'verified {i}/{len(rows)}',flush=True)
print(f'OK={ok} BAD={len(bad)} TOTAL={len(rows)}')
for x in bad[:100]: print('BAD',*x)
raise SystemExit(1 if bad else 0)
