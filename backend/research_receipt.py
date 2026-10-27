"""Replay unsigned research evidence. No authentication, persistence or firing."""
import hashlib
import hmac
import json
if __package__:
    from .trajectory_contract import separate, trajectory
else:
    from trajectory_contract import separate, trajectory

DOMAIN = b'waxtablet-research-run/1\0'
MAX_BYTES = 2 * 1024 * 1024
FIELDS = {'schema','kind','separation','result','liveGate','sphereWrites','receiptTrust','stored'}


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Nonfinite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def build_record(legs, tolerance, samples):
    separation = separate(legs, tolerance=tolerance)
    return {'schema':'waxtablet-research-run/1','kind':'supplied-sample-research',
            'separation':separation,'result':trajectory(separation,samples),
            'liveGate':'CLOSED','sphereWrites':False,'receiptTrust':'UNVERIFIED','stored':False}


def verify_research_receipt(receipt):
    if not isinstance(receipt, dict) or set(receipt) != FIELDS | {'canonicalRecord','sha512'}:
        raise ValueError('Unsupported receipt envelope')
    text, digest = receipt['canonicalRecord'], receipt['sha512']
    if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Invalid canonical record')
    if not isinstance(digest, str) or len(digest) != 128:
        raise ValueError('Invalid research digest')
    expected_hash = hashlib.sha512(DOMAIN + text.encode('utf-8')).hexdigest()
    if not hmac.compare_digest(expected_hash, digest):
        raise ValueError('Receipt SHA-512 mismatch')
    record = strict_json(text)
    displayed = {key:receipt[key] for key in FIELDS}
    # JSON comparison distinguishes false from 0 and arrays from objects.
    if canonical(record) != canonical(displayed):
        raise ValueError('Receipt differs from canonical record')
    try:
        separation, result = record['separation'], record['result']
        points = result['trajectory']
        if not isinstance(points, list) or not 2 <= len(points) <= 512:
            raise ValueError('Invalid trajectory sample count')
        samples = []
        for point in points:
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError('Invalid trajectory sample')
            samples.append({'tick':point[0], 'center':point[1]})
        replay = build_record(separation['separationInputs'], separation['separationTolerance'], samples)
        if canonical(replay) != canonical(record):
            raise ValueError('Research replay mismatch')
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Malformed research record') from error
    return {'schema':'waxtablet-research-verification/1','contentIntegrity':True,
            'replayConsistent':True,'sha512':digest,'receiptTrust':'UNVERIFIED',
            'liveGate':'CLOSED','sphereWrites':False,'stored':False}
