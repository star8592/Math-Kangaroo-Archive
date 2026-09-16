#!/usr/bin/env python3
"""Download only publicly accessible Math Kangaroo materials from official sites.
Does not bypass logins, paywalls, CAPTCHAs, access controls, or DRM.
"""
import argparse,hashlib,json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlparse,quote
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests
from bs4 import BeautifulSoup
UA={'User-Agent':'Math-Kangaroo-Archive/1.0 (+educational metadata archive)'}

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def safe_name(s): return re.sub(r'[^A-Za-z0-9._ -]+','_',s).strip().replace(' ','_')[:180] or 'file'
def fetch(url,tries=3,timeout=45):
    err=None
    for i in range(tries):
        try:
            r=requests.get(url,headers=UA,timeout=timeout,allow_redirects=True); r.raise_for_status(); return r
        except Exception as e: err=e; time.sleep(1+i)
    raise err

def save(root,rel,url,log,source_page=''):
    p=root/rel; p.parent.mkdir(parents=True,exist_ok=True)
    try:
        r=fetch(url); b=r.content
        p.write_bytes(b)
        log.append({'path':str(rel),'url':url,'final_url':r.url,'source_page':source_page,'size':len(b),'sha256':sha256_bytes(b),'status':'ok'})
        return True
    except Exception as e:
        log.append({'path':str(rel),'url':url,'source_page':source_page,'status':'fail','error':repr(e)})
        return False

def sync_usa(root,log):
    pages=[
      ('samples','https://mathkangaroo.org/mks/practice/free-question-samples/','01_Official_USA/Sample_Questions_2006_2026'),
      ('curricula','https://mathkangaroo.org/mks/resources/math-kangaroo-curricula/','01_Official_USA/Curricula'),
      ('team','https://mathkangaroo.org/mks/math-kangaroo-team-competition/team-competition-sample/','01_Official_USA/Team_Competition'),
      ('bulletins','https://mathkangaroo.org/mks/resources/bulletins/','01_Official_USA/Bulletins'),
    ]
    for kind,page,folder in pages:
        r=fetch(page); s=BeautifulSoup(r.text,'html.parser'); seen=set()
        for a in s.find_all('a',href=True):
            u=urljoin(r.url,a['href']); text=' '.join(a.stripped_strings)
            if '.pdf' not in u.lower() or u in seen: continue
            seen.add(u)
            if kind=='samples' and not re.search(r'20(0[6-9]|1\d|2\d).*sample',u,re.I): continue
            if kind=='curricula' and 'curriculum' not in u.lower(): continue
            if 'Introduction-to-Schools' in u and kind=='bulletins': continue
            fn=Path(urlparse(u).path).name
            if kind=='samples':
                m=re.search(r'(20\d{2})',text+' '+u); fn=f'{m.group(1) if m else "unknown"}_Math_Kangaroo_USA_Sample_Questions.pdf'
            elif kind=='bulletins' and text: fn=safe_name(text)+'.pdf'
            save(root,Path(folder)/fn,u,log,page)

def sync_france(root,log):
    base='https://www.mathkang.org/'
    pdf_seen=set(); html_seen=set()
    for year in range(2004,2027):
        page=f'{base}concours/sujsol{year}.html'
        try: r=fetch(page)
        except Exception as e:
            log.append({'path':'','url':page,'status':'fail','error':repr(e)}); continue
        d=Path('04_France_Official_Archive')/str(year); (root/d).mkdir(parents=True,exist_ok=True); (root/d/'archive_page.html').write_bytes(r.content)
        s=BeautifulSoup(r.text,'html.parser')
        for a in s.find_all('a',href=True):
            u=urljoin(r.url,a['href']); p=urlparse(u).path.lower()
            if urlparse(u).netloc not in ('www.mathkang.org','mathkang.org'): continue
            if p.endswith('.pdf') and str(year) in p and ('kangourou' in p or f'k{year}' in p):
                if u not in pdf_seen:
                    pdf_seen.add(u); save(root,d/'pdf'/Path(urlparse(u).path).name,u,log,page)
            elif p.endswith('.html') and str(year) in p and any(k in p for k in ('sol','corr','suj')) and u!=page:
                if u not in html_seen:
                    html_seen.add(u); save(root,d/'solutions_html'/Path(urlparse(u).path).name,u,log,page)

def sync_germany(root,log):
    page='https://www.mathe-kaenguru.de/chronik/aufgaben/'; r=fetch(page)
    out=Path('05_Germany_Official_Archive'); (root/out).mkdir(parents=True,exist_ok=True); (root/out/'source_index.html').write_bytes(r.content)
    s=BeautifulSoup(r.text,'html.parser'); items=[]; seen=set()
    for a in s.find_all('a',href=True):
        u=urljoin(r.url,a['href'])
        if '.pdf' not in u.lower() or u in seen: continue
        seen.add(u); items.append((u,Path(urlparse(u).path).name,' '.join(a.stripped_strings)))
    def one(x):
        u,fn,title=x; local=[]; save(root,out/'pdf'/fn,u,local,page); return local[0]|{'title':title,'country':'Germany'}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(one,x) for x in items]): log.append(f.result())

def sync_austria(root,log):
    page='https://www.kaenguru.at/aufgaben.html'; r=fetch(page)
    out=Path('06_Austria_Official_Archive'); (root/out).mkdir(parents=True,exist_ok=True); (root/out/'source_index.html').write_bytes(r.content)
    s=BeautifulSoup(r.text,'html.parser'); urls=[]; seen=set()
    for a in s.find_all('a',href=True):
        u=urljoin(r.url,a['href'])
        if '.pdf' in u.lower() and u not in seen:
            seen.add(u); urls.append(u)
    types=['Felix1','Felix2','Ecolier','Benjamin','Kadett','Junior','Student']; base='https://www.kaenguru.at/files/problems/'
    fns=[]
    for t in types:
        fns += [f'2026_{t}_AUT.pdf',f'2026_{t}_AUT_E.pdf',f'Lösungen_{t}_2026.pdf',f'2025_{t}.pdf',f'2025_{t}_E.pdf',f'2025_{t}_Loesungen.pdf',f'2024_{t}.pdf',f'2024_{t}_E.pdf',f'AUT_{t}_2024_Loesungen.pdf',f'2023_{t}.pdf',f'2023_{t}_EN.pdf',f'2023_{t}_UK.pdf',f'2023_{t}_Loesungen.pdf']
    for fn in fns:
        u=base+quote(fn)
        if u not in seen: seen.add(u); urls.append(u)
    def one(u):
        fn=Path(urlparse(u).path).name
        # preserve readable Unicode name for percent-encoded 2026 solution files
        from urllib.parse import unquote
        fn=unquote(fn); local=[]; save(root,out/'pdf'/fn,u,local,page); return local[0]|{'country':'Austria'}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for f in as_completed([ex.submit(one,u) for u in urls]): log.append(f.result())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True,type=Path); ap.add_argument('--sources',nargs='+',choices=['usa','france','germany','austria','all'],default=['all'])
    a=ap.parse_args(); root=a.root.expanduser().resolve(); root.mkdir(parents=True,exist_ok=True); (root/'99_Metadata').mkdir(exist_ok=True)
    sources={'usa':sync_usa,'france':sync_france,'germany':sync_germany,'austria':sync_austria}; chosen=list(sources) if 'all' in a.sources else a.sources
    log=[]
    for name in chosen:
        print('SYNC',name,flush=True); sources[name](root,log)
    p=root/'99_Metadata'/'official_sync_log.json'; p.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    ok=sum(x.get('status')=='ok' for x in log); fail=sum(x.get('status')=='fail' for x in log); print(json.dumps({'records':len(log),'ok':ok,'fail':fail},ensure_ascii=False))
if __name__=='__main__': main()
