#!/usr/bin/env python3
import argparse,sqlite3
from pathlib import Path
ap=argparse.ArgumentParser(description='Search Math Kangaroo local FTS5 index')
ap.add_argument('--root',required=True,type=Path)
ap.add_argument('--query',required=True)
ap.add_argument('--limit',type=int,default=20)
ap.add_argument('--questions',action='store_true',help='Search structured public sample questions instead of documents')
a=ap.parse_args(); db=a.root.expanduser().resolve()/'99_Metadata'/'library.sqlite'
if not db.exists(): raise SystemExit(f'Index not found: {db}')
con=sqlite3.connect(db); con.row_factory=sqlite3.Row
if a.questions:
    sql='''SELECT q.year,q.level,q.grades,q.language,q.question_no,q.difficulty,q.points,q.concept,q.question,q.answer,q.source_file,bm25(sample_questions_fts) rank FROM sample_questions_fts JOIN sample_questions q ON q.id=sample_questions_fts.rowid WHERE sample_questions_fts MATCH ? ORDER BY rank LIMIT ?'''
else:
    sql='''SELECT d.path,d.year,d.level,d.grades,d.language,d.source_url,snippet(documents_fts,2,'[',']',' … ',24) snippet,bm25(documents_fts) rank FROM documents_fts JOIN documents d ON d.id=documents_fts.rowid WHERE documents_fts MATCH ? ORDER BY rank LIMIT ?'''
for r in con.execute(sql,(a.query,a.limit)):
    print(dict(r))
