"""Behavioral checks for public staging plus disposable macOS integrations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills/macos-utility-launch/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


public = load("prepare_public")
icons = load("make_icons")
packager = load("package_app")


class PublicStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="utility-public-tests-")
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.manifest = self.root / "files.json"
        self.output = self.root / "public"

    def tearDown(self):
        self.temp.cleanup()

    def files(self, names):
        self.manifest.write_text(json.dumps({"files": names}))

    def test_stages_only_listed_files_and_preserves_contents(self):
        (self.source / "main.swift").write_text('print("示例")\n')
        (self.source / "private-note.txt").write_text("unlisted")
        self.files(["main.swift"])
        report = public.prepare(self.source, self.manifest, self.output)
        self.assertTrue(report["staged"])
        self.assertEqual([p.name for p in self.output.iterdir()], ["main.swift"])
        self.assertEqual((self.source / "main.swift").read_bytes(), (self.output / "main.swift").read_bytes())

    def test_check_only_does_not_create_output(self):
        (self.source / "readme.md").write_text("public")
        self.files(["readme.md"])
        self.assertFalse(public.prepare(self.source, self.manifest)["staged"])
        self.assertFalse(self.output.exists())

    def test_cli_reports_success_for_clean_check(self):
        (self.source / "readme.md").write_text("public")
        self.files(["readme.md"])
        result = subprocess.run([sys.executable, str(SCRIPTS / "prepare_public.py"),
                                 "--source-root", str(self.source), "--manifest", str(self.manifest)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["blocked"])

    def test_cli_blocks_without_echoing_secret(self):
        secret = "github_" + "pat_" + "X" * 32
        (self.source / "main.swift").write_text(secret)
        self.files(["main.swift"])
        result = subprocess.run([sys.executable, str(SCRIPTS / "prepare_public.py"),
                                 "--source-root", str(self.source), "--manifest", str(self.manifest),
                                 "--output-dir", str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertFalse(self.output.exists())

    def test_token_blocks_and_is_not_echoed_even_when_reviews_allowed(self):
        secret = "gh" + "p_" + "A" * 32
        (self.source / "main.swift").write_text('let token = "' + secret + '"')
        self.files(["main.swift"])
        report = public.prepare(self.source, self.manifest, self.output, True)
        self.assertTrue(report["blocked"])
        self.assertNotIn(secret, json.dumps(report))
        self.assertFalse(self.output.exists())

    def test_personal_path_requires_review_then_can_be_staged(self):
        path = "/" + "Users/" + "demo-person/Projects"
        (self.source / "readme.md").write_text(path)
        self.files(["readme.md"])
        report = public.prepare(self.source, self.manifest, self.output)
        self.assertTrue(report["blocked"])
        self.assertNotIn(path, json.dumps(report))
        self.assertFalse(self.output.exists())
        self.assertTrue(public.prepare(self.source, self.manifest, self.output, True)["staged"])

    def test_binary_requires_explicit_review(self):
        (self.source / "asset.bin").write_bytes(b"\x00\xff\x01")
        self.files(["asset.bin"])
        self.assertTrue(public.prepare(self.source, self.manifest)["blocked"])
        self.assertTrue(public.prepare(self.source, self.manifest, self.output, True)["staged"])

    def test_traversal_is_rejected(self):
        (self.root / "outside.txt").write_text("outside")
        self.files(["../outside.txt"])
        with self.assertRaises(ValueError):
            public.prepare(self.source, self.manifest, self.output)
        self.assertFalse(self.output.exists())

    def test_symlink_and_symlink_parent_are_rejected(self):
        (self.root / "outside.txt").write_text("outside")
        (self.source / "link.txt").symlink_to(self.root / "outside.txt")
        self.files(["link.txt"])
        with self.assertRaises(ValueError):
            public.prepare(self.source, self.manifest, self.output)
        (self.source / "folder").symlink_to(self.root, target_is_directory=True)
        self.files(["folder/outside.txt"])
        with self.assertRaises(ValueError):
            public.prepare(self.source, self.manifest, self.output)

    def test_private_rules_and_directories_are_rejected(self):
        (self.source / "rules.json").write_text("{}")
        self.files(["rules.json"])
        with self.assertRaises(ValueError):
            public.prepare(self.source, self.manifest, self.output)
        self.files(["."])
        with self.assertRaises(ValueError):
            public.prepare(self.source, self.manifest, self.output)

    def test_existing_output_is_preserved(self):
        (self.source / "public.txt").write_text("public")
        self.files(["public.txt"])
        self.output.mkdir()
        sentinel = self.output / "keep.txt"
        sentinel.write_text("keep")
        with self.assertRaises(ValueError):
            public.prepare(self.source, self.manifest, self.output)
        self.assertEqual(sentinel.read_text(), "keep")

    def test_case_collisions_are_rejected(self):
        self.files(["README.md", "readme.md"])
        (self.source / "README.md").write_text("public")
        with self.assertRaises(ValueError):
            public.prepare(self.source, self.manifest, self.output)


@unittest.skipUnless(sys.platform == "darwin", "Requires macOS system tools")
class MacIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="utility-mac-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.app = cls.root / "验证助手.app"
        contents = cls.app / "Contents"
        (contents / "MacOS").mkdir(parents=True)
        (contents / "Resources").mkdir()
        info = {"CFBundleIdentifier": "com.example.UtilitySkillFixture", "CFBundleExecutable": "Fixture",
                "CFBundlePackageType": "APPL", "CFBundleVersion": "1",
                "CFBundleShortVersionString": "0.1.0", "LSMinimumSystemVersion": "14.0"}
        (contents / "Info.plist").write_bytes(plistlib.dumps(info))
        # Apple's supplied binary is copied and re-signed; it is never executed.
        import shutil
        shutil.copyfile("/usr/bin/true", contents / "MacOS/Fixture")
        (contents / "MacOS/Fixture").chmod(0o755)
        (contents / "Resources/notice.txt").write_text("disposable fixture")
        subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", str(cls.app)],
                       check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_unicode_app_packages_roundtrips_and_input_is_unchanged(self):
        before = packager.bundle_manifest(self.app)
        output = self.root / "release"
        report = packager.package(self.app, output, "Fixture-macOS.zip")
        self.assertEqual(before, packager.bundle_manifest(self.app))
        self.assertEqual(report["signature_kind"], "ad-hoc")
        self.assertEqual(report["notarization"], "not-checked")
        digest = hashlib.sha256((output / "Fixture-macOS.zip").read_bytes()).hexdigest()
        self.assertEqual(report["sha256"], digest)
        self.assertIn(digest, (output / "SHA256SUMS").read_text())
        self.assertNotIn(str(self.root), (output / "package-report.json").read_text())
        with self.assertRaises(ValueError):
            packager.package(self.app, output)

    def test_unsigned_modified_app_is_rejected_without_output(self):
        import shutil
        modified = self.root / "Modified.app"
        shutil.copytree(self.app, modified)
        (modified / "Contents/Resources/notice.txt").write_text("tampered")
        output = self.root / "should-not-exist"
        with self.assertRaises(ValueError):
            packager.package(modified, output)
        self.assertFalse(output.exists())

    def test_external_symlink_is_rejected(self):
        folder = self.root / "link-fixture"
        folder.mkdir()
        (folder / "external").symlink_to("/etc/hosts")
        with self.assertRaises(ValueError):
            packager.bundle_manifest(folder)

    def test_icon_roundtrip_verifies_ten_representations_and_refuses_overwrite(self):
        # Standard-library-generated image avoids shipping a third-party picture.
        import struct
        import zlib
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        source = self.root / "master.png"
        raw = (b"\x00" + b"\x40\x80\xc0\xff" * 1024) * 1024
        source.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1024, 1024, 8, 6, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
        output = self.root / "Fixture.icns"
        result = icons.build(source, output)
        self.assertEqual(result["verified_representations"], 10)
        self.assertEqual(output.read_bytes()[:4], b"icns")
        before = output.read_bytes()
        with self.assertRaises(ValueError):
            icons.build(source, output)
        self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
