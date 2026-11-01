#!/usr/bin/env python3
"""Build and round-trip verify a complete ICNS with Apple's system tools."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "Apple tool failed")
    return result.stdout


def dimensions(path):
    result = run(["/usr/bin/sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)])
    width = re.search(r"pixelWidth:\s*(\d+)", result)
    height = re.search(r"pixelHeight:\s*(\d+)", result)
    if not width or not height:
        raise ValueError("Cannot read image dimensions")
    return int(width.group(1)), int(height.group(1))


def build(source, output, replace=False):
    if sys.platform != "darwin":
        raise ValueError("Requires macOS sips and iconutil")
    source, output = Path(source).resolve(), Path(output).absolute()
    if not source.is_file() or source.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Source must be a PNG file")
    if dimensions(source) != (1024, 1024):
        raise ValueError("Source must be exactly 1024 x 1024 pixels")
    if output.suffix.lower() != ".icns" or output.is_symlink():
        raise ValueError("Output must be a non-symlink .icns path")
    if output.exists() and (not replace or not output.is_file()):
        raise ValueError("Output exists; use --replace only for an intended resource replacement")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="macos-icons-", dir=output.parent) as work:
        root = Path(work)
        iconset = root / "Application.iconset"
        iconset.mkdir()
        expected = {}
        for size in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                name = "icon_{}x{}{}.png".format(size, size, "@2x" if scale == 2 else "")
                pixels = size * scale
                expected[name] = (pixels, pixels)
                run(["/usr/bin/sips", "-z", str(pixels), str(pixels), "-s", "dpiWidth", "72",
                     "-s", "dpiHeight", "72", str(source), "--out", str(iconset / name)])
        encoded, decoded = root / "Application.icns", root / "decoded.iconset"
        run(["/usr/bin/iconutil", "-c", "icns", str(iconset), "-o", str(encoded)])
        run(["/usr/bin/iconutil", "-c", "iconset", str(encoded), "-o", str(decoded)])
        for name, wanted in expected.items():
            path = decoded / name
            if not path.is_file() or dimensions(path) != wanted:
                raise ValueError("Round-trip icon representation invalid: " + name)
        os.replace(encoded, output)
    return {"output": str(output), "verified_representations": len(expected)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="1024 x 1024 PNG master")
    parser.add_argument("output", help="Output .icns")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    try:
        result = build(args.source, args.output, args.replace)
        print("Verified {} representations: {}".format(result["verified_representations"], result["output"]))
    except (ValueError, OSError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
