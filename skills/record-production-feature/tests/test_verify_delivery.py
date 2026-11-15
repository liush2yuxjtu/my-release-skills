"""Fixture-only tests for the verifier; generated color is never product evidence."""
import builtins
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/verify_delivery.py'
spec = importlib.util.spec_from_file_location('verify_delivery', SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
HAS_PILLOW = importlib.util.find_spec('PIL') is not None
HAS_MEDIA_TOOLS = bool(shutil.which('ffmpeg') and shutil.which('ffprobe') and HAS_PILLOW)


class DeliveryChecks(unittest.TestCase):
    def assert_receipt(self, output, verdict, stage=None):
        report = json.loads((output / 'machine.json').read_text())
        self.assertEqual(report['machine_verdict'], verdict)
        self.assertEqual(report['visual_verdict'], 'pending')
        self.assertEqual(report['native_playback_verdict'], 'pending')
        if stage:
            self.assertEqual(report['error_stage'], stage)
        return report

    def make_mp4(self, root, *, pixel_format='yuv420p', faststart=True):
        media = root / 'fixture-only.mp4'
        command = ['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                   'color=c=blue:s=160x100:r=30:d=1', '-c:v', 'libx264',
                   '-threads', '1', '-pix_fmt', pixel_format]
        if faststart:
            command.extend(['-movflags', '+faststart'])
        subprocess.run([*command, str(media)], capture_output=True, check=True)
        return media

    def make_gif(self, root, durations=(30, 170, 50, 90)):
        from PIL import Image
        media = root / 'fixture-only.gif'
        colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255)]
        frames = [Image.new('RGB', (16, 10), color) for color in colors[:len(durations)]]
        frames[0].save(media, save_all=True, append_images=frames[1:],
                       duration=list(durations), loop=0, optimize=False, disposal=2)
        return media

    def test_atom_reader_rejects_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'truncated.mp4'
            file.write_bytes(struct.pack('>I4s', 200, b'moov'))
            with self.assertRaises(ValueError):
                verify.movie_atoms(file)

    def test_atom_reader_rejects_short_extended_header(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'truncated.mp4'
            file.write_bytes(struct.pack('>I4s', 1, b'moov'))
            with self.assertRaisesRegex(ValueError, 'extended atom header'):
                verify.movie_atoms(file)

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_real_decode_never_implies_visual_or_playback_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_mp4(root)
            report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['machine_verdict'], 'PASS')
            self.assertEqual(report['visual_verdict'], 'pending')
            self.assertEqual(report['native_playback_verdict'], 'pending')
            self.assertEqual(report['decoded_frames'], 30)
            self.assertTrue(report['faststart'])
            self.assertTrue(report['source_unchanged'])
            self.assertEqual(report['sha256'], report['sha256_after'])
            self.assertEqual(report['source_stat_before'], report['source_stat_after'])
            self.assertEqual(report['frames'][0]['decoded_frame_index'], 0)
            self.assertEqual(report['frames'][-1]['decoded_frame_index'], 29)
            self.assertTrue((root / 'receipt/contact-sheet.png').exists())
            self.assertEqual(self.assert_receipt(root / 'receipt', 'PASS'), report)
            with self.assertRaises(FileExistsError):
                verify.inspect(media, root / 'receipt')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_h264_requires_faststart(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = verify.inspect(self.make_mp4(root, faststart=False), root / 'receipt')
            self.assertIn('not faststart', report['error'])
            self.assert_receipt(root / 'receipt', 'FAIL', 'codec')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_h264_requires_yuv420p(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = verify.inspect(self.make_mp4(root, pixel_format='yuv444p'), root / 'receipt')
            self.assertIn('must use yuv420p', report['error'])
            self.assert_receipt(root / 'receipt', 'FAIL', 'codec')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_variable_gif_delays_sample_display_time_and_include_final_pixels(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = verify.inspect(self.make_gif(root), root / 'receipt')
            self.assertEqual(report['machine_verdict'], 'PASS', report.get('error'))
            self.assertEqual(report['decoded_frames'], 4)
            self.assertEqual(report['gif_duration_ms'], 340)
            self.assertEqual(report['gif_loop'], 0)
            self.assertAlmostEqual(report['sample_timeline_duration_s'], 0.34)
            self.assertEqual([frame['decoded_frame_index'] for frame in report['frames']],
                             [0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3])
            self.assertAlmostEqual(report['frames'][-1]['time_s'], 0.25)
            self.assertLess(report['frames'][-1]['time_s'], report['duration_s'] - 1 / 30)
            for frame, expected in [(report['frames'][0], (255, 0, 0)),
                                    (report['frames'][-1], (0, 0, 255))]:
                with Image.open(root / 'receipt' / frame['path']) as image:
                    self.assertEqual(image.convert('RGB').getpixel((8, 5)), expected)
            self.assert_receipt(root / 'receipt', 'PASS')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_gif_zero_delays_use_decoder_timing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = verify.inspect(self.make_gif(root, durations=(0, 20, 0)), root / 'receipt')
            self.assertEqual(report['machine_verdict'], 'PASS', report.get('error'))
            self.assertEqual(report['gif_duration_ms'], 20)
            # GIF decoding normalizes missing/zero delays; raw delay sums do not
            # identify the final decoded frame or its actual presentation time.
            self.assertGreater(report['sample_timeline_duration_s'], 0.02)
            self.assertGreater(report['frames'][-1]['time_s'], 0.02)
            self.assertEqual(report['frames'][-1]['decoded_frame_index'], 2)
            self.assert_receipt(root / 'receipt', 'PASS')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_single_frame_gif_produces_sixteen_contact_sheet_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = verify.inspect(self.make_gif(root, durations=(500,)), root / 'receipt')
            self.assertEqual(report['machine_verdict'], 'PASS', report.get('error'))
            self.assertEqual(len(report['frames']), 16)
            self.assertEqual({frame['decoded_frame_index'] for frame in report['frames']}, {0})
            self.assertTrue((root / 'receipt/contact-sheet.png').exists())

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_invalid_delivery_is_failed_and_keeps_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / 'invalid.mp4'
            media.write_bytes(b'not a video')
            report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['machine_verdict'], 'FAIL')
            self.assert_receipt(root / 'receipt', 'FAIL', 'probe')

    def test_missing_delivery_is_failed_and_keeps_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = verify.inspect(root / 'missing.gif', root / 'receipt')
            self.assertIsNone(report['sha256'])
            self.assertIsNone(report['bytes'])
            self.assertEqual(report['error_type'], 'FileNotFoundError')
            self.assertEqual(self.assert_receipt(root / 'receipt', 'FAIL', 'input'), report)

    def test_cli_missing_delivery_exits_with_a_failure_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            completed = subprocess.run([sys.executable, str(SCRIPT), str(root / 'missing.gif'),
                                        str(root / 'receipt')], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(json.loads(completed.stdout)['machine_verdict'], 'FAIL')
            self.assertNotIn('Traceback', completed.stderr)
            self.assert_receipt(root / 'receipt', 'FAIL', 'input')

    def test_missing_pillow_is_failed_and_keeps_receipt(self):
        original_import = builtins.__import__

        def without_pillow(name, *args, **kwargs):
            if name == 'PIL':
                raise ModuleNotFoundError('Pillow is unavailable in this fixture')
            return original_import(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / 'fixture-only.gif'
            media.write_bytes(b'fixture input')
            with mock.patch('builtins.__import__', side_effect=without_pillow):
                report = verify.inspect(media, root / 'receipt')
            self.assertIsNotNone(report['sha256'])
            self.assertEqual(report['error_type'], 'ModuleNotFoundError')
            self.assert_receipt(root / 'receipt', 'FAIL', 'dependencies')

    @unittest.skipUnless(HAS_PILLOW, 'Pillow required')
    def test_missing_ffprobe_is_failed_and_keeps_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / 'fixture-only.gif'
            media.write_bytes(b'fixture input')
            with mock.patch.object(verify.subprocess, 'run', side_effect=FileNotFoundError('ffprobe unavailable')):
                report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['error_type'], 'FileNotFoundError')
            self.assert_receipt(root / 'receipt', 'FAIL', 'probe')

    @unittest.skipUnless(HAS_PILLOW, 'Pillow required')
    def test_media_tool_timeout_is_bounded_and_keeps_failure_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / 'fixture-only.gif'
            media.write_bytes(b'fixture input')
            with mock.patch.object(verify.subprocess, 'run',
                                   side_effect=subprocess.TimeoutExpired('ffprobe', 600)) as run:
                report = verify.inspect(media, root / 'receipt')
            self.assertGreater(run.call_args.kwargs['timeout'], 0)
            self.assertEqual(report['error_type'], 'TimeoutExpired')
            self.assert_receipt(root / 'receipt', 'FAIL', 'probe')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_missing_ffmpeg_is_failed_and_keeps_receipt(self):
        real_run = subprocess.run

        def without_ffmpeg(command, **kwargs):
            if command[0] == 'ffmpeg':
                raise FileNotFoundError('ffmpeg unavailable in this fixture')
            return real_run(command, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_gif(root)
            with mock.patch.object(verify.subprocess, 'run', side_effect=without_ffmpeg):
                report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['error_type'], 'FileNotFoundError')
            self.assert_receipt(root / 'receipt', 'FAIL', 'decode')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_decode_error_text_is_preserved_in_failure_receipt(self):
        real_run = subprocess.run

        def failed_decode(command, **kwargs):
            if command[0] == 'ffmpeg':
                # FFmpeg sometimes returns success while reporting decode errors.
                return subprocess.CompletedProcess(command, 0, '', 'fixture decode error')
            return real_run(command, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_gif(root)
            with mock.patch.object(verify.subprocess, 'run', side_effect=failed_decode):
                report = verify.inspect(media, root / 'receipt')
            self.assertIn('fixture decode error', report['error'])
            self.assert_receipt(root / 'receipt', 'FAIL', 'decode')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_successful_extractor_without_images_still_keeps_failure_receipt(self):
        real_run = subprocess.run

        def missing_samples(command, **kwargs):
            if command[0] == 'ffmpeg' and '-frames:v' in command:
                return subprocess.CompletedProcess(command, 0, '', '')
            return real_run(command, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_gif(root)
            with mock.patch.object(verify.subprocess, 'run', side_effect=missing_samples):
                report = verify.inspect(media, root / 'receipt')
            self.assertIn('did not produce a nonempty frame-00.png', report['error'])
            self.assert_receipt(root / 'receipt', 'FAIL', 'samples')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_extractor_failure_preserves_error_and_partial_evidence(self):
        real_run = subprocess.run

        def failed_samples(command, **kwargs):
            if command[0] == 'ffmpeg' and '-frames:v' in command:
                Path(command[-1].replace('%02d', '00')).write_bytes(b'fixture partial image')
                raise subprocess.CalledProcessError(1, command, stderr='fixture extraction error')
            return real_run(command, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_gif(root)
            with mock.patch.object(verify.subprocess, 'run', side_effect=failed_samples):
                report = verify.inspect(media, root / 'receipt')
            self.assertIn('fixture extraction error', report['error'])
            self.assert_receipt(root / 'receipt', 'FAIL', 'samples')
            self.assertEqual((root / 'receipt/frame-00.png').read_bytes(), b'fixture partial image')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_invalid_sample_pixels_keep_failure_receipt(self):
        real_run = subprocess.run

        def invalid_sample(command, **kwargs):
            if command[0] == 'ffmpeg' and '-frames:v' in command:
                Path(command[-1].replace('%02d', '00')).write_bytes(b'invalid PNG fixture')
                return subprocess.CompletedProcess(command, 0, '', '')
            return real_run(command, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_gif(root, durations=(500,))
            with mock.patch.object(verify.subprocess, 'run', side_effect=invalid_sample):
                report = verify.inspect(media, root / 'receipt')
            self.assert_receipt(root / 'receipt', 'FAIL', 'samples')
            self.assertEqual(report['error_type'], 'UnidentifiedImageError')
            self.assertEqual((root / 'receipt/frame-00.png').read_bytes(), b'invalid PNG fixture')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_image_decoder_specific_error_keeps_failure_receipt(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_gif(root)
            with mock.patch.object(Image, 'open', side_effect=Image.DecompressionBombError('fixture image limit')):
                report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['error_type'], 'DecompressionBombError')
            self.assert_receipt(root / 'receipt', 'FAIL', 'codec')

    @unittest.skipUnless(HAS_MEDIA_TOOLS, 'FFmpeg and Pillow required')
    def test_source_mutation_cannot_leave_a_pass_for_preinspection_hash(self):
        real_run = subprocess.run
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = self.make_gif(root)
            original_hash = hashlib.sha256(media.read_bytes()).hexdigest()

            def mutate_after_samples(command, **kwargs):
                completed = real_run(command, **kwargs)
                if command[0] == 'ffmpeg' and '-frames:v' in command:
                    with media.open('ab') as source:
                        source.write(b'fixture concurrent modification')
                return completed

            with mock.patch.object(verify.subprocess, 'run', side_effect=mutate_after_samples):
                report = verify.inspect(media, root / 'receipt')
            self.assertEqual(report['sha256'], original_hash)
            self.assertNotEqual(report['sha256_after'], original_hash)
            self.assertFalse(report['source_unchanged'])
            self.assertIn('Source changed during inspection', report['error'])
            self.assertTrue((root / 'receipt/contact-sheet.png').exists())
            self.assert_receipt(root / 'receipt', 'FAIL', 'source_integrity')

    def test_failure_retry_never_overwrites_previous_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / 'receipt'
            verify.inspect(root / 'missing.gif', output)
            (output / 'earlier-evidence.txt').write_text('retain this evidence')
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            with self.assertRaises(FileExistsError):
                verify.inspect(root / 'another-missing.gif', output)
            self.assertEqual(before, {path.name: path.read_bytes() for path in output.iterdir()})
            self.assert_receipt(output, 'FAIL', 'input')


if __name__ == '__main__':
    unittest.main()
