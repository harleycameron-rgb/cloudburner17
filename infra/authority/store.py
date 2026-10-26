"""Opt-in infrastructure authority, never imported by the zero-data engine."""
import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager

FACES = ('Tap', 'Surface', 'Gain', 'Habitat', 'Engine', 'Business')
P = set('SBFG RACP'.replace(' ', ''))
B = ('session_id', 'qualification_epoch', 'origin_digest', 'profile_digest')
D = ('origin_digest', 'profile_digest', 'input_digest', 'geometry_digest', 'output_digest', 'alternate_evidence_digest', 'counter_evidence_digest', 'validator_artifact_digest')
FIELDS = {'outcome', 'contract_id', 'contract_version', *B, 'face_id', 'event_id', 'logical_tick', *D, 'predicate_results', 'live_write_performed', 'face_commitment'}
class Rejected(ValueError): pass

def canon(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
def hashed(prefix, x):
    return hashlib.sha512((prefix + canon(x)).encode()).hexdigest()
def hexdigest(x):
    return type(x) is str and re.fullmatch('[0-9a-f]{128}', x) is not None
def identifier(x):
    return type(x) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', x) is not None
def predicates(x):
    return type(x) is dict and set(x) == P and all(v is True for v in x.values())
def checked(r):
    if type(r) is not dict or set(r) != FIELDS: raise Rejected('SCHEMA_INVALID')
    if (r['outcome'] != 'QUALIFIED' or r['contract_id'] != 'waxtablet.face-qualification' or r['contract_version'] != '1.0.0'
        or r['face_id'] not in FACES or not all(identifier(r[k]) for k in ('session_id','qualification_epoch','event_id'))
        or not all(hexdigest(r[k]) for k in (*D,'face_commitment')) or type(r['logical_tick']) is not int
        or not 0 <= r['logical_tick'] <= 2**53-1 or r['live_write_performed'] is not False or not predicates(r['predicate_results'])):
        raise Rejected('SCHEMA_INVALID')
    body = {k:v for k,v in r.items() if k != 'face_commitment'}
    if hashed('waxtablet/face-qualification/1.0.0/'+r['face_id']+'\0',body) != r['face_commitment']: raise Rejected('COMMITMENT_MISMATCH')
    return json.loads(canon(r))

class Store:
    """Trusted management capability. Do not expose this object as a public API."""
    def __init__(self, location, *, backend='sqlite', evaluate=None):
        if backend not in ('sqlite','postgres') or not location or location == ':memory:': raise ValueError('PERSISTENT_DATABASE_REQUIRED')
        self.location, self.backend, self.evaluate = location, backend, evaluate
    @contextmanager
    def _tx(self):
        if self.backend == 'sqlite': db = sqlite3.connect(self.location, timeout=10, isolation_level=None)
        else:
            import psycopg2
            db = psycopg2.connect(self.location, connect_timeout=10)
            db.set_session(isolation_level='READ COMMITTED', readonly=False, autocommit=False)
        c = db.cursor()
        try:
            if self.backend == 'sqlite':
                c.execute('PRAGMA synchronous=FULL'); c.execute('BEGIN IMMEDIATE')
            else: c.execute("SET LOCAL lock_timeout = '10s'")
            def q(sql, args=()):
                c.execute(sql.replace('?', '%s') if self.backend == 'postgres' else sql, args)
                return c
            yield q
            db.commit()
        except BaseException:
            db.rollback(); raise
        finally: c.close(); db.close()
    def migrate(self):
        with self._tx() as q:
            q('CREATE TABLE IF NOT EXISTS waxtablet_authority_v1 (session_id TEXT PRIMARY KEY, state TEXT NOT NULL, version BIGINT NOT NULL CHECK(version>=0), center TEXT)')
    def create(self, bindings, validators):
        if (type(bindings) is not dict or set(bindings) != set(B) or not all(identifier(bindings[k]) for k in B[:2])
            or not all(hexdigest(bindings[k]) for k in B[2:]) or type(validators) is not list or not validators or not all(hexdigest(v) for v in validators)):
            raise Rejected('BINDINGS_INVALID')
        state = {'bindings':dict(bindings),'validators':sorted(set(validators)),'active':True,'records':{},'selected':{},'events':{},'ticks':{}}
        with self._tx() as q:
            q('INSERT INTO waxtablet_authority_v1 VALUES (?, ?, 0, NULL)', (bindings['session_id'],canon(state)))
    def _load(self, q, sid):
        suffix = ' FOR UPDATE' if self.backend == 'postgres' else ''
        row = q('SELECT state,version,center FROM waxtablet_authority_v1 WHERE session_id=?'+suffix,(sid,)).fetchone()
        if not row: raise Rejected('SESSION_UNKNOWN')
        state = json.loads(row[0])
        if state['bindings']['session_id'] != sid: raise Rejected('STORED_BINDING_MISMATCH')
        return state,row[1],row[2]
    def _save(self, q, sid, s, version):
        changed = q('UPDATE waxtablet_authority_v1 SET state=?,version=version+1 WHERE session_id=? AND version=?',(canon(s),sid,version)).rowcount
        if changed != 1: raise Rejected('VERSION_CONFLICT')
    def issue(self, record):
        r = checked(record); sid = r['session_id']; face = r['face_id']
        with self._tx() as q:
            s,v,_ = self._load(q,sid)
            if not s['active']: raise Rejected('SESSION_INACTIVE')
            if any(r[k] != s['bindings'][k] for k in B): raise Rejected('BINDING_MISMATCH')
            if r['validator_artifact_digest'] not in s['validators']: raise Rejected('VALIDATOR_NOT_APPROVED')
            if r['event_id'] in s['events']: raise Rejected('REPLAY')
            if r['logical_tick'] <= s['ticks'].get(face,-1): raise Rejected('STALE_TICK')
            if len(s['records']) >= 10000: raise Rejected('SESSION_CAPACITY_REACHED')
            if not callable(self.evaluate) or not predicates(self.evaluate(json.loads(canon(r)))): raise Rejected('INDEPENDENT_VALIDATION_FAILED')
            old = s['selected'].get(face)
            if old: s['records'][old]['status'] = 'superseded'
            s['records'][r['face_commitment']] = {'record':r,'status':'active'}
            s['selected'][face] = r['face_commitment']; s['events'][r['event_id']] = True; s['ticks'][face] = r['logical_tick']
            self._save(q,sid,s,v)
        return r['face_commitment']
    def change(self, sid, operation, value=None):
        with self._tx() as q:
            s,v,_ = self._load(q,sid)
            if operation in ('revoked','invalidated'):
                entry = s['records'].get(value)
                if not entry or entry['status'] != 'active': raise Rejected('STATUS_TERMINAL_OR_UNKNOWN')
                entry['status'] = operation
            elif operation == 'deactivate': s['active'] = False
            elif operation == 'withdraw':
                if value not in s['validators']: raise Rejected('VALIDATOR_UNKNOWN')
                s['validators'].remove(value)
            else: raise Rejected('OPERATION_INVALID')
            self._save(q,sid,s,v)
    def _proposal(self, s, version):
        if not s['active']: raise Rejected('SESSION_INACTIVE')
        faces = []
        for face in FACES:
            key = s['selected'].get(face); entry = s['records'].get(key)
            if not entry: raise Rejected('MISSING_FACE:'+face)
            if entry['status'] != 'active': raise Rejected('FACE_NOT_ACTIVE:'+face)
            r = checked(entry['record'])
            if r['face_commitment'] != key or r['face_id'] != face or any(r[k] != s['bindings'][k] for k in B): raise Rejected('STORED_BINDING_MISMATCH')
            if r['validator_artifact_digest'] not in s['validators']: raise Rejected('VALIDATOR_NOT_APPROVED')
            faces.append({'face_id':face,'face_commitment':key})
        payload = {'domain':'waxtablet/center-commitment/1.0.0',**s['bindings'],'faces':faces}
        return {'outcome':'PREPARED','authority_version':version,'payload':payload,'center_digest':hashed('waxtablet/center-commitment/1.0.0\0',payload)}
    def prepare(self, sid):
        with self._tx() as q:
            s,v,_ = self._load(q,sid)
            return self._proposal(s,v)
    def commit(self, sid, proposal, *, writes_authorized=False):
        if writes_authorized is not True: raise Rejected('LIVE_WRITES_DISABLED')
        proposal = canon(proposal)
        with self._tx() as q:
            s,v,existing = self._load(q,sid); current = self._proposal(s,v)
            if proposal != canon(current): raise Rejected('STALE_OR_TAMPERED_PROPOSAL')
            receipt = canon({'center_digest':current['center_digest'],'payload':current['payload'],'authority_version':v})
            if existing is not None and existing != receipt: raise Rejected('CENTER_ALREADY_COMMITTED')
            if existing is None: q('UPDATE waxtablet_authority_v1 SET center=? WHERE session_id=?',(receipt,sid))
            return {'outcome':'COMMITTED','center_digest':current['center_digest'],'idempotent':existing is not None}
