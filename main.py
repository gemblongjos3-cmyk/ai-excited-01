#!/usr/bin/env python3
"""Copy the competition image to the make.fun output location."""

import hashlib
import os
from pathlib import Path
import shutil
import struct


def jpeg_dimensions(data):
    """Return (width, height) from a JPEG byte string."""
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("entry.jpg is not a JPEG image")

    index = 2
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
    }
    while index < len(data):
        while index < len(data) and data[index] != 0xFF:
            index += 1
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break

        marker = data[index]
        index += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if index + 2 > len(data):
            break

        segment_length = struct.unpack_from(">H", data, index)[0]
        if segment_length < 2 or index + segment_length > len(data):
            break
        if marker in sof_markers:
            if segment_length < 7:
                break
            height, width = struct.unpack_from(">HH", data, index + 3)
            return width, height
        if marker == 0xDA:  # Start of scan; no frame header was found.
            break
        index += segment_length

    raise ValueError("could not find JPEG dimensions")


def main():
    script_dir = Path(__file__).resolve().parent
    beside_script = script_dir / "entry.jpg"
    source = beside_script if beside_script.is_file() else Path.cwd() / "entry.jpg"
    if not source.is_file():
        raise FileNotFoundError("entry.jpg not found beside the script or in the working directory")

    source_bytes = source.read_bytes()
    if len(source_bytes) > 1048576:
        raise ValueError(f"entry.jpg is too large: {len(source_bytes)} bytes (maximum 1048576)")
    if not source_bytes.startswith(b"\xff\xd8"):
        raise ValueError("entry.jpg is not a JPEG: missing SOI marker (ffd8) at the start")
    if not source_bytes.endswith(b"\xff\xd9"):
        raise ValueError("entry.jpg is not a complete JPEG: missing EOI marker (ffd9) at the end")

    width, height = jpeg_dimensions(source_bytes)
    if width > 1024 or height > 1024:
        raise ValueError(f"entry.jpg dimensions exceed 1024 px per side: {width}x{height}")

    digest = hashlib.sha256(source_bytes).hexdigest()
    destination = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)

    copied_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if copied_digest != digest:
        raise OSError(f"copied file sha256 mismatch: source {digest}, copy {copied_digest}")
    print(f"ai-excited-01 -> {destination} | {len(source_bytes)} bytes | {width}x{height} | sha256 {digest}")


if __name__ == "__main__":
    main()
