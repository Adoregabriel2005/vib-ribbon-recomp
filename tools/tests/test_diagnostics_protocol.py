"""Regressions from the native SIO/timing trace response format."""
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnostics import read_response


class TraceProtocolTests(unittest.TestCase):
    def test_streamed_trace_is_one_complete_response(self):
        stream = io.BytesIO(b'{"id":1,"ok":true,"entries":[\n'
                            b'{"tx":"0x42","rx":"0x41"},\n'
                            b'{"tx":"0x00","rx":"0xDF"}]}\n')
        reply = read_response(stream)
        self.assertEqual(reply['entries'][-1]['rx'], '0xDF')
        self.assertEqual(reply['id'], 1)

    def test_incomplete_trace_is_not_accepted(self):
        with self.assertRaises(ConnectionError):
            read_response(io.BytesIO(b'{"ok":true,"entries":[\n'))

    def test_oversized_response_is_bounded(self):
        with self.assertRaises(ValueError):
            read_response(io.BytesIO(b'{"data":"' + b'x' * 100), limit=32)


if __name__ == '__main__':
    unittest.main()
