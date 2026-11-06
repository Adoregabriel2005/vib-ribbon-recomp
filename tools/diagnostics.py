"""Development console using the unmodified PSXRecomp diagnostic server."""
import argparse
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import re
import socket
import time

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = ('dispatch_stats', 'dirty_ram_stats', 'dirty_ram_unsupported',
            'overlay_loader_status', 'unknown_dispatch_log', 'audio_stats',
            'cdrom_state', 'spu_status', 'latency', 'overlay_static_entries', 'frame', 'perf')


def read_response(stream, limit=4 * 1024 * 1024):
    """Some framework trace handlers stream one JSON object across lines."""
    data = bytearray()
    while len(data) < limit:
        line = stream.readline(limit - len(data))
        if not line:
            raise ConnectionError('Runtime closed diagnostic connection')
        data.extend(line)
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            continue
    raise ValueError('Diagnostic response exceeded size limit')


def build_metrics():
    dispatch = ROOT / 'generated/SCES_028.73_dispatch.c'
    audit = ROOT / 'generated/AOT_STATIC_AUDIT.json'
    proof = json.loads(audit.read_text(encoding='utf-8')) if audit.exists() else {}
    profile = json.loads((ROOT / 'aot/overlays.json').read_text(encoding='utf-8'))
    audited = bool(proof) and all((ROOT / 'generated' / name).is_file() and
                hashlib.sha256((ROOT / 'generated' / name).read_bytes()).hexdigest() == digest
                for name, digest in proof.get('files', {}).items())
    identified = sum(len(image.get('files', [])) for image in profile['images'])
    return dict(static_functions_emitted=len(re.findall(r'^extern void func_[0-9A-F]+\(',
                dispatch.read_text(encoding='utf-8'), re.M)) if dispatch.exists() else None,
                static_execution_coverage=None,
                overlays_identified=identified,
                overlays_audited=len(proof.get('image_coverage', [])) if audited else None,
                overlay_dispatch_variants=proof.get('published_variants') if audited else None,
                generated_sources_match_audit=audited,
                full_static_coverage_proven=proof.get('full_static_coverage_proven', False),
                limitation='Emitted C and byte provenance do not prove execution or fidelity. '
                           'PAK contents and optional isolated fragments remain under investigation.')


def collect(port):
    result = dict(utc=datetime.now(timezone.utc).isoformat(), build=build_metrics(), runtime={})
    failures = {}
    for request_id, command in enumerate(COMMANDS, 1):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=3) as sock:
                with sock.makefile('rwb') as stream:
                    stream.write((json.dumps(dict(id=request_id, cmd=command)) + '\n').encode())
                    stream.flush()
                    reply = read_response(stream)
                    if reply.get('id') != request_id and reply.get('ok'):
                        raise ValueError('Unexpected diagnostic response id')
                    result['runtime'][command] = reply
        except (OSError, ValueError, ConnectionError) as error:
            failures[command] = str(error)
    result['connection'] = ('partial' if failures and result['runtime'] else
                            'unavailable' if failures else 'connected')
    if failures:
        result['errors'] = failures
    return result


def show(result):
    build, runtime = result['build'], result['runtime']
    print('Vib-Ribbon Recomp | development diagnostics |', result['utc'])
    print('Runtime:', result['connection'])
    print('Static functions emitted:', build['static_functions_emitted'])
    print('Static execution coverage: not established')
    print('Overlay images identified/audited:', build['overlays_identified'], '/', build['overlays_audited'])
    print('Overlay dispatch variants:', build['overlay_dispatch_variants'])
    print('Full native coverage proven:', build['full_static_coverage_proven'])
    for name, fields in (
        ('dispatch_stats', ('static_hits', 'miss_total', 'miss_unique', 'segment_miss_total')),
        ('dirty_ram_stats', ('blocks_run', 'insns_run', 'aborts', 'guard_yields', 'per_pc_matching', 'per_pc_emitted')),
        ('overlay_loader_status', ('active', 'registered', 'last_msg')),
        ('audio_stats', ('underruns', 'out', 'spu_out')),
    ):
        reply = runtime.get(name, {})
        print(name + ':', json.dumps({key: reply.get(key) for key in fields}))
    print('Missing values mean not measured. Full addresses, audio and timing evidence are in JSON.')
    if result.get('error'):
        print(result['error'])
    if result.get('errors'):
        print('Query errors:', json.dumps(result['errors']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4370)
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/diagnostics-latest.json')
    args = parser.parse_args()
    while True:
        result = (dict(utc=datetime.now(timezone.utc).isoformat(), build=build_metrics(),
                       runtime={}, connection='offline') if args.offline else collect(args.port))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        show(result)
        if not args.watch:
            break
        time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
