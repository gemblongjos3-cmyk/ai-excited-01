"""Copy the competition artwork without changing its bytes."""

import hashlib
import os
from pathlib import Path
import shutil
import sys


SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
               0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_dimensions(data):
    """Read dimensions from a JPEG start-of-frame segment."""
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            raise ValueError("invalid JPEG marker")
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            break
        marker = data[pos]
        pos += 1
        if marker in (0xD9, 0xDA):
            break
        if marker in {0x01, 0xD8, *range(0xD0, 0xD8)}:
            continue
        if pos + 2 > len(data):
            raise ValueError("truncated JPEG segment length")
        length = int.from_bytes(data[pos:pos + 2], "big")
        if length < 2 or pos + length > len(data):
            raise ValueError("invalid or truncated JPEG segment")
        if marker in SOF_MARKERS:
            if length < 8:
                raise ValueError("truncated JPEG SOF segment")
            height = int.from_bytes(data[pos + 3:pos + 5], "big")
            width = int.from_bytes(data[pos + 5:pos + 7], "big")
            return width, height
        pos += length
    raise ValueError("JPEG SOF marker not found")


def main():
    source = Path(__file__).resolve().parent / "entry.jpg"
    if not source.is_file():
        source = Path.cwd() / "entry.jpg"
    max_bytes = 1048576
    if source.stat().st_size > max_bytes:
        raise ValueError(f"JPEG exceeds the {max_bytes}-byte limit")
    data = source.read_bytes()
    if len(data) > max_bytes:
        raise ValueError(f"JPEG exceeds the {max_bytes}-byte limit")
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("JPEG is missing the SOI marker (ffd8) at the start")
    if not data.endswith(b"\xff\xd9"):
        raise ValueError("JPEG is missing the EOI marker (ffd9) at the end")
    width, height = jpeg_dimensions(data)
    if not (0 < width <= 1024 and 0 < height <= 1024):
        raise ValueError(f"JPEG dimensions {width}x{height} must be 1–1024 px per side")
    digest = hashlib.sha256(data).hexdigest()
    destination = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    copied_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if copied_digest != digest:
        raise ValueError("copied file SHA256 does not match the source")
    print(f"ai-excited-01 -> {destination} | {len(data)} bytes | "
          f"{width}x{height} | sha256 {digest}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
