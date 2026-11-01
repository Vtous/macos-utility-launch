# macos-utility-launch

**A Codex skill for developing, validating, branding, packaging, and preparing native macOS utilities for release.**

[简体中文](README.zh-CN.md) · [Skill entrypoint](skills/macos-utility-launch/SKILL.md)

Built from the real development of [OtterMate](https://github.com/Vtous/OtterMate), this skill preserves practical lessons about tiny menu bar icons, complete ICNS files, configuration-preserving upgrades, isolated testing, and clean public releases.

## What is included

- A short phase-aware workflow: use only the part relevant to the current request.
- References for product scope and naming, native behavior and validation, visual identity, upgrades and icon diagnosis, and bilingual GitHub release preparation.
- Three Python tools: build a complete ICNS, package and verify an already signed App, and stage an explicit public source file list.
- A sanitized OtterMate case study and example project/file-list specifications.

The skill does not prescribe an otter mascot, require a specific app architecture, or publish projects without task authorization. Developer ID notarization and subscription billing are future integration topics, not implemented services.

## Install

Copy **only** `skills/macos-utility-launch` into your Codex user skills directory, normally `~/.codex/skills/`. If `CODEX_HOME` is configured, use its `skills` directory instead. Preserve any existing skill of the same name before replacing it. The repository root is not itself the installable skill directory.

Codex may need a new chat/session or a skills refresh to discover a newly installed skill. Invoke it with:

```text
Use $macos-utility-launch to prepare this native Mac utility for release,
including real validation, app/menu bar icons, and English/Chinese documentation.
```

You can also request one stage, such as an icon correction or configuration-preserving rename. Automatic skill discovery uses the normal default; invoking the skill does not authorize public uploads or new system permissions.

## Tools and checks

Python tools use only the standard library, Python 3.9+. Icon generation and App packaging require macOS and Apple's system tools. Source staging also runs on other platforms. The full UI/workflow documentation is currently in Chinese; this project overview is bilingual.

```sh
python3 -m unittest discover -s tests -v
```

The suite includes local file-selection/privacy checks and macOS integration checks using a disposable signed fixture. It does not launch apps, change login items, use personal configuration, or upload anything. See [script usage](skills/macos-utility-launch/references/script-tools.md) for limits and parameters.

Validation snapshot (2026-11-01): 16 checks passed on macOS 27.2 / Apple Silicon, including Apple's icon encoder and native ZIP/signature round trips. Restricted execution environments may require access to macOS image services for `iconutil`.

The repository includes an explicit `public-files.json` list. To inspect it without uploading or copying anything:

```sh
python3 skills/macos-utility-launch/scripts/prepare_public.py --source-root . --manifest public-files.json
```

## Limits and license

Pattern checks are not a security audit. Signature integrity is not Apple notarization. A single-machine test is not universal compatibility. Commercial services and platform policies should be verified against current official documentation when used.

[MIT License](LICENSE). The adapted icon-generation workflow derives from the MIT-licensed OtterMate project. This skill contains no Apple credentials, personal input-method rules, or proprietary image assets.
