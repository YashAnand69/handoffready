"""Prepare a public, read-only video page. Never deploys a live AI API."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def timestamp(seconds, vtt=False):
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, remainder = divmod(remainder, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{remainder:03d}' if vtt else f'{minutes + hours * 60}:{seconds:02d}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('demo_directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source, output = args.demo_directory.resolve(), args.output.resolve()
    if output == source or source.is_relative_to(output):
        parser.error('Output must be a separate staging directory.')
    manifest = json.loads((source / 'manifest.json').read_text())
    receipt = json.loads((source / 'walkthrough.verification.json').read_text())
    video = source / 'walkthrough.mp4'
    if hashlib.sha256(video.read_bytes()).hexdigest() != receipt['video_sha256']:
        parser.error('Video bytes do not match the verified encoding receipt.')
    if receipt['manifest_sha256'] != hashlib.sha256((source / 'manifest.json').read_bytes()).hexdigest():
        parser.error('Video manifest changed after encoding.')
    chapters, transcript, cues, elapsed = [], [], ['WEBVTT\n'], 0
    chapter_names = {1: 'Start with a delivery packet', 3: 'Actual Gemma checklist inference', 4: 'Review the source and requirements', 7: 'Actual local matching', 9: 'Failed alpha check stays visible', 11: 'Review the welcome-only guide', 14: 'Correct the PNG and re-review', 19: 'Compare immutable snapshots'}
    for index, slide in enumerate(manifest['slides'], 1):
        caption = html.escape(slide['caption'])
        duration = round(slide['duration_seconds'] * manifest['fps']) / manifest['fps']
        if index in chapter_names:
            chapters.append(f'<button type="button" data-time="{elapsed}"><span>{timestamp(elapsed)}</span>{chapter_names[index]}</button>')
        transcript.append(f'<li><time>{timestamp(elapsed)}</time>{caption}</li>')
        cues.append(f'{index}\n{timestamp(elapsed, True)} --> {timestamp(elapsed + duration, True)}\n{caption}\n')
        elapsed += duration
    if abs(elapsed - receipt['duration_seconds']) > .1:
        parser.error('Chapter duration does not match the encoded video.')
    output.mkdir(parents=True, exist_ok=True)
    template = (ROOT / 'docs/demo/index.template.html').read_text()
    (output / 'index.html').write_text(template.replace('__CHAPTERS__', '\n'.join(chapters)).replace('__TRANSCRIPT__', '\n'.join(transcript)))
    (output / 'walkthrough.vtt').write_text('\n'.join(cues))
    for name in ['demo.css', 'demo.js']:
        shutil.copy2(ROOT / 'docs/demo' / name, output / name)
    for name in ['walkthrough.mp4', 'walkthrough.poster.png', 'walkthrough.verification.json']:
        shutil.copy2(source / name, output / name)
    (output / '.nojekyll').write_text('')
    print(json.dumps({'output': str(output), 'chapters': len(chapters), 'duration_seconds': elapsed, 'video_sha256': receipt['video_sha256']}, indent=2))


if __name__ == '__main__':
    main()
