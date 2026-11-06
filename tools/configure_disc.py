"""Configure a local disc without putting personal paths or game data in Git."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def local_config(template: str, disc: Path) -> str:
    replacement = 'disc = ' + json.dumps(disc.as_posix(), ensure_ascii=False)
    result, count = re.subn(r'^disc\s*=.*$', lambda _: replacement, template, count=1,
                            flags=re.MULTILINE)
    if count != 1:
        raise ValueError('Missing game.disc in template')
    tomllib.loads(result)
    return result


def configure(disc: Path) -> None:
    disc = disc.resolve(strict=True)
    if disc.suffix.lower() != '.cue':
        raise ValueError('Use the European multi-track CUE; all track BINs must remain beside it.')
    sys.path.insert(0, str(ROOT / 'psxrecomp' / 'tools' / 'aot_overlay_spike'))
    import extract_generic as extractor
    sys.path.insert(0, str(ROOT / 'psxrecomp' / 'tools' / 'new_project_layout'))
    import probe_disc
    template = (ROOT / 'game.toml').read_text(encoding='utf-8')
    config = tomllib.loads(template)
    tracks, names = probe_disc.parse_cue(disc)
    if len(tracks) != config['netplay']['required_tracks']:
        raise ValueError('The supported disc needs eight tracks, including the original audio.')
    for name in names:
        path = probe_disc.resolve_cue_file(disc, name)
        if not path.is_file() or not path.stat().st_size or path.stat().st_size % 2352:
            raise ValueError(f'Missing or incomplete track: {name}')
    track, raw = extractor.parse_cue_datatrack(str(disc))
    with Path(track).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha1').hexdigest()
    if digest not in config['prepare_disc']['known_sha1']:
        raise ValueError('Data track does not match the supported SCES-02873 dump.')
    reader = extractor.eo.DiscReader(track, raw=raw)
    boot = config['prepare_disc']['boot_exe']
    matches = [(lba, size) for name, lba, size in extractor.eo.enumerate_files(reader)
               if name.upper().split(';')[0] == boot.upper()]
    if len(matches) != 1:
        raise ValueError('Boot executable not found uniquely on this disc.')
    data = reader.read_file_bytes(*matches[0])
    if not data.startswith(b'PS-X EXE'):
        raise ValueError('Invalid boot executable.')
    output = ROOT / config['game']['exe']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    (ROOT / 'game.local.toml').write_text(local_config(template, disc), encoding='utf-8')
    print('Local disc configured; source tracks were not changed or copied.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('disc', type=Path)
    args = parser.parse_args()
    try:
        configure(args.disc)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
