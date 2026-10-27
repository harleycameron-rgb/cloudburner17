import copy
import hashlib
import json
import pytest
from backend.research_receipt import build_record, canonical, DOMAIN, strict_json, verify_research_receipt


def envelope(record):
    text=canonical(record)
    return {**record,'canonicalRecord':text,'sha512':hashlib.sha512(DOMAIN+text.encode()).hexdigest()}


def record():
    return json.loads(canonical(build_record(
        {name:[i*.01,0,0] for i,name in enumerate(('tap','surface','gain','habitat','engine','business'))},
        .5,[{'tick':0,'center':[0,0,0]},{'tick':1,'center':[.1,0,0]}])))


def test_replay_matches_real_generated_record():
    result=verify_research_receipt(envelope(record()))
    assert result['replayConsistent'] and result['contentIntegrity']
    assert result['receiptTrust']=='UNVERIFIED' and result['liveGate']=='CLOSED'
    assert result['sphereWrites'] is False and result['stored'] is False


@pytest.mark.parametrize('mutate',[
    lambda r:r['separation'].update(center=[99,0,0]),
    lambda r:r['result'].update(separationCommitment='0'*128),
    lambda r:r['result'].update(origin=[0,0,0]),
    lambda r:r.update(liveGate='OPEN'),
    lambda r:r.update(sphereWrites=0),
    lambda r:r['result'].update(temporal_tentacles=['past','future','extra']),
    lambda r:r['separation']['separationInputs'].pop('tap'),
    lambda r:r['result']['trajectory'][1].__setitem__(0,0),
])
def test_rehashed_inconsistent_record_rejected(mutate):
    r=record();mutate(r)
    with pytest.raises(ValueError): verify_research_receipt(envelope(r))


def test_display_and_digest_tampering_rejected():
    r=envelope(record());r['result']['origin']=[0,0,0]
    with pytest.raises(ValueError): verify_research_receipt(r)
    r=envelope(record());r['sha512']='0'*128
    with pytest.raises(ValueError): verify_research_receipt(r)


def test_ambiguous_json_rejected():
    for text in ('{"legs":{},"legs":{}}','{"x":NaN}'):
        with pytest.raises(ValueError): strict_json(text)
