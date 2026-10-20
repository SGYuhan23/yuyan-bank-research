"""SQLite optimistic concurrency; cases, results and reviews commit atomically."""
import json,sqlite3
from pathlib import Path
from .contracts import CaseRecord,Review,now,uid,digest
class Store:
    def __init__(self,path=None):
        self.path=Path(path or Path(__file__).resolve().parents[1]/'local/cases.sqlite')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, version INTEGER, body TEXT);
            CREATE TABLE IF NOT EXISTS history(id TEXT, version INTEGER, body TEXT, PRIMARY KEY(id,version));
            CREATE TABLE IF NOT EXISTS results(id TEXT PRIMARY KEY, case_id TEXT, version INTEGER, body TEXT);
            CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, body TEXT);
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, body TEXT);''')
    def db(self):
        db=sqlite3.connect(self.path,timeout=10);db.row_factory=sqlite3.Row;return db
    def create(self,c):
        c=CaseRecord.model_validate(c)
        if c.version!=1 or c.evidence or c.artifacts: raise ValueError('NEW_CASE_MUST_BE_EMPTY')
        with self.db() as db: db.execute('INSERT INTO cases VALUES(?,?,?)',(c.case_id,1,c.model_dump_json()))
        return c
    def get(self,cid):
        with self.db() as db: row=db.execute('SELECT body FROM cases WHERE id=?',(cid,)).fetchone()
        if not row: raise ValueError('CASE_NOT_FOUND')
        return CaseRecord.model_validate_json(row[0])
    @staticmethod
    def validate_evidence(c,ids):
        known={e.evidence_id:e for e in c.evidence}
        if any(i not in known or known[i].case_id!=c.case_id or known[i].case_version!=c.version for i in ids): raise ValueError('CROSS_CASE_OR_STALE_EVIDENCE')
    def update(self,cid,version,patch):
        if set(patch)-{'query','requester_role','subject_role','task_scene','fields','artifacts','jurisdiction','as_of'}:raise ValueError('PATCH_FORBIDDEN')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM cases WHERE id=?',(cid,)).fetchone()
            if not row or row['version']!=version: raise ValueError('STALE_VERSION')
            old=CaseRecord.model_validate_json(row['body'])
            c=CaseRecord.model_validate({**old.model_dump(),**patch,'version':version+1,'evidence':[],'status':'open','unresolved_questions':[]})
            if any(a.case_id!=cid for a in c.artifacts):raise ValueError('CROSS_CASE_ARTIFACT')
            db.execute('INSERT INTO history VALUES(?,?,?)',(cid,version,row['body']))
            db.execute('UPDATE cases SET version=?,body=? WHERE id=?',(c.version,c.model_dump_json(),cid))
        return c
    def finish(self,c,result):
        self.validate_evidence(c,[i for r in result.get('recommendations',[]) for i in r['supporting_evidence_ids']+r['counter_evidence_ids']])
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT version FROM cases WHERE id=?',(c.case_id,)).fetchone()
            if not row or row[0]!=c.version:raise ValueError('STALE_VERSION')
            db.execute('INSERT INTO results VALUES(?,?,?,?)',(result['run_id'],c.case_id,c.version,json.dumps(result,ensure_ascii=False)))
            db.execute('UPDATE cases SET body=? WHERE id=?',(c.model_dump_json(),c.case_id))
    def result(self,rid):
        with self.db() as db:r=db.execute('SELECT body FROM results WHERE id=?',(rid,)).fetchone()
        if not r:raise ValueError('RESULT_NOT_FOUND')
        return json.loads(r[0])
    def review(self,data):
        r=Review.model_validate(data)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            previous=db.execute('SELECT body FROM reviews WHERE id=?',(r.request_id,)).fetchone()
            if previous:
                if json.loads(previous[0])['request']!=r.model_dump():raise ValueError('IDEMPOTENCY_CONFLICT')
                return json.loads(previous[0])
            row=db.execute('SELECT body FROM cases WHERE id=?',(r.case_id,)).fetchone()
            if not row:raise ValueError('CASE_NOT_FOUND')
            c=CaseRecord.model_validate_json(row[0])
            result=db.execute('SELECT * FROM results WHERE id=?',(r.result_id,)).fetchone()
            if c.version!=r.case_version or not result or result['version']!=c.version or result['case_id']!=c.case_id:raise ValueError('STALE_OR_FOREIGN_RESULT')
            previous_reviews=[json.loads(x[0]) for x in db.execute('SELECT body FROM reviews')]
            if r.decision=='accept' and any(x['request']['result_id']==r.result_id and x['request']['decision']=='reject' for x in previous_reviews):raise ValueError('REJECTED_RESULT_REQUIRES_NEW_RUN')
            if r.decision=='accept' and json.loads(result['body'])['status']!='pending_review':raise ValueError('RESULT_NOT_REVIEWABLE')
            if r.decision=='revise' and not r.revisions:raise ValueError('REVISIONS_REQUIRED')
            self.validate_evidence(c,[i for x in r.revisions for i in x.supporting_evidence_ids+x.counter_evidence_ids])
            record={'request':r.model_dump(),'at':now(),'evidence_version_hash':digest([e.model_dump() for e in c.evidence]),'result_hash':digest(json.loads(result['body'])),'review_scope':'entire_original_result_including_answer_risks_steps_questions_boundaries_and_evidence' if r.decision!='revise' else 'human_recommendations_only_original_result_unchanged','identity_notice':'local operator name, not authenticated enterprise identity','revision_notice':'human-authored recommendation revision stored separately; original answer unchanged, not model validation'}
            db.execute('INSERT INTO reviews VALUES(?,?)',(r.request_id,json.dumps(record,ensure_ascii=False)))
        return record
    def export(self,cid):
        c=self.get(cid)
        with self.db() as db:
            results=[json.loads(x[0]) for x in db.execute('SELECT body FROM results WHERE case_id=?',(cid,))]
            reviews=[json.loads(x[0]) for x in db.execute('SELECT body FROM reviews') if json.loads(x[0])['request']['case_id']==cid]
        return {'case':c.model_dump(),'results':[{**r,'stale':r['case_version']!=c.version} for r in results],'reviews':reviews}
    def session(self,sid,body=None):
        with self.db() as db:
            if body is not None:db.execute('INSERT OR REPLACE INTO sessions VALUES(?,?)',(sid,json.dumps(body,ensure_ascii=False)));return body
            row=db.execute('SELECT body FROM sessions WHERE id=?',(sid,)).fetchone()
        if not row:raise ValueError('SESSION_NOT_FOUND')
        return json.loads(row[0])
