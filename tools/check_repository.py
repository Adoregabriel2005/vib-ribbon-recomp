"""Check candidate Git content before publishing. Never print matched secrets."""
import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_ROOTS = {'generated', 'reports', 'disc', 'saves', 'music-cache', '.cache',
                  'build', 'dist', 'release-stage', 'bios', 'isos'}
EXCLUDED_SUFFIXES = {'.bin', '.cue', '.iso', '.img', '.chd', '.mp3', '.wav', '.flac',
                     '.ogg', '.mcr', '.mcd', '.exe', '.dll', '.obj', '.o', '.a', '.pdb',
                     '.pem', '.key'}
SECRETS = re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|'
                     rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')


def violation(name: str, data: bytes) -> str | None:
    path = PurePosixPath(name)
    if (path.parts[0] in EXCLUDED_ROOTS or path.parts[0].startswith('build-') or
            path.suffix.lower() in EXCLUDED_SUFFIXES or
            path.name in {'game.local.toml', 'interface-language.txt'} or path.name.startswith('.env')):
        return 'local/generated/media file'
    if len(data) > 5 * 1024 * 1024:
        return 'file larger than 5 MiB; review before publishing'
    if data.startswith(b'PS-X EXE'):
        return 'original PlayStation executable'
    if SECRETS.search(data):
        return 'possible credential'
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Read actual index blobs')
    args = parser.parse_args()
    command = ['git', 'ls-files', '-z', '--cached']
    if not args.staged:
        command += ['--others', '--exclude-standard']
    names = subprocess.check_output(command, cwd=ROOT).decode('utf-8').split('\0')
    failures = []
    checked = 0
    for name in sorted(set(filter(None, names))):
        if (ROOT / name).is_dir():  # Submodule commits; their content is not uploaded here.
            continue
        if args.staged:
            data = subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT)
        else:
            data = (ROOT / name).read_bytes()
        checked += 1
        reason = violation(name, data)
        if reason:
            failures.append((name, reason))
    for name, reason in failures:
        print(f'REJECT {name}: {reason}')
    print(f'Checked {checked} files; {len(failures)} rejected.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
