"""Copy the competition artwork using only the Python standard library."""
import hashlib
import os
from pathlib import Path
import struct
import sys


def dimensions(data):
    offset = 2
    while offset < len(data):
        if data[offset] != 0xFF:
            raise ValueError("Invalid JPEG marker")
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            raise ValueError("Truncated JPEG marker")
        marker = data[offset]
        offset += 1
        if marker in (0xDA, 0xD9):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            raise ValueError("Truncated JPEG segment length")
        length = int.from_bytes(data[offset:offset + 2], "big")
        if length < 2 or offset + length > len(data):
            raise ValueError("Invalid or truncated JPEG segment")
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if length < 8:
                raise ValueError("Truncated JPEG SOF segment")
            height, width = struct.unpack(">HH", data[offset + 3:offset + 7])
            if width == 0 or height == 0:
                raise ValueError("JPEG dimensions must be positive")
            return width, height
        offset += length
    raise ValueError("JPEG has no SOF marker")


def main():
    source = Path(__file__).resolve().parent / "entry.jpg"
    if not source.is_file():
        source = Path.cwd() / "entry.jpg"
    if source.stat().st_size > 1048576:
        raise ValueError("Artwork exceeds the 1048576-byte limit")
    data = source.read_bytes()
    if len(data) > 1048576:
        raise ValueError("Artwork exceeds the 1048576-byte limit")
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("JPEG is missing the SOI marker (ffd8)")
    if not data.endswith(b"\xff\xd9"):
        raise ValueError("JPEG is missing the EOI marker (ffd9); file may be truncated")
    width, height = dimensions(data)
    if max(width, height) > 1024:
        raise ValueError("Artwork exceeds the 1024-pixel side limit")
    destination = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        raise ValueError("Copied file SHA-256 does not match the source")
    print(f"ai-excited-01 -> {destination} | {len(data)} bytes | "
          f"{width}x{height} | sha256 {digest}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
