#!/usr/bin/env python3
"""Package an already signed macOS app; verify copied and extracted contents."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import subprocess
import sys
import tempfile


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "System tool failed")
    return result.stdout + result.stderr


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bundle_manifest(root):
    root = Path(root).resolve()
    result = {}
    for current, directories, files in os.walk(root, followlinks=False):
        for name in sorted(directories + files):
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if path.is_symlink():
                try:
                    path.resolve().relative_to(root)
                except (ValueError, RuntimeError):
                    raise ValueError("External or cyclic bundle symlink: " + relative)
                result[relative] = {"type": "symlink", "target": os.readlink(path)}
            elif stat.S_ISREG(mode):
                result[relative] = {"type": "file", "mode": stat.S_IMODE(mode), "sha256": sha256(path)}
            elif stat.S_ISDIR(mode):
                result[relative] = {"type": "directory"}
            else:
                raise ValueError("Unsupported bundle entry: " + relative)
    return result


def verify(app, ticket):
    run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)])
    if ticket:
        run(["/usr/bin/xcrun", "stapler", "validate", str(app)])


def package(app, output, archive_name=None, ticket=False):
    if sys.platform != "darwin":
        raise ValueError("Requires macOS codesign and ditto")
    app, output = Path(app).resolve(), Path(output).absolute()
    if not app.is_dir() or app.suffix.lower() != ".app":
        raise ValueError("Input must be an existing .app bundle")
    if output.exists() or output.is_symlink():
        raise ValueError("Output directory must not already exist")
    if output.resolve() == app or app in output.resolve().parents:
        raise ValueError("Output cannot be inside the input app")
    archive_name = archive_name or app.stem + "-macOS.zip"
    if (Path(archive_name).name != archive_name or not archive_name.endswith(".zip")
            or "\\" in archive_name or any(ord(c) < 32 for c in archive_name)):
        raise ValueError("Archive name must be a simple .zip filename")
    with open(app / "Contents/Info.plist", "rb") as stream:
        info = plistlib.load(stream)
    executable = info.get("CFBundleExecutable", "")
    if not isinstance(executable, str) or not executable or Path(executable).name != executable:
        raise ValueError("Invalid CFBundleExecutable")
    binary = app / "Contents/MacOS" / executable
    if not binary.is_file():
        raise ValueError("Missing main executable")
    original = bundle_manifest(app)
    verify(app, ticket)
    signing = run(["/usr/bin/codesign", "-d", "--verbose=2", str(app)])
    architectures = run(["/usr/bin/lipo", "-archs", str(binary)]).strip().split()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="macos-package-", dir=output.parent) as work:
        root = Path(work)
        staged = root / "staging" / app.name
        staged.parent.mkdir()
        run(["/usr/bin/ditto", "--norsrc", "--noextattr", str(app), str(staged)])
        verify(staged, ticket)
        if bundle_manifest(staged) != original:
            raise ValueError("Staged bundle contents differ from input")
        archive = root / archive_name
        run(["/usr/bin/ditto", "-c", "-k", "--norsrc", "--noextattr", "--keepParent",
             str(staged), str(archive)])
        extracted = root / "verify"
        extracted.mkdir()
        run(["/usr/bin/ditto", "-x", "-k", str(archive), str(extracted)])
        restored = extracted / app.name
        verify(restored, ticket)
        if bundle_manifest(restored) != original or bundle_manifest(app) != original:
            raise ValueError("Extracted bundle differs, or input changed during packaging")
        digest = sha256(archive)
        report = {
            "archive": archive_name, "sha256": digest, "bytes": archive.stat().st_size,
            "bundle_identifier": info.get("CFBundleIdentifier"),
            "version": info.get("CFBundleShortVersionString"), "build": info.get("CFBundleVersion"),
            "minimum_macos_declared": info.get("LSMinimumSystemVersion"),
            "architectures": architectures,
            "signature_kind": "ad-hoc" if "Signature=adhoc" in signing else "certificate-or-other",
            "signature_integrity": "verified-original-staged-extracted",
            "bundle_contents": "identical-original-staged-extracted",
            "notarization": "stapled-ticket-validated" if ticket else "not-checked",
        }
        # Claim a fresh directory only after all checks. Never replace a previous release.
        output.mkdir()
        shutil.copy2(archive, output / archive_name)
        (output / "SHA256SUMS").write_text(digest + "  " + archive_name + "\n", encoding="utf-8")
        (output / "package-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", help="Already signed .app; input is never changed")
    parser.add_argument("--output-dir", required=True, help="New output directory")
    parser.add_argument("--archive-name")
    parser.add_argument("--validate-stapled-ticket", action="store_true")
    args = parser.parse_args()
    try:
        report = package(args.app, args.output_dir, args.archive_name, args.validate_stapled_ticket)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (ValueError, OSError, plistlib.InvalidFileException) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
