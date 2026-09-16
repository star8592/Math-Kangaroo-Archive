#!/usr/bin/env python3
import argparse,csv,json,shutil,collections
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True,type=Path); ap.add_argument('--repo',required=True,type=Path)
a=ap.parse_args(); root=a.root.resolve(); repo=a.repo.resolve(); data=repo/'data'; data.mkdir(parents=True,exist_ok=True); meta=root/'99_Metadata'
for name in ('inventory.csv','duplicates.json','library_summary.json'):
    if (meta/name).exists(): shutil.copy2(meta/name,data/name)
rows=list(csv.DictReader((meta/'inventory.csv').open(encoding='utf-8-sig')))
coverage=[]
source_collections=[('USA Official','01_Official_USA/'),('Canada University Archive','02_Canada_University_Archive/'),('China Public Resources','03_China_Public_Resources/'),('France Official Archive','04_France_Official_Archive/'),('Germany Official Archive','05_Germany_Official_Archive/'),('Austria Official Archive','06_Austria_Official_Archive/')]
for label,prefix in source_collections:
    rr=[x for x in rows if x['path'].startswith(prefix)]; years=sorted({int(x['year']) for x in rr if x.get('year','').isdigit()})
    coverage.append({'collection':label,'files':len(rr),'pdfs':sum(x['ext']=='.pdf' for x in rr),'html':sum(x['ext'] in('.html','.htm') for x in rr),'year_min':min(years) if years else '', 'year_max':max(years) if years else ''})
with (data/'source_coverage.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=coverage[0].keys()); w.writeheader(); w.writerows(coverage)
# aggregate question statistics only; never export question bodies
qf=meta/'sample_questions.jsonl'; c=collections.Counter(); concepts=collections.Counter(); n=0
if qf.exists():
    for line in qf.open(encoding='utf-8'):
        q=json.loads(line); n+=1; c[(q.get('year'),q.get('level'),q.get('language'))]+=1; concepts[q.get('concept','')]+=1
with (data/'sample_question_stats.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['year','level','language','count']); [w.writerow([*k,v]) for k,v in sorted(c.items(),key=lambda x:tuple(map(str,x[0])))]
(data/'sample_question_summary.json').write_text(json.dumps({'structured_public_sample_questions':n,'top_concepts':concepts.most_common(30)},ensure_ascii=False,indent=2),encoding='utf-8')
# merge failure logs without exporting page contents
fails=[]
for p in meta.glob('*log.json'):
    try:
        x=json.loads(p.read_text())
        if isinstance(x,list): fails += [r for r in x if isinstance(r,dict) and r.get('status')=='fail']
    except Exception: pass
with (data/'upstream_failures.csv').open('w',newline='',encoding='utf-8') as f:
    fields=['country','title','url','path','error']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); [w.writerow({k:r.get(k,'') for k in fields}) for r in fails]
print(json.dumps({'coverage':coverage,'question_records':n,'failures':len(fails)},ensure_ascii=False,indent=2))
