import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from smoke_boot import runtime_failures


class RuntimeFailureTests(unittest.TestCase):
    def test_halted_runtime_is_detected_despite_clean_process_exit(self):
        log = ('renderer ready\nDISPATCH FATAL: misaligned target 0x0000FFFF\n'
               'emulation halted; TCP debug server stays live\n')
        self.assertEqual(len(runtime_failures(log)), 2)

    def test_normal_startup_has_no_fatal_marker(self):
        self.assertEqual(runtime_failures('OpenBIOS LLE\nrenderer ready\n'), [])


if __name__ == '__main__':
    unittest.main()
