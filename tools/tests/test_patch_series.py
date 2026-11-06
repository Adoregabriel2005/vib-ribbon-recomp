"""Ensure published patches apply to pristine pinned upstream files."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PatchSeriesTests(unittest.TestCase):
    def test_patches_apply_to_pinned_source_and_reverse_cleanly(self):
        series = {
            'psxrecomp': ['lle-irq-thread-switch.patch', 'audio-cd-media.patch',
                          'pc-volume-settings.patch'],
            'recomp-ui': ['recomp-ui-pt-br.patch'],
        }
        cache = ROOT / '.cache/tmp'
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as folder:
            for module, patches in series.items():
                base = Path(folder) / module
                base.mkdir()
                paths = set()
                published = {}
                for patch in patches:
                    # Test the actual Git blobs, including their line endings.
                    data = subprocess.check_output(['git', '-C', str(ROOT),
                                                    'show', ':patches/' + patch])
                    published[patch] = Path(folder) / patch
                    published[patch].write_bytes(data)
                    for line in data.decode('utf-8').splitlines():
                        if line.startswith('--- a/'):
                            paths.add(line[6:])
                for name in paths:
                    destination = base / name
                    self.assertTrue(destination.resolve().is_relative_to(base.resolve()))
                    data = subprocess.check_output(['git', '-C', str(ROOT / module),
                                                    'show', 'HEAD:' + name])
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
                subprocess.run(['git', 'init', '-q', str(base)], check=True, capture_output=True)
                for patch in patches:
                    path = str(published[patch])
                    subprocess.run(['git', '-C', str(base), 'apply', '--check', path],
                                   check=True, capture_output=True)
                    subprocess.run(['git', '-C', str(base), 'apply', path],
                                   check=True, capture_output=True)
                for patch in reversed(patches):
                    subprocess.run(['git', '-C', str(base), 'apply', '--reverse',
                                    str(published[patch])], check=True, capture_output=True)
