"""Inventory original disc files without exporting their contents.

PS-X EXE signatures are candidates, not proof of executable coverage.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'psxrecomp' / 'tools' / 'aot_overlay_spike'))
import extract_generic as extractor
sys.path.insert(0, str(ROOT / 'psxrecomp' / 'tools' / 'new_project_layout'))
import probe_disc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cue', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports' / 'disc_inventory.json')
    args = parser.parse_args()
    binary, raw = extractor.parse_cue_datatrack(str(args.cue))
    reader = extractor.eo.DiscReader(binary, raw=raw)
    files = []
    for name, lba, size in extractor.eo.enumerate_files(reader):
        data = reader.read_file_bytes(lba, size)
        images = []
        start = 0
        while True:
            offset = data.find(b'PS-X EXE', start)
            if offset < 0:
                break
            if offset + 0x800 <= len(data):
                entry, load, length = (struct.unpack_from('<I', data, offset + field)[0]
                                       for field in (0x10, 0x18, 0x1c))
                images.append(dict(offset=offset, entry=f'0x{entry:08X}',
                                   load=f'0x{load:08X}', text_bytes=length,
                                   payload_in_file=offset + 0x800 + length <= len(data)))
            start = offset + 8
        files.append(dict(name=name, lba=lba, bytes=size,
                          sha256=hashlib.sha256(data).hexdigest(), exe_candidates=images))
    cue_tracks, file_order = probe_disc.parse_cue(args.cue)
    track_files = []
    for name in file_order:
        path = probe_disc.resolve_cue_file(args.cue, name)
        length = path.stat().st_size
        if length % 2352:
            raise ValueError(f'Track is not sector aligned: {name}')
        with path.open('rb') as stream:
            sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
        track_files.append(dict(name=name, bytes=length, sectors=length // 2352, sha256=sha256))
    tracks = [dict(number=t.number, kind=t.kind, file=t.file,
                   index00_frames=t.index00_frames, index01_frames=t.index01_frames)
              for t in cue_tracks]
    report = dict(schema=1, files=files, track_files=track_files, tracks=tracks,
                  limitation='Signatures do not identify raw/compressed overlays or establish code coverage.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'{len(files)} files; {sum(len(f["exe_candidates"]) for f in files)} PS-X EXE candidates')
    for item in files:
        print(f'{item["name"]}: {item["bytes"]} bytes; EXE candidates={len(item["exe_candidates"])}')


if __name__ == '__main__':
    main()
