#!/usr/bin/env python3
import argparse,csv,hashlib,json,re,sqlite3,subprocess
from collections import defaultdict
from pathlib import Path
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup=None

def get_root():
    ap=argparse.ArgumentParser(description='Rebuild Math Kangaroo local metadata and FTS5 index')
    ap.add_argument('--root',required=True,type=Path)
    return ap.parse_args().root.expanduser().resolve()

def extract_year(rel):
    name=Path(rel).name
    m=re.search(r'(19\d{2}|20\d{2})',name)
    if m: return m.group(1)
    parts=Path(rel).parts
    for part in reversed(parts):
        if re.fullmatch(r'(19\d{2}|20\d{2})',part): return part
    if rel.startswith('05_Germany_Official_Archive/'):
        m=re.match(r'(\d{2})_',name)
        if m:
            yy=int(m.group(1)); return str(1900+yy if yy>=98 else 2000+yy)
    m=re.search(r'(19\d{2}|20\d{2})',rel)
    return m.group(1) if m else ''

def metadata(rel):
    year=extract_year(rel); level=''; grades=''; lang=''
    m=re.search(r'Level[_ -]?([A-F])',rel,re.I)
    if m: level=m.group(1).upper()
    grade_map={'A':'1-2','B':'3-4','C':'5-6','D':'7-8','E':'9-10','F':'11-12'}
    if level: grades=grade_map.get(level,'')
    if not grades:
        m=re.search(r'(?:Grades?|Klassenstufen?)[_ -]?(\d{1,2})[-_/ ](?:and|bis|&)?[_ -]?(\d{1,2})',rel,re.I)
        if m: grades=f'{m.group(1)}-{m.group(2)}'
        else:
            m=re.search(r'(?:kaenguru\d{4}|(?:^|/)(?:\d{2}))_(34|56|78|910|1113)',rel,re.I)
            if m: grades={'34':'3-4','56':'5-6','78':'7-8','910':'9-10','1113':'11-13'}[m.group(1)]
    low=rel.lower(); name=Path(low).name
    if '/zh/' in low: lang='zh'
    elif '/en/' in low or re.search(r'(_en|_eng|_english|_e)\.',name): lang='en'
    elif re.search(r'_fr\.',name): lang='fr'
    elif re.search(r'_uk\.',name): lang='uk'
    elif '/04_france_' in low: lang='fr'
    elif '/05_germany_' in low: lang='de'
    elif '/06_austria_' in low: lang='de'
    elif '/03_china_' in low: lang='zh/mixed'
    elif '/01_' in low or 'official_usa' in low: lang='en'
    return year,level,grades,lang

def extract_text(p):
    ext=p.suffix.lower()
    if ext=='.pdf':
        try:
            q=subprocess.run(['pdftotext','-layout',str(p),'-'],capture_output=True,timeout=90)
            if q.returncode==0: return q.stdout.decode('utf-8','ignore')
        except Exception: return ''
    if ext in ('.html','.htm') and BeautifulSoup:
        try:
            raw=p.read_bytes(); html=None
            for enc in ('utf-8','gb18030','latin1'):
                try: html=raw.decode(enc); break
                except Exception: pass
            return ' '.join(BeautifulSoup(html or '','html.parser').stripped_strings)
        except Exception: return ''
    if ext in ('.md','.txt','.csv','.json','.jsonl','.py'):
        try: return p.read_text(errors='ignore')
        except Exception: return ''
    return ''

def main():
    root=get_root(); meta=root/'99_Metadata'; meta.mkdir(parents=True,exist_ok=True); db=meta/'library.sqlite'
    source_map={}
    for j in meta.glob('*log.json'):
        try:
            data=json.loads(j.read_text(errors='ignore'))
            if isinstance(data,list):
                for x in data:
                    if isinstance(x,dict):
                        p=x.get('path'); u=x.get('url') or x.get('source_url')
                        if p and u: source_map[p]=u
        except Exception: pass
    mf=meta/'manifest.csv'
    if mf.exists():
        try:
            for x in csv.DictReader(mf.open(encoding='utf-8-sig')):
                p=x.get('path') or x.get('relative_path') or x.get('file'); u=x.get('source_url') or x.get('url')
                if p and u: source_map.setdefault(p,u)
        except Exception: pass
    files=[p for p in root.rglob('*') if p.is_file() and p!=db and '.git' not in p.parts]
    rows=[]; texts={}
    for i,p in enumerate(files,1):
        rel=str(p.relative_to(root)); text=extract_text(p); texts[rel]=text
        h=hashlib.sha256()
        try:
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
            sha=h.hexdigest()
        except Exception: sha=''
        year,level,grades,lang=metadata(rel)
        rows.append({'path':rel,'ext':p.suffix.lower(),'size':p.stat().st_size,'sha256':sha,'year':year,'level':level,'grades':grades,'language':lang,'text_chars':len(text),'source_url':source_map.get(rel,'')})
        if i%100==0: print(f'indexed {i}/{len(files)}',flush=True)
    inv=meta/'inventory.csv'
    if rows:
        with inv.open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    groups=defaultdict(list)
    for x in rows:
        if x['sha256']: groups[x['sha256']].append(x['path'])
    dups=[v for v in groups.values() if len(v)>1]
    (meta/'duplicates.json').write_text(json.dumps(dups,ensure_ascii=False,indent=2),encoding='utf-8')
    if db.exists(): db.unlink()
    con=sqlite3.connect(db)
    con.execute('CREATE TABLE documents(id INTEGER PRIMARY KEY, path TEXT UNIQUE, title TEXT, ext TEXT, year TEXT, level TEXT, grades TEXT, language TEXT, size INTEGER, sha256 TEXT, source_url TEXT, text TEXT)')
    con.execute("CREATE VIRTUAL TABLE documents_fts USING fts5(title,path,text,content='documents',content_rowid='id')")
    for x in rows:
        title=Path(x['path']).stem.replace('_',' ')
        cur=con.execute('INSERT INTO documents(path,title,ext,year,level,grades,language,size,sha256,source_url,text) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(x['path'],title,x['ext'],x['year'],x['level'],x['grades'],x['language'],x['size'],x['sha256'],x['source_url'],texts[x['path']]))
        con.execute('INSERT INTO documents_fts(rowid,title,path,text) VALUES(?,?,?,?)',(cur.lastrowid,title,x['path'],texts[x['path']]))
    qfile=meta/'sample_questions.jsonl'
    if qfile.exists():
        con.execute('CREATE TABLE sample_questions(id INTEGER PRIMARY KEY, year INTEGER, level TEXT, grades TEXT, language TEXT, question_no INTEGER, difficulty TEXT, points INTEGER, concept TEXT, question TEXT, options_json TEXT, answer TEXT, solution TEXT, source_file TEXT)')
        con.execute("CREATE VIRTUAL TABLE sample_questions_fts USING fts5(concept,question,solution,content='sample_questions',content_rowid='id')")
        for line in qfile.open(encoding='utf-8'):
            r=json.loads(line); keys=['year','level','grades','language','question_no','difficulty','points','concept','question','options_json','answer','solution','source_file']
            cur=con.execute('INSERT INTO sample_questions(year,level,grades,language,question_no,difficulty,points,concept,question,options_json,answer,solution,source_file) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',tuple(r.get(k) for k in keys))
            con.execute('INSERT INTO sample_questions_fts(rowid,concept,question,solution) VALUES(?,?,?,?)',(cur.lastrowid,r.get('concept',''),r.get('question',''),r.get('solution','')))
    con.commit(); con.close()
    summary={'total_files':len(rows),'total_bytes':sum(x['size'] for x in rows),'pdfs':sum(x['ext']=='.pdf' for x in rows),'html':sum(x['ext'] in('.html','.htm') for x in rows),'indexed_text_docs':sum(x['text_chars']>0 for x in rows),'duplicate_groups':len(dups)}
    (meta/'library_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__': main()
