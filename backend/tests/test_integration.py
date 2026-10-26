import subprocess,sys,textwrap
from pathlib import Path

def test_integrated_flow_under_real_zero_data_lifespan():
    code=r'''
import copy,hashlib,json,re
from fastapi.testclient import TestClient
from backend.main import app
from backend.integration_page import ASSETS
with TestClient(app) as c:
    home=c.get('/')
    assert home.status_code==200 and 'INTEGRATED RESEARCH WORKSPACE' in home.text
    assert c.get('/supervisor').status_code==200
    for path in ['/terminal','/geometry.html','/audit','/audit.js','/web/app.js','/web/audio.js','/web/protocol.js','/portal/app.js','/portal/style.css','/source-manifest.json']:
        assert c.get(path).status_code==200,path
    for name in ('tap','surface','spiritlevel','gain','habitat','time','space','lineage'):
        assert c.get('/apps/'+name+'.html').status_code==200
    assert c.get('/modules/TAP.html').status_code==200
    assert c.get('/portal/missing.js').status_code==404
    assert c.get('/integration/status').json()['assetsLoaded']>=31
    audit=c.get('/api/tentacled-sphere').json()
    assert len(audit['tentacles'])==8
    assert len(c.get('/tentacled-sphere').json())==8
    for query in ('seed=nan','delta=inf','seed=1&seed=2'):
        assert c.get('/api/tentacled-sphere?'+query).status_code==422
    payload={'legs':{name:[i*.01,0,0] for i,name in enumerate(('tap','surface','gain','habitat','engine','business'))},'tolerance':.5,'samples':[{'tick':0,'center':[0,0,0]},{'tick':1,'center':[.1,0,0]}]}
    d=c.post('/integration/research-run',json=payload)
    assert d.status_code==200,d.text
    d=d.json();digest=d.pop('sha512')
    assert digest==hashlib.sha512(b'waxtablet-research-run/1\0'.replace(b'\\0',b'\0')+json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert d['sphereWrites'] is False and d['receiptTrust']=='UNVERIFIED' and d['stored'] is False
    assert len(d['result']['trajectory'])==2
    assert c.post('/integration/research-run',json=payload).json()['sha512']==digest
    for transform in [lambda p:p['legs'].pop('tap'),lambda p:p['legs'].update(tap=[100,0,0]),lambda p:p.update(tolerance=True),lambda p:p['samples'][1].update(tick=0),lambda p:p.update(samples=[]),lambda p:p.update(extra=True)]:
        x=copy.deepcopy(payload);transform(x);assert c.post('/integration/research-run',json=x).status_code==422
    assert c.post('/integration/research-run',content='{"legs":NaN}').status_code==422
    assert c.post('/integration/research-run',content='x'*1048577).status_code==413
print('integration checked with lifespan and no live writes')
'''
    result=subprocess.run([sys.executable,'-B','-c',textwrap.dedent(code)],cwd=Path(__file__).resolve().parents[2],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
