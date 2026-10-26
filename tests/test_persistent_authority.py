import json
import multiprocessing as mp
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from infra.authority.store import Store, Rejected, FACES, P, canon, hashed, checked
H,V = 'a'*128,'b'*128
def yes(_): return {p:True for p in P}
def record(b,face='Tap',tick=0,event=None):
    r = {'outcome':'QUALIFIED','contract_id':'waxtablet.face-qualification','contract_version':'1.0.0',**b,'face_id':face,'event_id':event or 'event-'+face,'logical_tick':tick,'input_digest':H,'geometry_digest':H,'output_digest':H,'alternate_evidence_digest':H,'counter_evidence_digest':H,'validator_artifact_digest':V,'predicate_results':yes(None),'live_write_performed':False}
    return {**r,'face_commitment':hashed('waxtablet/face-qualification/1.0.0/'+face+'\0',r)}
class Held(Store):
    def _load(self,q,sid):
        row=super()._load(q,sid)
        self.entered.set()
        if not self.release.wait(8): raise RuntimeError('TEST_BARRIER_TIMEOUT')
        return row

def worker(location,backend,sid,operation,p,h,entered,release,attempted,out):
    store=Held(location,backend=backend);store.entered=entered;store.release=release
    attempted.set()
    try:
        result=store.commit(sid,p,writes_authorized=True) if operation=='commit' else store.change(sid,'revoked',h)
        out.put(('ok',result))
    except Exception as e: out.put(('error',str(e)))

class SQLiteTests(unittest.TestCase):
    backend='sqlite'
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.location=str(Path(self.temp.name)/'authority.db')
        if self.backend=='postgres':
            self.location=os.environ.get('WAXTABLET_TEST_POSTGRES_DSN','')
            if not self.location:self.skipTest('PostgreSQL test DSN not configured')
        self.b={'session_id':'s'+uuid.uuid4().hex,'qualification_epoch':'e1','origin_digest':H,'profile_digest':H}
        self.sid=self.b['session_id'];self.store=Store(self.location,backend=self.backend,evaluate=yes)
        self.store.migrate();self.store.create(self.b,[V]);self.records=[record(self.b,f) for f in FACES]
    def fill(self):
        for r in reversed(self.records):self.store.issue(r)
    def centers(self):
        with self.store._tx() as q:return int(q('SELECT center FROM waxtablet_authority_v1 WHERE session_id=?',(self.sid,)).fetchone()[0] is not None)
    def test_commit_retry(self):
        self.fill();p=self.store.prepare(self.sid)
        self.assertFalse(self.store.commit(self.sid,p,writes_authorized=True)['idempotent'])
        self.assertTrue(self.store.commit(self.sid,p,writes_authorized=True)['idempotent']);self.assertEqual(self.centers(),1)
    def test_no_write_default(self):
        self.fill();p=self.store.prepare(self.sid);self.assertEqual(self.centers(),0)
        with self.assertRaisesRegex(Rejected,'LIVE_WRITES_DISABLED'):self.store.commit(self.sid,p)
        self.assertEqual(self.centers(),0)
    def test_restart_replay(self):
        self.fill();fresh=Store(self.location,backend=self.backend,evaluate=yes)
        self.assertEqual(fresh.prepare(self.sid),self.store.prepare(self.sid))
        with self.assertRaisesRegex(Rejected,'REPLAY'):fresh.issue(self.records[0])
    def test_missing_face(self):
        for r in self.records[:-1]:self.store.issue(r)
        with self.assertRaisesRegex(Rejected,'MISSING_FACE:Business'):self.store.prepare(self.sid)
    def test_wrong_epoch(self):
        with self.assertRaisesRegex(Rejected,'BINDING_MISMATCH'):self.store.issue(record({**self.b,'qualification_epoch':'other'}))
    def test_independent_refusal(self):
        self.store.evaluate=lambda _: {**yes(None),'R':False}
        with self.assertRaisesRegex(Rejected,'INDEPENDENT_VALIDATION_FAILED'):self.store.issue(self.records[0])
    def test_evaluator_failure_rollback(self):
        def fail(_):raise RuntimeError('evidence unavailable')
        self.store.evaluate=fail
        with self.assertRaises(RuntimeError):self.store.issue(self.records[0])
        self.store.evaluate=yes;self.store.issue(self.records[0])
    def test_tampered_record(self):
        with self.assertRaisesRegex(Rejected,'COMMITMENT_MISMATCH'):self.store.issue({**self.records[0],'output_digest':'c'*128})
    def test_extra_field(self):
        with self.assertRaisesRegex(Rejected,'SCHEMA_INVALID'):self.store.issue({**self.records[0],'extra':True})
    def test_stale_tick(self):
        self.store.issue(self.records[0])
        with self.assertRaisesRegex(Rejected,'STALE_TICK'):self.store.issue(record(self.b,event='new'))
    def test_supersession(self):
        self.fill();p=self.store.prepare(self.sid);self.store.issue(record(self.b,tick=1,event='new'))
        with self.assertRaisesRegex(Rejected,'STALE_OR_TAMPERED'):self.store.commit(self.sid,p,writes_authorized=True)
    def test_revocation_restart(self):
        self.fill();self.store.change(self.sid,'revoked',self.records[0]['face_commitment'])
        with self.assertRaisesRegex(Rejected,'FACE_NOT_ACTIVE'):Store(self.location,backend=self.backend).prepare(self.sid)
    def test_terminal_status(self):
        self.fill();h=self.records[0]['face_commitment'];self.store.change(self.sid,'invalidated',h)
        with self.assertRaisesRegex(Rejected,'STATUS_TERMINAL'):self.store.change(self.sid,'revoked',h)
    def test_deactivation(self):
        self.fill();p=self.store.prepare(self.sid);self.store.change(self.sid,'deactivate')
        with self.assertRaisesRegex(Rejected,'SESSION_INACTIVE'):self.store.commit(self.sid,p,writes_authorized=True)
    def test_validator_withdrawal(self):
        self.fill();p=self.store.prepare(self.sid);self.store.change(self.sid,'withdraw',V)
        with self.assertRaisesRegex(Rejected,'VALIDATOR_NOT_APPROVED'):self.store.commit(self.sid,p,writes_authorized=True)
    def test_payload_tampering(self):
        self.fill();p=self.store.prepare(self.sid);p['payload']['origin_digest']='c'*128
        with self.assertRaisesRegex(Rejected,'STALE_OR_TAMPERED'):self.store.commit(self.sid,p,writes_authorized=True)
    def test_face_reorder(self):
        self.fill();p=self.store.prepare(self.sid);p['payload']['faces'].reverse()
        with self.assertRaisesRegex(Rejected,'STALE_OR_TAMPERED'):self.store.commit(self.sid,p,writes_authorized=True)
    def test_version_tampering(self):
        self.fill();p=self.store.prepare(self.sid);p['authority_version']+=1
        with self.assertRaisesRegex(Rejected,'STALE_OR_TAMPERED'):self.store.commit(self.sid,p,writes_authorized=True)
    def test_hash_tampering(self):
        self.fill();p=self.store.prepare(self.sid);p['center_digest']='c'*128
        with self.assertRaisesRegex(Rejected,'STALE_OR_TAMPERED'):self.store.commit(self.sid,p,writes_authorized=True)
    def test_one_center(self):
        self.fill();self.store.commit(self.sid,self.store.prepare(self.sid),writes_authorized=True)
        self.store.issue(record(self.b,tick=1,event='new'))
        with self.assertRaisesRegex(Rejected,'CENTER_ALREADY_COMMITTED'):self.store.commit(self.sid,self.store.prepare(self.sid),writes_authorized=True)
    def test_fixed_order(self):
        self.fill();self.assertEqual([x['face_id'] for x in self.store.prepare(self.sid)['payload']['faces']],list(FACES))
    def test_database_tampering(self):
        self.fill()
        with self.store._tx() as q:
            s,v,_=self.store._load(q,self.sid);s['records'][self.records[0]['face_commitment']]['record']['output_digest']='c'*128
            self.store._save(q,self.sid,s,v)
        with self.assertRaisesRegex(Rejected,'COMMITMENT_MISMATCH'):self.store.prepare(self.sid)
    def _race(self,first):
        self.fill();p=self.store.prepare(self.sid);ctx=mp.get_context('spawn')
        entered,release,attempt1,attempt2= [ctx.Event() for _ in range(4)]
        entered2,release2=ctx.Event(),ctx.Event();release2.set()
        out1,out2=ctx.Queue(),ctx.Queue();other='revoke' if first=='commit' else 'commit'
        common=(self.location,self.backend,self.sid)
        a=ctx.Process(target=worker,args=(*common,first,p,self.records[0]['face_commitment'],entered,release,attempt1,out1))
        b=ctx.Process(target=worker,args=(*common,other,p,self.records[0]['face_commitment'],entered2,release2,attempt2,out2))
        try:
            a.start();self.assertTrue(entered.wait(10));b.start();self.assertTrue(attempt2.wait(10))
            b.join(.2);self.assertTrue(b.is_alive(),'second operation bypassed lock')
            release.set();a.join(12);b.join(12);self.assertEqual(a.exitcode,0);self.assertEqual(b.exitcode,0)
            x,y=out1.get(timeout=2),out2.get(timeout=2);self.assertEqual(x[0],'ok')
            self.assertEqual(y[0],'error' if first=='revoke' else 'ok')
            self.assertEqual(self.centers(),0 if first=='revoke' else 1)
            with self.assertRaises(Rejected):self.store.commit(self.sid,p,writes_authorized=True)
        finally:
            release.set()
            for process in (a,b):
                if process.pid and process.is_alive():process.terminate();process.join()
            out1.close();out2.close()
    def test_concurrent_revoke_first(self):self._race('revoke')
    def test_concurrent_commit_first(self):self._race('commit')
    def test_wrong_origin(self):
        with self.assertRaisesRegex(Rejected,'BINDING_MISMATCH'):self.store.issue(record({**self.b,'origin_digest':'c'*128}))
    def test_missing_evaluator(self):
        with self.assertRaisesRegex(Rejected,'INDEPENDENT_VALIDATION_FAILED'):Store(self.location,backend=self.backend).issue(self.records[0])
    def test_reused_event_other_face(self):
        self.store.issue(self.records[0])
        with self.assertRaisesRegex(Rejected,'REPLAY'):self.store.issue(record(self.b,'Surface',event=self.records[0]['event_id']))
    def test_cross_session(self):
        self.fill()
        with self.assertRaisesRegex(Rejected,'SESSION_UNKNOWN'):self.store.commit('unknown',self.store.prepare(self.sid),writes_authorized=True)
    def test_nonfinite_tick(self):
        with self.assertRaisesRegex(Rejected,'SCHEMA_INVALID'):self.store.issue({**self.records[0],'logical_tick':float('nan')})
    def test_false_predicate(self):
        with self.assertRaisesRegex(Rejected,'SCHEMA_INVALID'):self.store.issue({**self.records[0],'predicate_results':{**yes(None),'A':False}})
class PostgreSQLTests(SQLiteTests):backend='postgres'
class EncodingTests(unittest.TestCase):
    def test_literal_pr1_vector(self):
        b={'session_id':'s1','qualification_epoch':'e1','origin_digest':H,'profile_digest':H}
        r=record(b,event='evt-Tap')
        self.assertEqual(r['face_commitment'],'85a4337093c5981439c80ed1d0278cf41987f1386f41adbbf9ee1f7c4d42a0609a66d204ea2b42e8b8fff4de683fcae7629f01f5135214ee2df75aea0ee71119')
        self.assertEqual(checked(r),r)
    def test_literal_center_vector(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(str(Path(d)/'vector.db'),evaluate=yes);s.migrate()
            b={'session_id':'s1','qualification_epoch':'e1','origin_digest':H,'profile_digest':H};s.create(b,[V])
            for f in FACES:s.issue(record(b,f))
            self.assertEqual(s.prepare('s1')['center_digest'],'6125d2c929bc27f1163cda0c2c8f291c7c935ad04535301ee9ecf142188b339c7a78ab77f58109cd76d7b53bdd41d02fb2209cef18506b815d699da815ff3c32')
    def test_boolean_tick_rejected(self):
        b={'session_id':'s1','qualification_epoch':'e1','origin_digest':H,'profile_digest':H}
        with self.assertRaisesRegex(Rejected,'SCHEMA_INVALID'):checked({**record(b),'logical_tick':True})
