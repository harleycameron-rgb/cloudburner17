"""Application integration outside the engine: preloaded assets, pure research calls."""
import hashlib
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, RedirectResponse
if __package__:
    from .audit_geometry import geometry
    from .trajectory_contract import separate, trajectory
else:
    from audit_geometry import geometry
    from trajectory_contract import separate, trajectory

ROOT = Path(__file__).parent / 'portal'
ASSETS = {str(p.relative_to(ROOT)): p.read_text(encoding='utf-8') for p in ROOT.rglob('*') if p.is_file()}
router = APIRouter()
HEADERS = {'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Cache-Control':'no-store',
 'Permissions-Policy':'camera=(self), microphone=(), geolocation=()'}
CSP = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; frame-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'"

def asset(key):
    if key not in ASSETS: raise HTTPException(404,'Unknown application asset')
    suffix=key.rsplit('.',1)[-1]
    media={'html':'text/html','js':'text/javascript','css':'text/css','json':'application/json'}.get(suffix)
    if not media: raise HTTPException(404,'Unknown application asset')
    return Response(ASSETS[key],media_type=media,headers={**HEADERS,'Content-Security-Policy':CSP})

@router.get('/portal')
@router.get('/portal/')
async def portal(): return asset('hub/index.html')
@router.get('/terminal')
@router.get('/terminal/')
async def terminal(): return asset('terminal/index.html')
@router.get('/geometry.html')
async def geometry_page(): return asset('terminal/geometry.html')
@router.get('/modules/{name}')
async def legacy(name:str): return asset('terminal/modules/'+name)
@router.get('/audit')
@router.get('/audit/')
async def audit(): return asset('audit/index.html')
@router.get('/web/{name}')
async def audit_web(name:str): return asset('audit/web/'+name)
@router.get('/apps/{name}')
async def audit_apps(name:str): return asset('audit/apps/'+name)
@router.get('/audit.js')
async def audit_script(): return asset('audit/audit.js')
@router.get('/portal/{name}')
async def hub_asset(name:str): return asset('hub/'+name)
@router.get('/source-manifest.json')
async def manifest(): return asset('source-manifest.json')

@router.get('/api/tentacled-sphere')
async def preview_geometry(request:Request):
    try:
        values=[]
        for name,default in [('seed','1.0'),('delta','0.1137')]:
            if len(request.query_params.getlist(name))>1: raise ValueError('Duplicate parameter')
            values.append(float(request.query_params.get(name,default)))
        return geometry(*values)
    except (ValueError,OverflowError): raise HTTPException(422,'Finite seed and delta required')

@router.get('/integration/status')
async def integration_status():
    return {'schema':'waxtablet-integration/1','mode':'research','liveGate':'CLOSED','sphereWrites':False,
      'clients':{'terminal': '/terminal','audit':'/audit','supervisor':'/supervisor','scandoc':'/scandoc'},
      'geometryContracts':{'audit':'/api/tentacled-sphere','cloudburner':'/tentacled-sphere'},
      'trajectory':'/integration/research-run','assetsLoaded':len(ASSETS),'receiptTrust':'UNVERIFIED'}

@router.post('/integration/research-run')
async def research_run(request:Request):
    raw=await request.body()
    if len(raw)>1048576: raise HTTPException(413,'Maximum request size is 1 MiB')
    try:
        payload=json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
        if not isinstance(payload,dict) or set(payload)!={'legs','tolerance','samples'}: raise ValueError('Expected legs, tolerance and samples')
        if not isinstance(payload['samples'],list) or len(payload['samples'])>512: raise ValueError('Maximum 512 samples')
        separation=separate(payload['legs'],tolerance=payload['tolerance'])
        result=trajectory(separation,payload['samples'])
        record={'schema':'waxtablet-research-run/1','kind':'supplied-sample-research','separation':separation,'result':result,
          'liveGate':'CLOSED','sphereWrites':False,'receiptTrust':'UNVERIFIED','stored':False}
        canonical=json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        # Return the exact hashed bytes as text: Python and JavaScript serialize
        # floats differently (e.g. 1.0 vs 1). Consumers must check BOTH the
        # digest and equality of this record to the displayed envelope.
        return {**record,'canonicalRecord':canonical.decode('utf-8'),
          'sha512':hashlib.sha512(b'waxtablet-research-run/1\0'+canonical).hexdigest()}
    except (ValueError,TypeError,OverflowError,KeyError) as error:
        raise HTTPException(422,str(error)) from error
