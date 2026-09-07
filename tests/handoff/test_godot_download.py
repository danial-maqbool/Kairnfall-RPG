"""Offline HTTP fixtures for verified, resumable official tool downloads."""
from __future__ import annotations

import contextlib
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import get_godot as downloader


class Response(io.BytesIO):
    def __init__(self, body, status=200, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}


class InterruptedResponse(Response):
    def read(self, size=-1):
        if self.tell():
            raise OSError('simulated connection interruption')
        return super().read(2)


class GodotDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.body = b'abcdef'
        self.asset = {
            'name': 'official.zip', 'size': len(self.body),
            'digest': 'sha256:' + hashlib.sha256(self.body).hexdigest(),
            'browser_download_url': 'https://github.com/godotengine/godot/releases/download/fixture/official.zip',
        }
        self.target = self.folder / self.asset['name']
        self.partial = self.folder / (self.asset['name'] + '.partial')

    def run_download(self, response):
        with patch.object(downloader.urllib.request, 'urlopen', return_value=response) as opened, contextlib.redirect_stdout(io.StringIO()):
            result = downloader.download(self.asset, self.folder)
        return result, opened.call_args.args[0]

    def test_complete_response_is_hash_verified_before_promotion(self):
        result, request = self.run_download(Response(self.body, headers={'Content-Length': '6'}))
        self.assertEqual(result.read_bytes(), self.body)
        self.assertFalse(self.partial.exists())
        self.assertEqual(request.get_header('Accept-encoding'), 'identity')

    def test_resume_sends_range_and_appends_only_matching_range(self):
        self.partial.write_bytes(b'ab')
        result, request = self.run_download(Response(b'cdef', 206, {'Content-Range': 'bytes 2-5/6', 'Content-Length': '4'}))
        self.assertEqual(request.get_header('Range'), 'bytes=2-')
        self.assertEqual(result.read_bytes(), self.body)

    def test_ignored_range_restarts_instead_of_appending(self):
        self.partial.write_bytes(b'ab')
        result, request = self.run_download(Response(self.body, 200, {'Content-Length': '6'}))
        self.assertEqual(request.get_header('Range'), 'bytes=2-')
        self.assertEqual(result.read_bytes(), self.body)

    def test_interruption_preserves_prefix_for_next_attempt(self):
        with self.assertRaises(OSError):
            self.run_download(InterruptedResponse(self.body, headers={'Content-Length': '6'}))
        self.assertEqual(self.partial.read_bytes(), b'ab')
        self.assertFalse(self.target.exists())
        result, _ = self.run_download(Response(b'cdef', 206, {'Content-Range': 'bytes 2-5/6'}))
        self.assertEqual(result.read_bytes(), self.body)

    def test_bad_range_headers_never_truncate_existing_prefix(self):
        for value in ('bytes 0-3/6', 'bytes 2-5/7', 'bytes 2-6/6', 'bytes 2-1/6', 'bytes 2-5/*', ''):
            with self.subTest(value=value):
                self.partial.write_bytes(b'ab')
                with self.assertRaises(RuntimeError):
                    self.run_download(Response(b'cdef', 206, {'Content-Range': value}))
                self.assertEqual(self.partial.read_bytes(), b'ab')
                self.assertFalse(self.target.exists())

    def test_bad_full_response_headers_preserve_existing_prefix(self):
        for headers in ({'Content-Length': '5'}, {'Content-Length': 'bad'}, {'Content-Encoding': 'gzip'}, {'Content-Range': 'bytes 0-5/6'}):
            with self.subTest(headers=headers):
                self.partial.write_bytes(b'ab')
                with self.assertRaises(RuntimeError):
                    self.run_download(Response(self.body, 200, headers))
                self.assertEqual(self.partial.read_bytes(), b'ab')

    def test_range_content_length_must_match_range(self):
        self.partial.write_bytes(b'ab')
        with self.assertRaises(RuntimeError):
            self.run_download(Response(b'cdef', 206, {'Content-Range': 'bytes 2-5/6', 'Content-Length': '6'}))
        self.assertEqual(self.partial.read_bytes(), b'ab')

    def test_short_response_retains_bytes_without_promotion(self):
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            self.run_download(Response(b'ab', 200, {'Content-Length': '6'}))
        self.assertEqual(self.partial.read_bytes(), b'ab')
        self.assertFalse(self.target.exists())

    def test_short_valid_range_can_be_resumed_again(self):
        self.partial.write_bytes(b'ab')
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            self.run_download(Response(b'cd', 206, {'Content-Range': 'bytes 2-3/6', 'Content-Length': '2'}))
        self.assertEqual(self.partial.read_bytes(), b'abcd')
        result, request = self.run_download(Response(b'ef', 206, {'Content-Range': 'bytes 4-5/6'}))
        self.assertEqual(request.get_header('Range'), 'bytes=4-')
        self.assertEqual(result.read_bytes(), self.body)

    def test_connection_failure_does_not_truncate_partial(self):
        self.partial.write_bytes(b'ab')
        with patch.object(downloader.urllib.request, 'urlopen', side_effect=OSError('offline')), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(OSError):
                downloader.download(self.asset, self.folder)
        self.assertEqual(self.partial.read_bytes(), b'ab')

    def test_unexpected_http_status_preserves_partial(self):
        self.partial.write_bytes(b'ab')
        with self.assertRaisesRegex(RuntimeError, 'HTTP status'):
            self.run_download(Response(b'', 416))
        self.assertEqual(self.partial.read_bytes(), b'ab')

    def test_response_overflow_is_rejected_before_writing_chunk(self):
        self.partial.write_bytes(b'ab')
        with self.assertRaisesRegex(RuntimeError, 'exceeds'):
            self.run_download(Response(b'cdefEXTRA', 206, {'Content-Range': 'bytes 2-5/6'}))
        self.assertEqual(self.partial.read_bytes(), b'ab')

    def test_hash_mismatch_never_replaces_existing_archive(self):
        self.target.write_bytes(b'previous-unverified-file')
        with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
            self.run_download(Response(b'xxxxxx'))
        self.assertEqual(self.target.read_bytes(), b'previous-unverified-file')
        self.assertFalse(self.partial.exists())

    def test_complete_partial_is_verified_without_http(self):
        self.partial.write_bytes(self.body)
        with patch.object(downloader.urllib.request, 'urlopen') as opened:
            self.assertEqual(downloader.download(self.asset, self.folder).read_bytes(), self.body)
            opened.assert_not_called()

    def test_corrupt_complete_partial_is_not_promoted(self):
        self.partial.write_bytes(b'xxxxxx')
        with patch.object(downloader.urllib.request, 'urlopen') as opened:
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                downloader.download(self.asset, self.folder)
            opened.assert_not_called()
        self.assertFalse(self.target.exists())

    def test_valid_cached_archive_is_hash_checked_without_http(self):
        self.target.write_bytes(self.body)
        with patch.object(downloader.urllib.request, 'urlopen') as opened:
            self.assertEqual(downloader.download(self.asset, self.folder), self.target)
            opened.assert_not_called()

    def test_invalid_official_metadata_is_rejected_without_http(self):
        for changes in ({'digest': 'sha256:not-a-hash'}, {'size': 0}, {'size': True}, {'size': '6'}):
            with self.subTest(changes=changes), patch.object(downloader.urllib.request, 'urlopen') as opened:
                asset = self.asset | changes
                with self.assertRaises(RuntimeError):
                    downloader.download(asset, self.folder)
                opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
