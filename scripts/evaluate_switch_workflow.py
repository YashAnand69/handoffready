#!/usr/bin/env python3
"""Freeze and execute assistant-authored synthetic workflow regressions.

No model/provider calls, live room access, credentials or human observations.
Run `freeze /absolute/external/path` before `run /absolute/external/path`.
Every execution uses an immutable backend snapshot and a new isolated data tree.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time
import traceback
import zlib

ROOT = Path(__file__).resolve().parents[1]
NOTICE = 'Assistant-authored fresh synthetic regression; not independently held-out, human judgment, model accuracy or live Switch evidence.'
NEEDLE = 'RELEASE-NOTE-CEDAR'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode() + b'\n'


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as target:
        target.write(content)
    path.chmod(0o444)


def png(width, height):
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    pixels = (b'\x00' + bytes([51, 102, 153, 255]) * width) * height
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(pixels, 9)) + chunk(b'IEND', b'')


def requirement(identity, title, checks):
    return {'id': identity, 'title': title, 'origin': 'human_added', 'quote': None, 'source_id': None,
            'human_note': 'Assistant-authored synthetic requirement; this API origin label is not evidence of human authorship.', 'checks': checks}


def suite():
    art = requirement('art', 'Synthetic 4 by 4 artwork', [{'kind': 'presence', 'types': ['png']}, {'kind': 'image_dimensions', 'width_px': 4, 'height_px': 4}])
    guide = requirement('guide', 'Synthetic release guide', [{'kind': 'presence', 'types': ['text']}, {'kind': 'literal_text', 'needle': NEEDLE}])
    good = (NEEDLE + ': install the supplied synthetic artwork.\n').encode()
    common = {'art.png': png(4, 4), 'guide.txt': good}
    return [
        {'id': 'complete-assets', 'family': 'complete assets', 'files': common, 'requirements': [art, guide],
         'mapping': {'art': ['art.png'], 'guide': ['guide.txt']}, 'disposition': 'satisfied',
         'expected': {'inspection': {'art.png': 'inspected', 'guide.txt': 'inspected'}, 'checks': {'art': ['pass', 'pass'], 'guide': ['pass', 'pass']}, 'status': 'reviewed'}},
        {'id': 'duplicate-wrong-size', 'family': 'exact duplicates and wrong dimensions',
         'files': {'banner-a.png': png(8, 4), 'banner-b.png': png(8, 4), 'guide.txt': good},
         'requirements': [requirement('art', 'Two distinct 4 by 4 PNGs', [{'kind': 'count', 'types': ['png'], 'comparison': 'exact', 'value': 2, 'distinct_bytes': True}, {'kind': 'image_dimensions', 'width_px': 4, 'height_px': 4}]), guide],
         'mapping': {'art': ['banner-a.png', 'banner-b.png'], 'guide': ['guide.txt']}, 'disposition': 'satisfied',
         'expected': {'inspection': {'banner-a.png': 'inspected', 'banner-b.png': 'inspected', 'guide.txt': 'inspected'}, 'checks': {'art': ['fail', 'fail'], 'guide': ['pass', 'pass']}, 'status': 'draft_with_gaps'}},
        {'id': 'irrelevant-same-name', 'family': 'irrelevant same-name guide',
         'files': {'art.png': png(4, 4), 'guide.txt': b'A synthetic tea recipe: warm water and steep leaves.\n'},
         'requirements': [art, guide], 'mapping': {'art': ['art.png'], 'guide': ['guide.txt']}, 'disposition': 'satisfied',
         'expected': {'inspection': {'art.png': 'inspected', 'guide.txt': 'inspected'}, 'checks': {'art': ['pass', 'pass'], 'guide': ['pass', 'fail']}, 'status': 'draft_with_gaps'}},
        {'id': 'ambiguous-manual', 'family': 'ambiguous scope and manual uncertainty',
         'files': {'guide.txt': b'Please make this feel spacious; exact spacing is unspecified.\n'},
         'requirements': [requirement('scope', 'Spacing needs a local judgment', [{'kind': 'manual', 'instruction': 'Decide what spacious means after checking the agreed source.'}])],
         'mapping': {'scope': ['guide.txt']}, 'disposition': 'unresolved',
         'context': {'question': 'Which spacing interpretation is intended? [synthetic private question]',
                     'reply': 'The teammate says approved, but this is an unverified synthetic scope claim.'},
         'expected': {'inspection': {'guide.txt': 'inspected'}, 'checks': {'scope': ['unknown']}, 'status': 'draft_with_gaps', 'context_hold': True}},
        {'id': 'malformed-unsupported', 'family': 'malformed and unsupported input',
         'files': {'broken.png': b'\x89PNG\r\n\x1a\ncorrupt synthetic body', 'archive.bin': b'unsupported synthetic archive bytes'},
         'requirements': [art], 'mapping': {'art': ['broken.png']}, 'disposition': None,
         'expected': {'inspection': {'broken.png': 'blocked', 'archive.bin': 'blocked'}, 'packet_error': 'delivery_inspection_failed', 'committed_files': 0, 'export_error': 'delivery_hold'}},
        {'id': 'corrected-packet', 'family': 'revised packet after review and immutable export',
         'files': {'guide.txt': good}, 'replacement_files': {'guide.txt': (NEEDLE + ': corrected installation order; use the new artwork first.\n').encode()},
         'requirements': [guide], 'mapping': {'guide': ['guide.txt']}, 'disposition': 'satisfied',
         'expected': {'inspection': {'guide.txt': 'inspected'}, 'checks': {'guide': ['pass', 'pass']}, 'status': 'reviewed', 'correction_stales': True, 'historical_export_unchanged': True}},
    ]


def external(path):
    path = Path(path).expanduser().resolve()
    if not path.is_absolute() or path == ROOT or ROOT in path.parents:
        raise ValueError('Choose an absolute artifact folder outside the repository.')
    return path


def freeze(base):
    base = external(base)
    base.mkdir(mode=0o700, parents=True, exist_ok=False)
    frozen = base / 'frozen'
    sources = {}
    source_paths = [*sorted((ROOT / 'backend' / 'handoffready').glob('*.py')), ROOT / 'scripts' / 'evaluate_switch_workflow.py']
    for source in source_paths:
        relative = source.relative_to(ROOT).as_posix()
        raw = source.read_bytes()
        write_new(frozen / 'candidate' / relative, raw)
        sources[relative] = sha(raw)
    cases = []
    for case in suite():
        case = dict(case)
        for key in ('files', 'replacement_files'):
            if key not in case:
                continue
            records = []
            for name, raw in case[key].items():
                path = f'inputs/{case["id"]}/{key}/{name}'
                write_new(frozen / path, raw)
                records.append({'name': name, 'path': path, 'sha256': sha(raw), 'bytes': len(raw)})
            case[key] = records
        case['operation_keys'] = {'create': f'{case["id"]}-create', 'packet': f'{case["id"]}-packet-v1', 'replacement': f'{case["id"]}-packet-v2',
                                  'question': f'{case["id"]}-question', 'reply': f'{case["id"]}-reply',
                                  'stage_v1': [f'{case["id"]}-v1-{index}' for index in range(len(case['files']))],
                                  'stage_v2': [f'{case["id"]}-v2-{index}' for index in range(len(case.get('replacement_files', [])))]}
        cases.append(case)
    versions = {name: importlib.metadata.version(name) for name in ('fastapi', 'starlette', 'httpx', 'pydantic', 'pillow', 'pypdf', 'psutil')}
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    manifest = {'schema_version': 1, 'notice': NOTICE, 'frozen_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'git_base_head': git, 'candidate_identity': 'Exact source fingerprints; working tree candidate is not claimed as a commit.',
                'python': platform.python_version(), 'dependencies': versions, 'source_sha256': sources,
                'source_fingerprint': sha(encoded(sources)), 'cases': cases,
                'not_run': ['model extraction', 'model evidence association', 'live Switch transport', 'independent human review', 'usability or timing study']}
    raw = encoded(manifest)
    write_new(frozen / 'manifest.json', raw)
    write_new(frozen / 'manifest.sha256', (sha(raw) + '\n').encode())
    print(json.dumps({'frozen_manifest': str(frozen / 'manifest.json'), 'manifest_sha256': sha(raw), 'source_fingerprint': manifest['source_fingerprint'], 'case_count': len(cases)}))


def run(base):
    base = external(base)
    frozen = base / 'frozen'
    raw = (frozen / 'manifest.json').read_bytes()
    if sha(raw) != (frozen / 'manifest.sha256').read_text().strip():
        raise ValueError('Frozen manifest changed.')
    manifest = json.loads(raw)
    for name, version in manifest['dependencies'].items():
        if importlib.metadata.version(name) != version:
            raise ValueError('Frozen dependency version changed.')
    for relative, expected in manifest['source_sha256'].items():
        if sha((frozen / 'candidate' / relative).read_bytes()) != expected:
            raise ValueError('Frozen candidate changed.')
    runner = 'scripts/evaluate_switch_workflow.py'
    if sha(Path(__file__).read_bytes()) != manifest['source_sha256'][runner]:
        raise ValueError('Run the frozen runner or freeze a new candidate after changing the runner.')
    for case in manifest['cases']:
        for key in ('files', 'replacement_files'):
            for row in case.get(key, []):
                if sha((frozen / row['path']).read_bytes()) != row['sha256']:
                    raise ValueError('Frozen input changed.')
    # Put the exact frozen source first, including parser worker imports.
    sys.path.insert(0, str(frozen / 'candidate' / 'backend'))
    from fastapi.testclient import TestClient
    from handoffready.api import create_app, inspect_bounded
    from handoffready.store import input_hash
    from handoffready.delivery_context import context_hold
    started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    runs = base / 'runs'
    runs.mkdir(exist_ok=True)
    number = 1
    while (runs / f'run-{number:02}').exists():
        number += 1
    output = runs / f'run-{number:02}'
    output.mkdir(mode=0o700)
    results = {'notice': NOTICE, 'started_at': started, 'run_number': number, 'manifest_sha256': sha(raw), 'source_fingerprint': manifest['source_fingerprint'], 'cases': []}
    for case in manifest['cases']:
        record = {'id': case['id'], 'family': case['family'], 'checks': [], 'parser_facts': [], 'api_trace': [], 'model_extraction': 'not run',
                  'evidence_association': 'authored file mapping, not a model prediction', 'local_review': 'scripted assistant-authored synthetic actions, not human observations'}
        results['cases'].append(record)
        def check(name, actual, expected):
            record['checks'].append({'name': name, 'actual': actual, 'expected': expected, 'passed': actual == expected})
        def data(response):
            if response.status_code not in {200, 201, 202}:
                raise RuntimeError(f'Unexpected API status {response.status_code}: {response.text}')
            return response.json()['data']
        try:
            directory = output / case['id']
            directory.mkdir(mode=0o700)
            config = {'binding_id': 'synthetic-evaluation', 'server': 'http://127.0.0.1:8877', 'room': 'synthetic-' + case['id'], 'token': 'synthetic-evaluation-token-not-an-account-secret'}
            app = create_app(directory / 'data', delivery_config=config)
            with TestClient(app, base_url='http://127.0.0.1:8877') as client:
                token = data(client.get('/api/v1/bootstrap'))['token']
                client.headers.update({'X-Handoff-Token': token, 'Origin': 'http://127.0.0.1:8877'})
                def request(method, path, payload=None, revision=None):
                    headers = {'If-Match': str(revision)} if revision is not None else {}
                    response = client.request(method, path, json=payload, headers=headers)
                    record['api_trace'].append({'method': method, 'path': path, 'status': response.status_code,
                                                'error_code': response.json().get('error', {}).get('code') if response.headers.get('content-type', '').startswith('application/json') else None})
                    return response
                project = data(request('POST', '/api/v1/projects', {'name': 'Assistant synthetic: ' + case['id']}))
                project_id = project['id']
                prefix = f'/api/v1/projects/{project_id}'
                project = data(request('PUT', prefix + '/brief', {'text': 'Assistant-authored synthetic brief. No private client data. ' + case['family'], 'source_label': 'Synthetic evaluation'}, project['revision']))
                project = data(request('PUT', prefix + '/baseline', {'requirements': case['requirements']}, project['revision']))
                project = data(request('POST', prefix + '/baseline/approve', {'baseline_hash': project['baseline']['hash'], 'reviewed_requirement_ids': [r['id'] for r in case['requirements']]}, project['revision']))
                job_id = data(request('POST', '/api/v1/delivery/jobs', {'project_id': project_id, 'operation_key': case['operation_keys']['create']}))['result']['job_id']
                service = app.state.delivery_service
                # The service exposes the configured binding through this immutable value.
                from handoffready.delivery import DeliveryBinding
                binding = DeliveryBinding(config['server'], config['room'])
                def fresh():
                    return data(request('GET', prefix))
                def stage(rows, version):
                    ids = []
                    for index, row in enumerate(rows):
                        raw_input = (frozen / row['path']).read_bytes()
                        source_id = case['operation_keys']['stage_' + version][index]
                        payload = {'source_id': source_id, 'filename': row['name'], 'content': raw_input}
                        first = service.stage_receipt(job_id, binding, source_id, **payload)
                        check(f'{version} receipt {index} replay stable', service.stage_receipt(job_id, binding, source_id, **payload), first)
                        ids.append(first['result']['receipt_id'])
                    return ids
                def packet(rows, version):
                    ids = stage(rows, version)
                    p = app.state.store.get(project_id)
                    preview = service.preview_packet(job_id, binding, receipt_ids=ids, expected_revision=p['revision'], expected_hash=input_hash(p))
                    key = case['operation_keys']['packet' if version == 'v1' else 'replacement']
                    result = service.confirm_packet(job_id, binding, key, receipt_ids=ids, expected_revision=p['revision'], expected_hash=input_hash(p), manifest_hash=preview['manifest_hash'], inspect_file=inspect_bounded)
                    return result
                for row in case['files']:
                    fact = inspect_bounded(frozen / row['path'], row['name'], time.monotonic() + 30)
                    record['parser_facts'].append({'name': row['name'], 'sha256': row['sha256'], **fact})
                    check(row['name'] + ' inspection', fact['inspection'], case['expected']['inspection'][row['name']])
                    if fact['inspection'] == 'blocked':
                        check(row['name'] + ' blocked retains no partial evidence', [fact['metadata'], fact['text']], [{}, ''])
                if 'packet_error' in case['expected']:
                    try:
                        packet(case['files'], 'v1')
                        error_code = None
                    except Exception as error:
                        error_code = getattr(error, 'code', type(error).__name__)
                    check('complete packet refused', error_code, case['expected']['packet_error'])
                    project = fresh()
                    check('blocked packet committed file count', len(project['files']), case['expected']['committed_files'])
                    response = request('POST', prefix + '/exports', {'acknowledge_unresolved': True, 'input_hash': project['input_hash']}, project['revision'])
                    check('blocked intake cannot export', response.json().get('error', {}).get('code'), case['expected']['export_error'])
                    record['workflow_outcome'] = 'Expected safe refusal; packet remains pending, not completed.'
                    continue
                packet(case['files'], 'v1')
                project = fresh()
                def assess(p, key='initial'):
                    names = {f['name']: f['id'] for f in p['files']}
                    for requirement_id, selected_names in case['mapping'].items():
                        ids = [names[name] for name in selected_names]
                        preview = data(request('POST', prefix + f'/requirements/{requirement_id}/check-preview', {'file_ids': ids, 'input_hash': p['input_hash']}, p['revision']))
                        check(key + ' ' + requirement_id + ' provisional facts', [c['status'] for c in preview['checks']], case['expected']['checks'][requirement_id])
                        p = data(request('PUT', prefix + f'/decisions/{requirement_id}', {'file_ids': ids, 'review_state': 'confirmed', 'human_disposition': case['disposition'],
                                          'internal_decision_note': 'ASSISTANT SYNTHETIC REVIEW ACTION; no human judgment observed.', 'client_usage_note': '', 'input_hash': p['input_hash']}, p['revision']))
                    return p
                project = assess(project)
                check('saved summary status', project['attention_summary']['status'], case['expected']['status'])
                for requirement_id, statuses in case['expected']['checks'].items():
                    check(requirement_id + ' saved technical facts', [c['status'] for c in project['checks'] if c['requirement_id'] == requirement_id], statuses)
                if case['id'] == 'duplicate-wrong-size':
                    check('two filenames have exact identical bytes', len({f['sha256'] for f in project['files'] if f['type'] == 'png'}), 1)
                    check('decoded wrong dimensions', [(f['metadata']['width_px'], f['metadata']['height_px']) for f in project['files'] if f['type'] == 'png'], [(8, 4), (8, 4)])
                if case.get('context'):
                    context = service.context.read_project(project_id)
                    q = data(request('POST', f'/api/v1/delivery/jobs/{job_id}/questions', {'operation_key': case['operation_keys']['question'], 'expected_revision': project['revision'], 'input_hash': project['input_hash'],
                                     'expected_context_epoch': context['context_epoch'], 'requirement_id': 'scope', 'file_ids': [f['id'] for f in project['files']], 'question': case['context']['question'], 'source_ref': 'synthetic:context-question'}))
                    question_id = q['result']['question_id']
                    data(request('POST', f'/api/v1/delivery/jobs/{job_id}/questions/{question_id}/replies', {'operation_key': case['operation_keys']['reply'], 'question_input_hash': project['input_hash'], 'source_ref': 'synthetic:context-reply', 'reported_speaker': 'Assistant-authored synthetic teammate', 'text': case['context']['reply']}))
                    status = data(request('GET', f'/api/v1/delivery/jobs/{job_id}/status'))
                    check('question text absent from status', case['context']['question'] in json.dumps(status), False)
                    check('reply text absent from status', case['context']['reply'] in json.dumps(status), False)
                    with app.state.store.connection() as db:
                        check('unresolved context holds project', context_hold(db, project_id)['blocked'], True)
                    response = request('POST', prefix + '/exports', {'acknowledge_unresolved': True, 'input_hash': project['input_hash']}, project['revision'])
                    check('quoted approval cannot authorize record', response.json().get('error', {}).get('code'), 'delivery_hold')
                    record['workflow_outcome'] = 'Manual uncertainty remains unknown and unresolved; unverified reply does not clear hold.'
                    continue
                def export(p, allow_gaps):
                    response = request('POST', prefix + '/exports', {'acknowledge_unresolved': allow_gaps, 'input_hash': p['input_hash'], 'preview_revision': p['revision']}, p['revision'])
                    value = data(response)['export']
                    contents = {fmt: client.get(prefix + f'/exports/{value["id"]}/{fmt}').content for fmt in ('json', 'md', 'html')}
                    for fmt, content in contents.items():
                        write_new(directory / f'{value["id"]}.{fmt}', content)
                    return value, contents
                if project['attention_summary']['status'] != 'reviewed':
                    response = request('POST', prefix + '/exports', {'acknowledge_unresolved': False, 'input_hash': project['input_hash']}, project['revision'])
                    check('technical failures refuse unacknowledged export', response.json().get('error', {}).get('code'), 'unresolved_export')
                    value, _ = export(project, True)
                    check('acknowledged record stays draft', value['status'], 'draft_with_gaps')
                    record['workflow_outcome'] = 'Technical findings preserved despite synthetic satisfied disposition; explicit draft export.'
                else:
                    value, originals = export(project, False)
                    record['export_hashes'] = {fmt: sha(content) for fmt, content in originals.items()}
                    check('complete record status', value['status'], 'reviewed')
                    if case.get('replacement_files'):
                        project = fresh()
                        old_input = project['input_hash']
                        packet(case['replacement_files'], 'v2')
                        project = fresh()
                        check('correction changes input hash', project['input_hash'] != old_input, True)
                        check('correction makes all saved reviews stale', [d['review_state'] for d in project['decisions']], ['stale'])
                        check('correction cannot remain ready', project['attention_summary']['status'], 'draft_with_gaps')
                        for fmt, original in originals.items():
                            check('historical ' + fmt + ' byte identical', client.get(prefix + f'/exports/{value["id"]}/{fmt}').content == original, True)
                        project = assess(project, 'corrected')
                        second, second_contents = export(project, False)
                        check('fresh scripted review creates new current snapshot', second['id'] != value['id'] and second['status'] == 'reviewed', True)
                        record['second_export_hashes'] = {fmt: sha(content) for fmt, content in second_contents.items()}
                        record['workflow_outcome'] = 'Two packet compositions and two records; correction stales old reviews and preserves old downloads.'
                    else:
                        record['workflow_outcome'] = 'Narrow facts pass, scripted synthetic review saved, local record created.'
        except Exception as error:
            record['execution_error'] = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
        finally:
            record['passed'] = bool(record['checks']) and all(c['passed'] for c in record['checks']) and 'execution_error' not in record
            # Save incremental outcomes even if a later family fails.
            write_new(output / (case['id'] + '-result.json'), encoded(record))
    results['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    results['passed_checks'] = sum(c['passed'] for r in results['cases'] for c in r['checks'])
    results['total_checks'] = sum(len(r['checks']) for r in results['cases'])
    results['passed_families'] = sum(r['passed'] for r in results['cases'])
    write_new(output / 'results.json', encoded(results))
    print(json.dumps({'results': str(output / 'results.json'), 'passed_checks': results['passed_checks'], 'total_checks': results['total_checks'], 'passed_families': results['passed_families'], 'total_families': len(results['cases'])}))
    return 0 if results['passed_families'] == len(results['cases']) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'run'])
    parser.add_argument('artifact_root')
    args = parser.parse_args()
    if args.action == 'freeze':
        freeze(args.artifact_root)
        return 0
    return run(args.artifact_root)


if __name__ == '__main__':
    raise SystemExit(main())
