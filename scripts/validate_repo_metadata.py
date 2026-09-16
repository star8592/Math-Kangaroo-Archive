#!/usr/bin/env python3
import csv,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; errors=[]
for p in root.rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.pdf','.html','.htm','.sqlite','.db'}: errors.append(f'raw/binary material should not be committed: {p.relative_to(root)}')
inv=root/'data'/'inventory.csv'
if not inv.exists(): errors.append('missing data/inventory.csv')
else:
    rows=list(csv.DictReader(inv.open(encoding='utf-8-sig')))
    required={'path','ext','size','sha256','year','level','grades','language','text_chars','source_url'}
    if not rows: errors.append('inventory is empty')
    elif not required.issubset(rows[0]): errors.append(f'inventory missing columns: {sorted(required-set(rows[0]))}')
    for i,r in enumerate(rows[:],2):
        sha=r.get('sha256','')
        if sha and (len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha.lower())): errors.append(f'bad sha256 row {i}')
summary=root/'data'/'library_summary.json'
if not summary.exists(): errors.append('missing data/library_summary.json')
else:
    try: json.loads(summary.read_text())
    except Exception as e: errors.append(f'invalid summary json: {e}')
if errors:
    print('\n'.join('ERROR: '+x for x in errors)); sys.exit(1)
print('metadata validation passed')
