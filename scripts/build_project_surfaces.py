"""Prepare reproducible Vercel mirror payloads without network or credentials."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(kind):
 root=ROOT/'backend/portal'/kind
 files=[{'file':str(p.relative_to(root)),'data':p.read_text(),'encoding':'utf-8'} for p in sorted(root.rglob('*')) if p.is_file()]
 files.append({'file':'source-manifest.json','data':(ROOT/'backend/portal/source-manifest.json').read_text(),'encoding':'utf-8'})
 redirects=[{'source':'/portal','destination':'https://waxtablet.co.uk/portal','permanent':False}]
 name='waxtablet-null-terminal' if kind=='terminal' else 'waxtablet-integration-audit'
 redirects.append({'source':'/terminal' if kind=='terminal' else '/audit','destination':'/','permanent':False})
 if kind=='terminal':redirects.append({'source':'/audit','destination':'https://waxtablet.co.uk/audit','permanent':False})
 else:files += [{'file':'api/tentacled-sphere.py','data':(ROOT/'backend/audit_geometry.py').read_text(),'encoding':'utf-8'},{'file':'requirements.txt','data':'','encoding':'utf-8'}]
 config={'version':2,'buildCommand':'','installCommand':'','outputDirectory':'.','redirects':redirects,'headers':[{'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'},{'key':'Referrer-Policy','value':'no-referrer'},{'key':'Permissions-Policy','value':'camera=(self), microphone=(), geolocation=()'}]}]}
 config['headers'][0]['headers'].append({'key':'Content-Security-Policy','value':"default-src 'self'; script-src 'self'"+(" 'unsafe-inline'" if kind=='terminal' else '')+"; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; frame-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'"})
 files.append({'file':'vercel.json','data':json.dumps(config),'encoding':'utf-8'})
 return {'name':name,'project':name,'files':files,'projectSettings':{'framework':None,'buildCommand':'','installCommand':'','outputDirectory':'.','rootDirectory':None,'skipGitConnectDuringLink':True}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();a.directory.mkdir(parents=True,exist_ok=True)
 for kind in ('terminal','audit'):(a.directory/(kind+'.json')).write_text(json.dumps(build(kind)))
