#!/usr/bin/env python3
"""Audit actual delivered MP4/GIF bytes; never promote machine checks to visual PASS.

Requires ffmpeg/ffprobe and Pillow. Paths and private receipts remain in the run,
not in the public skill repository. Example: verify_delivery.py clip.mp4 qa/run-2
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path


def movie_atoms(path):
    atoms = []
    with path.open('rb') as stream:
        total = path.stat().st_size
        while stream.tell() + 8 <= total:
            offset = stream.tell()
            size, kind = struct.unpack('>I4s', stream.read(8))
            if size == 1:
                size = struct.unpack('>Q', stream.read(8))[0]
            elif size == 0:
                size = total - offset
            if size < 8 or offset + size > total:
                raise ValueError('Truncated or invalid MP4 atom')
            atoms.append(kind.decode('ascii', errors='replace'))
            stream.seek(offset + size)
    return atoms


def inspect(media, output):
    from PIL import Image
    media, output = Path(media).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {'sha256': hashlib.sha256(media.read_bytes()).hexdigest(),
              'bytes': media.stat().st_size, 'machine_verdict': 'FAIL',
              'visual_verdict': 'pending', 'native_playback_verdict': 'pending'}
    try:
        probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames',
                                '-show_streams', '-show_format', '-of', 'json', str(media)],
                               capture_output=True, text=True, check=True)
        metadata = json.loads(probe.stdout)
        video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        duration = float(metadata['format']['duration'])
        assert duration > 0, 'Nonpositive duration'
        decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(media), '-f', 'null', '-'],
                                 capture_output=True, text=True)
        assert decoded.returncode == 0 and not decoded.stderr.strip(), 'Decode reported errors'
        result.update(duration_s=duration, width=video['width'], height=video['height'],
                      codec=video['codec_name'], pix_fmt=video.get('pix_fmt'),
                      decoded_frames=int(video['nb_read_frames']),
                      audio_streams=sum(s['codec_type'] == 'audio' for s in metadata['streams']))
        if video['codec_name'] == 'h264':
            assert video['pix_fmt'] == 'yuv420p', 'MP4 must use yuv420p'
            atoms = movie_atoms(media)
            assert 'moov' in atoms and 'mdat' in atoms, 'Missing MP4 index or media'
            assert atoms.index('moov') < atoms.index('mdat'), 'MP4 is not faststart'
            result['faststart'] = True
        elif video['codec_name'] == 'gif':
            gif = Image.open(media)
            durations = []
            for i in range(gif.n_frames):
                gif.seek(i)
                durations.append(gif.info.get('duration', 0))
            result['gif_duration_ms'] = sum(durations)
            result['gif_loop'] = gif.info.get('loop')
        else:
            raise ValueError('Unsupported delivery codec: ' + video['codec_name'])
        frames = []
        for i in range(16):
            time_s = i * max(0, duration - 1 / 30) / 15
            frame = output / f'frame-{i:02d}.png'
            subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(time_s), '-i', str(media),
                            '-frames:v', '1', str(frame)], check=True)
            frames.append({'time_s': time_s, 'path': frame.name})
        # Anonymous, unlabeled frames for an independent reader. Keep originals too.
        thumb_width = 640
        thumb_height = round(video['height'] * thumb_width / video['width'])
        sheet = Image.new('RGB', (thumb_width * 4, thumb_height * 4))
        for i, entry in enumerate(frames):
            image = Image.open(output / entry['path']).convert('RGB')
            image = image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            sheet.paste(image, ((i % 4) * thumb_width, (i // 4) * thumb_height))
        sheet.save(output / 'contact-sheet.png')
        result.update(machine_verdict='PASS', frames=frames,
                      note='A decoded file and contact sheet do not establish visual or playback PASS.')
    except (AssertionError, ValueError, StopIteration, subprocess.CalledProcessError) as error:
        result['error'] = str(error)
    (output / 'machine.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('media')
    parser.add_argument('output', help='New directory; previous evidence is never overwritten')
    arguments = parser.parse_args()
    report = inspect(arguments.media, arguments.output)
    print(json.dumps(report))
    raise SystemExit(0 if report['machine_verdict'] == 'PASS' else 1)
