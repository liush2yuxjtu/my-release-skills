"""Fixture-only tests for the verifier; generated color is never product evidence."""
import importlib.util
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/verify_delivery.py'
spec = importlib.util.spec_from_file_location('verify_delivery', SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class DeliveryChecks(unittest.TestCase):
    def test_atom_reader_rejects_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'truncated.mp4'
            file.write_bytes(struct.pack('>I4s', 200, b'moov'))
            with self.assertRaises(ValueError):
                verify.movie_atoms(file)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_real_decode_never_implies_visual_or_playback_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / 'fixture-only.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'color=c=blue:s=160x100:r=30:d=1', '-c:v', 'libx264',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(media)], check=True)
            report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['machine_verdict'], 'PASS')
            self.assertEqual(report['visual_verdict'], 'pending')
            self.assertEqual(report['native_playback_verdict'], 'pending')
            self.assertEqual(report['decoded_frames'], 30)
            self.assertTrue((root / 'receipt/contact-sheet.png').exists())
            with self.assertRaises(FileExistsError):
                verify.inspect(media, root / 'receipt')

    @unittest.skipUnless(shutil.which('ffprobe'), 'ffprobe required')
    def test_invalid_delivery_is_failed_and_keeps_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / 'invalid.mp4'
            media.write_bytes(b'not a video')
            report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['machine_verdict'], 'FAIL')
            self.assertEqual(json.loads((root / 'receipt/machine.json').read_text())['visual_verdict'], 'pending')


if __name__ == '__main__':
    unittest.main()
