"""Prepare authored synthetic participant files and separate moderator keys.

No network, application mutation, inference, consent or participant result.
Refuse an existing output folder so first-run materials cannot be overwritten.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw


BRIEF = """# Cedar Demo Studio — delivery brief

This fictional studio needs three distinct 1200 × 1200 PNG launch images and a
short guide explaining how a teammate changes the contact email and telephone
number in the fictional site's Contact settings, publishes the change, and
checks the public result. Artwork quality and whether the guide is useful need
human review; image metadata alone cannot settle them.

The owner also wrote: “Maybe we could include a logo as one launch image.”
That suggestion has not been agreed. Identify any clarification you need before
treating it as confirmed scope. No real website, login or customer exists.
"""

PARTICIPANT = """# HandoffReady trial — participant instructions

These are fictional, non-confidential materials. Participation is voluntary.
We are evaluating the workflow, not testing your ability. You can stop at any
time. Tell the moderator before sharing any personal or customer information.

Your role is the designer/developer handing work to Yash, the local reviewer.
You use Discord on your own account; Yash operates his local review desk.
You do not need the application, an AI subscription, a bot token or localhost.

## Task 1

Read BRIEF.md. Use the delivery room to help the reviewer understand the work
in packet-01, identify anything that needs resolving and leave a clear record
of what is ready and what is not. Explain your reasoning aloud if comfortable.
Ask for help when needed; there is no hidden requirement to know tool commands.

## Task 2 — wait until the moderator gives you the replacement

A revised packet has arrived. Help the reviewer decide what should happen to
the earlier review and record, and prepare the current delivery record.

## At the end

Explain what the final record promises, what you would still inspect, and
whether this would fit a real delivery you do. Candid criticism is useful.
This record is not a client's contractual acceptance or a quality guarantee.
"""

INITIAL_GUIDE = """# Contact settings

Welcome to Cedar Demo Studio. To change the site logo, choose Brand, upload
artwork and publish. Contact settings is another area in this fictional site.
This synthetic note describes the branding task.
"""

CORRECTED_GUIDE = """# Contact settings

Synthetic instructions for the fictional Cedar Demo Studio site only.
1. Open Contact settings in the site editor.
2. Update the contact email and telephone fields with the agreed values.
3. Save the fields, then choose Publish.
4. Open the public contact page in a fresh browser view. Check both visible
   values and the email/telephone link destinations against the agreed values.
5. If the public page still shows old values, report the discrepancy; do not
   assume that saving or publishing proved the public page is correct.

No real site or account is supplied. The reviewer must judge usefulness and
state the limitation that these instructions have not been executed on a site.
"""


def png(color, size, label):
    image = Image.new('RGB', size, color)
    ImageDraw.Draw(image).text((30, 30), label, fill='white')
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    participant = output / 'participant'
    participant.mkdir()
    (participant / 'START-HERE.md').write_text(PARTICIPANT)
    (participant / 'BRIEF.md').write_text(BRIEF)
    first = png('#294C43', (1200, 1200), 'Cedar synthetic launch 01')
    initial = {'launch-01.png': first, 'launch-02.png': first,
        'launch-03.png': png('#836241', (600, 600), 'Cedar synthetic launch 03'),
        'guide.md': INITIAL_GUIDE.encode()}
    corrected = {'launch-01.png': first,
        'launch-02.png': png('#46547C', (1200, 1200), 'Cedar synthetic launch 02'),
        'launch-03.png': png('#836241', (1200, 1200), 'Cedar synthetic launch 03'),
        'guide.md': CORRECTED_GUIDE.encode()}
    rows = []
    for name, contents, parent in [('packet-01', initial, participant),
            ('packet-02', corrected, output / 'moderator-only')]:
        folder = parent / name
        folder.mkdir(parents=True)
        for filename, raw in contents.items():
            (folder / filename).write_bytes(raw)
            rows.append({'packet': name, 'filename': filename, 'bytes': len(raw),
                'sha256': hashlib.sha256(raw).hexdigest()})
        with zipfile.ZipFile(output / f'{name}.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
            for filename, raw in contents.items():
                archive.writestr(filename, raw)
    with zipfile.ZipFile(output / 'participant-start.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(participant.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(participant))
    key = {
        'scope': 'Assistant-authored synthetic usability materials; not held-out or a completed trial',
        'initial': {'png_files': 3, 'distinct_png_byte_sequences': 2,
            'wrong_dimensions': {'launch-03.png': [600, 600]},
            'guide_literal': 'Contact settings is present, but the guide describes logo changes; literal success does not settle suitability',
            'scope': 'Logo inclusion is unconfirmed; preserve uncertainty or ask'},
        'replacement': {'png_files': 3, 'distinct_png_byte_sequences': 3,
            'all_png_dimensions': [1200, 1200],
            'guide': 'Describes contact email/telephone, publishing and public checks; no actual website execution is proved',
            'currency': 'Changed bytes stale prior decisions; old record stays immutable; fresh local review required'},
        'interpretation': 'Synthetic technical facts and human observations must be reported separately',
    }
    (output / 'moderator-only/ANSWER-KEY.json').write_text(json.dumps(key, indent=2) + '\n')
    manifest = {'status': 'prepared_not_run', 'authorship': 'AI-assisted authored synthetic materials',
        'files': rows, 'initial_packet_count': 4, 'corrected_packet_count': 4,
        'not_in_participant_start': ['replacement packet', 'moderator answer key', 'observation sheet']}
    (output / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    guide = Path(__file__).resolve().parents[1] / 'docs/switch/TRIAL-GUIDE.md'
    (output / 'YASH-TRIAL-GUIDE.md').write_text(guide.read_text())
    observation = guide.read_text().split('## Observation sheet — fill only after observing\n', 1)[1].split('\n## If no participant', 1)[0]
    (output / 'moderator-only/OBSERVATION-SHEET.md').write_text(
        '# Private trial observations — blank until a real session\n\n' + observation)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    arguments = parser.parse_args()
    manifest = prepare(arguments.output.expanduser().resolve())
    print(json.dumps({'status': manifest['status'], 'files': len(manifest['files']),
        'output': str(arguments.output)}, indent=2))
