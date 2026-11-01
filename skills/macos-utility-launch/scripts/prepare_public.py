#!/usr/bin/env python3
"""Check an explicit public file list; optionally stage reviewed files in a new directory."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys


BLOCKED_PARTS = {".git", ".build", ".test-data", ".venv", "node_modules", "dist",
                 "__pycache__", ".ssh", ".aws", ".DS_Store"}
BLOCKED_NAMES = {"rules.json", "credentials", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}
RULES = [
    ("private-key", "error", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("github-token", "error", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("aws-access-key", "error", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("credential-assignment", "error", re.compile(
        r'''(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|password)\b["']?\s*[:=]\s*["']([A-Za-z0-9_+/=.-]{24,})["']''')),
    ("personal-home-path", "review", re.compile(r"/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/")),
    ("email-address", "review", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def selected_files(root, manifest):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("Source root must be a directory")
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    names = data.get("files") if isinstance(data, dict) else None
    if not isinstance(names, list) or not names:
        raise ValueError("Manifest must contain a non-empty files array")
    result, seen = [], set()
    for name in names:
        if not isinstance(name, str) or not name or "\\" in name or any(ord(c) < 32 for c in name):
            raise ValueError("Invalid file-list entry")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or str(path) != name:
            raise ValueError("File-list entries must be normalized relative file paths")
        if name.casefold() in seen:
            raise ValueError("Duplicate or case-colliding file-list entry: " + name)
        seen.add(name.casefold())
        if (any(part in BLOCKED_PARTS or part.startswith(".env") for part in path.parts)
                or path.name in BLOCKED_NAMES or path.name.startswith("rules-backup-")
                or path.suffix.lower() in {".p12", ".pfx", ".key", ".log"}):
            raise ValueError("Private/build file type excluded: " + name)
        source = root
        for part in path.parts:
            source = source / part
            if source.is_symlink():
                raise ValueError("Symlinks cannot enter the public file list: " + name)
        source.resolve().relative_to(root)
        if not source.is_file():
            raise ValueError("File-list entry is missing or is a directory: " + name)
        result.append((name, source))
    return result


def scan(files):
    findings, hashes = [], {}
    for name, source in files:
        hashes[name] = sha256_file(source)
        if source.stat().st_size > 4 * 1024 * 1024:
            findings.append({"path": name, "kind": "large-file-not-content-scanned", "severity": "review"})
            continue
        raw = source.read_bytes()
        try:
            text = raw.decode("utf-8")
            if "\x00" in text:
                raise UnicodeDecodeError("utf-8", raw, 0, 1, "binary content")
        except UnicodeDecodeError:
            findings.append({"path": name, "kind": "binary-not-content-scanned", "severity": "review"})
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for kind, severity, pattern in RULES:
                for match in pattern.finditer(line):
                    if kind == "email-address" and match.group().lower().endswith("@users.noreply.github.com"):
                        continue
                    findings.append({"path": name, "line": line_number, "kind": kind, "severity": severity})
                    break
    return findings, hashes


def prepare(root, manifest, output=None, allow_reviews=False):
    files = selected_files(root, manifest)
    if output is not None:
        output = Path(output).absolute()
        if output.exists() or output.is_symlink():
            raise ValueError("Output directory must not already exist")
    findings, hashes = scan(files)
    blocked = any(f["severity"] == "error" for f in findings) or (bool(findings) and not allow_reviews)
    report = {
        "files": len(files), "findings": findings, "blocked": blocked, "staged": False,
        "sha256": hashes,
        "limits": "Pattern checks only. Review binary/image contents, licenses, Git history and commit identity separately.",
    }
    if output is not None and not blocked:
        output.mkdir(parents=True)
        try:
            for name, source in files:
                target = output / name
                target.parent.mkdir(parents=True, exist_ok=True)
                # Re-check links and hashes in case files changed after the scan.
                current = Path(root).resolve()
                for part in PurePosixPath(name).parts:
                    current = current / part
                    if current.is_symlink():
                        raise ValueError("File became a symlink after review: " + name)
                if sha256_file(source) != hashes[name]:
                    raise ValueError("Source changed after review: " + name)
                shutil.copyfile(source, target)
                shutil.copymode(source, target)
                if sha256_file(target) != hashes[name]:
                    raise ValueError("Staged content mismatch: " + name)
        except Exception:
            # Only this newly created staging directory is removed; sources are never altered.
            shutil.rmtree(output)
            raise
        report["staged"] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", help="Omit to check only; supplied directory must be new")
    parser.add_argument("--allow-reviewed-findings", action="store_true",
                        help="Stage review-level findings only after their contents have been reviewed; errors still block")
    args = parser.parse_args()
    try:
        result = prepare(args.source_root, args.manifest, args.output_dir, args.allow_reviewed_findings)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result["blocked"] else 0
    except (ValueError, OSError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
