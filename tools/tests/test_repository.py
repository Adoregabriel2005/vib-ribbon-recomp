import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_repository import violation
from configure_disc import local_config
import tomllib


class RepositoryTests(unittest.TestCase):
    def test_publication_rejects_media_and_generated_code(self):
        for name in ('disc/SCES_028.73', 'generated/overlay.c', 'music-cache/audio.bin',
                     'test.MP3', 'game.local.toml', 'reports/private.json'):
            self.assertIsNotNone(violation(name, b'example'), name)
        self.assertIsNone(violation('native/music_disc.cpp', b'// native source'))

    def test_publication_detects_credentials_without_exposing_them(self):
        self.assertIsNotNone(violation('settings.txt', b'ghp_' + b'x' * 36))
        self.assertIsNotNone(violation('data', b'PS-X EXE' + b'\0' * 32))

    def test_disc_config_preserves_other_settings_and_unicode(self):
        template = '[game]\ndisc = "disc/default.cue"\nplayers = 1\n[runtime]\nbios_hle = false\n'
        disc = Path('Músicas/disco "teste".cue')
        parsed = tomllib.loads(local_config(template, disc))
        self.assertEqual(parsed['game']['disc'], disc.as_posix())
        self.assertFalse(parsed['runtime']['bios_hle'])
        self.assertEqual(parsed['game']['players'], 1)
