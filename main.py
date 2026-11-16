import hashlib
import os
import sys
from pathlib import Path


SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
               0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def dimensions(data):
    offset = 2
    while offset < len(data):
        if data[offset] != 0xFF:
            raise ValueError('invalid JPEG marker')
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in (0xD9, 0xDA):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD8:
            continue
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset:offset + 2], 'big')
        if length < 2 or offset + length > len(data):
            raise ValueError('truncated or invalid JPEG segment')
        if marker in SOF_MARKERS:
            if length < 8:
                raise ValueError('invalid JPEG SOF segment')
            height = int.from_bytes(data[offset + 3:offset + 5], 'big')
            width = int.from_bytes(data[offset + 5:offset + 7], 'big')
            return width, height
        offset += length
    raise ValueError('JPEG SOF dimensions not found')


def main():
    source = Path(__file__).resolve().parent / 'entry.jpg'
    if not source.is_file():
        source = Path.cwd() / 'entry.jpg'
    if source.stat().st_size > 1048576:
        raise ValueError('source exceeds 1048576 bytes')
    data = source.read_bytes()
    if len(data) > 1048576:
        raise ValueError('source exceeds 1048576 bytes')
    if not data.startswith(b'\xff\xd8'):
        raise ValueError('JPEG SOI magic ffd8 missing at start')
    if not data.endswith(b'\xff\xd9'):
        raise ValueError('JPEG EOI magic ffd9 missing at end (possibly truncated)')
    width, height = dimensions(data)
    if width <= 0 or height <= 0:
        raise ValueError('JPEG dimensions must be positive')
    if width > 1024 or height > 1024:
        raise ValueError(f'JPEG dimensions {width}x{height} exceed 1024 px per side')
    destination = Path(os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')) / 'entry.png'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        raise ValueError('copied file SHA-256 does not match source')
    print(f'ai-excited-01 -> {destination} | {len(data)} bytes | {width}x{height} | sha256 {digest}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
