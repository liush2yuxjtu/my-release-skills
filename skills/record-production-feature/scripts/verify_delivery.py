#!/usr/bin/env python3
"""Audit actual delivered MP4/GIF bytes; never promote machine checks to visual PASS.

Requires ffmpeg/ffprobe and Pillow. Paths and private receipts remain in the run,
not in the public skill repository. Example: verify_delivery.py clip.mp4 qa/run-2
"""
import argparse
import bisect
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path

MEDIA_TOOL_TIMEOUT_S = 600


def source_fingerprint(media):
    def identity():
        stat = media.stat()
        return {'device': stat.st_dev, 'inode': stat.st_ino, 'bytes': stat.st_size,
                'mtime_ns': stat.st_mtime_ns, 'ctime_ns': stat.st_ctime_ns}

    before = identity()
    digest = hashlib.sha256()
    with media.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    after = identity()
    if before != after:
        raise ValueError('Source changed while hashing')
    return digest.hexdigest(), after


def movie_atoms(path):
    atoms = []
    with path.open('rb') as stream:
        total = path.stat().st_size
        while stream.tell() + 8 <= total:
            offset = stream.tell()
            size, kind = struct.unpack('>I4s', stream.read(8))
            header_size = 8
            if size == 1:
                extended_size = stream.read(8)
                if len(extended_size) != 8:
                    raise ValueError('Truncated MP4 extended atom header')
                size = struct.unpack('>Q', extended_size)[0]
                header_size = 16
            elif size == 0:
                size = total - offset
            if size < header_size or offset + size > total:
                raise ValueError('Truncated or invalid MP4 atom')
            atoms.append(kind.decode('ascii', errors='replace'))
            stream.seek(offset + size)
    return atoms


def run_media_tool(command):
    completed = subprocess.run(command, capture_output=True, text=True, check=True,
                               timeout=MEDIA_TOOL_TIMEOUT_S)
    if completed.stderr.strip():
        raise ValueError(f'{command[0]} reported errors: {completed.stderr.strip()}')
    return completed


def frame_samples(decoded_frames, duration, count=16):
    """Choose actual decoded frame indices at evenly spaced presentation times.

    Seeking into the final GIF frame's delay can produce no image at all. Select
    decoded indices instead, including the first and final frames explicitly.
    FFmpeg timestamps also account for GIF delays it normalizes during decoding.
    """
    timestamps = []
    for frame in decoded_frames:
        timestamp = float(frame.get('best_effort_timestamp_time', frame.get('pts_time')))
        if not math.isfinite(timestamp) or (timestamps and timestamp < timestamps[-1]):
            raise ValueError('Invalid decoded frame timestamps')
        timestamps.append(timestamp)
    if not timestamps:
        raise ValueError('No decoded video frames')
    starts = [timestamp - timestamps[0] for timestamp in timestamps]
    last = decoded_frames[-1]
    last_duration = float(last.get('duration_time', last.get('pkt_duration_time', 0)))
    if not math.isfinite(last_duration) or last_duration < 0:
        raise ValueError('Invalid final decoded frame duration')
    timeline_duration = starts[-1] + last_duration if last_duration > 0 else duration
    if not math.isfinite(timeline_duration) or timeline_duration <= 0 or timeline_duration < starts[-1]:
        raise ValueError('Invalid decoded timeline duration')
    samples = []
    for i in range(count):
        target = i * timeline_duration / (count - 1)
        index = min(len(starts) - 1, bisect.bisect_right(starts, target) - 1)
        if i == 0:
            index = 0
        elif i == count - 1:
            index = len(starts) - 1
        samples.append({'target_time_s': target, 'time_s': starts[index],
                        'decoded_frame_index': index})
    return samples, timeline_duration


def inspect(media, output):
    output = Path(output).resolve()
    # Refuse an existing path before touching it, including a previous FAIL run.
    output.mkdir(parents=True, exist_ok=False)
    result = {'sha256': None, 'bytes': None, 'machine_verdict': 'FAIL',
              'visual_verdict': 'pending', 'native_playback_verdict': 'pending',
              'source_unchanged': None,
              'note': 'A decoded file and contact sheet do not establish visual or playback PASS.'}
    stage = 'input'
    try:
        media = Path(media).resolve()
        digest, source_before = source_fingerprint(media)
        result.update(sha256=digest, bytes=source_before['bytes'], source_stat_before=source_before)
        stage = 'dependencies'
        from PIL import Image

        stage = 'probe'
        probe = run_media_tool(['ffprobe', '-v', 'error', '-count_frames',
                                '-show_streams', '-show_format', '-of', 'json', str(media)])
        metadata = json.loads(probe.stdout)
        video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        duration = float(metadata['format']['duration'])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('Nonpositive or invalid duration')
        result.update(duration_s=duration, width=video['width'], height=video['height'],
                      codec=video['codec_name'], pix_fmt=video.get('pix_fmt'),
                      decoded_frames=int(video['nb_read_frames']),
                      audio_streams=sum(s['codec_type'] == 'audio' for s in metadata['streams']))
        if video['width'] <= 0 or video['height'] <= 0 or result['decoded_frames'] <= 0:
            raise ValueError('No decoded video frames or invalid dimensions')
        stage = 'decode'
        run_media_tool(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(media), '-f', 'null', '-'])
        stage = 'codec'
        if video['codec_name'] == 'h264':
            if video['pix_fmt'] != 'yuv420p':
                raise ValueError('MP4 must use yuv420p')
            atoms = movie_atoms(media)
            if 'moov' not in atoms or 'mdat' not in atoms:
                raise ValueError('Missing MP4 index or media')
            if atoms.index('moov') > atoms.index('mdat'):
                raise ValueError('MP4 is not faststart')
            result['faststart'] = True
        elif video['codec_name'] == 'gif':
            with Image.open(media) as gif:
                result['gif_loop'] = gif.info.get('loop')
                durations = []
                for i in range(gif.n_frames):
                    gif.seek(i)
                    durations.append(gif.info.get('duration', 0))
                result['gif_duration_ms'] = sum(durations)
        else:
            raise ValueError('Unsupported delivery codec: ' + video['codec_name'])

        stage = 'frame_timing'
        timing = run_media_tool(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                 '-show_frames', '-show_entries',
                                 'frame=best_effort_timestamp_time,pts_time,pkt_duration_time,duration_time',
                                 '-of', 'json', str(media)])
        decoded_frames = json.loads(timing.stdout)['frames']
        if len(decoded_frames) != result['decoded_frames']:
            raise ValueError('Decoded frame count changed between probes')
        frames, timeline_duration = frame_samples(decoded_frames, duration)
        result['sample_timeline_duration_s'] = timeline_duration
        indices = sorted({entry['decoded_frame_index'] for entry in frames})
        paths = {index: f'frame-{i:02d}.png' for i, index in enumerate(indices)}
        for entry in frames:
            entry['path'] = paths[entry['decoded_frame_index']]
        stage = 'samples'
        selection = '+'.join(f'eq(n\\,{index})' for index in indices)
        run_media_tool(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', str(media),
                        '-map', '0:v:0', '-vf', 'select=' + selection, '-vsync', '0',
                        '-frames:v', str(len(indices)), '-start_number', '0',
                        str(output / 'frame-%02d.png')])
        for path in paths.values():
            frame = output / path
            if not frame.is_file() or frame.stat().st_size == 0:
                raise ValueError('Sample extraction did not produce a nonempty ' + path)
            with Image.open(frame) as image:
                image.load()
                if image.size != (video['width'], video['height']):
                    raise ValueError('Sample dimensions differ from the delivered video')
        result['frames'] = frames
        # Anonymous, unlabeled frames for an independent reader. Keep originals too.
        stage = 'contact_sheet'
        thumb_width = 640
        thumb_height = round(video['height'] * thumb_width / video['width'])
        sheet = Image.new('RGB', (thumb_width * 4, thumb_height * 4))
        for i, entry in enumerate(frames):
            with Image.open(output / entry['path']) as source:
                image = source.convert('RGB').resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                sheet.paste(image, ((i % 4) * thumb_width, (i // 4) * thumb_height))
        sheet.save(output / 'contact-sheet.png')
        stage = 'source_integrity'
        digest_after, source_after = source_fingerprint(media)
        result.update(sha256_after=digest_after, source_stat_after=source_after,
                      source_unchanged=digest_after == digest and source_after == source_before)
        if not result['source_unchanged']:
            raise ValueError('Source changed during inspection; generated samples are not verified evidence')
        result['machine_verdict'] = 'PASS'
    except Exception as error:
        # Tool, dependency and image-decoder errors must leave a failure receipt.
        # Interrupts still propagate; an existing output is rejected above.
        detail = str(error) or type(error).__name__
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            detail += ': ' + error.stderr.strip()
        result.update(error=detail, error_type=type(error).__name__, error_stage=stage)
    with (output / 'machine.json').open('x') as receipt:
        receipt.write(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('media')
    parser.add_argument('output', help='New directory; previous evidence is never overwritten')
    arguments = parser.parse_args()
    report = inspect(arguments.media, arguments.output)
    print(json.dumps(report))
    raise SystemExit(0 if report['machine_verdict'] == 'PASS' else 1)
