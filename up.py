#!/usr/bin/env python3
"""Move font.sh into scripts/, updating every reference. Practices §6 rule 3.

Built against rnvizion.github.io @ main, all eleven anchors read live
2026-08-23. Run from repo root. Requires a clean git tree.

    python3 move_font_sh.py            # DRY RUN -- verifies, writes nothing
    python3 move_font_sh.py --apply

WHY CHECK-FIRST RATHER THAN THE sed BLOCK. The handoff's command block is
correct on today's tree -- I ran it and its proof gate printed `none`. But it
does `git mv` first and verifies last, so a drifted anchor leaves a moved file
and a half-edited tree to unpick by hand. This computes every replacement in
memory, refuses if any anchor is missing or ambiguous, and only then moves
anything. Nothing is written until all eleven have been found.

THE TRAP THIS EXISTS TO AVOID, which is the register's own by another name.
`build-og.yml` carries bare `"font.sh"` as a TRIGGER PATH. Move the file without
that line and the OG workflow silently stops firing on font changes -- the same
generator-outside-its-own-trigger-path defect already closed for
`generate_card.py`, one file over. A silent trigger is the worst shape of this:
CI goes green by not running.

MOVE AND YAML IN ONE COMMIT. GitHub runs a workflow from the commit that
triggered it, so splitting them leaves a window where CI runs `bash font.sh`
against a file that is gone.

THE MOVE ITSELF IS SAFE. font.sh resolves its font directory via
`git rev-parse --show-toplevel`, not relative to its own location, so it does
not care where it lives.

ELEVEN ANCHORS: seven external across six files, four inside font.sh itself.
The four internal ones matter because `--help` prints that block -- they are
output, not decoration, and a moved script whose help tells you to run it at the
old path is a document lying about itself.
"""
import pathlib
import re
import shutil
import subprocess
import sys

APPLY = "--apply" in sys.argv
ROOT = pathlib.Path(".")
SRC, DST = ROOT / "font.sh", ROOT / "scripts" / "font.sh"

# (path, old, new, expected occurrences)
EDITS = [
    (".github/workflows/build-og.yml", '      - "font.sh"', '      - "scripts/font.sh"', 1),
    (".github/workflows/build-og.yml", "        run: bash font.sh", "        run: bash scripts/font.sh", 1),
    (".github/workflows/build-og.yml", "so font.sh's downloads", "so scripts/font.sh's downloads", 1),
    (".devcontainer/devcontainer.json", "bash font.sh", "bash scripts/font.sh", 1),
    ("scripts/generate_site_og.py", "run ./font.sh first.", "run ./scripts/font.sh first.", 1),
    ("scripts/generate_project_card.py", "\n./font.sh first.", "\n./scripts/font.sh first.", 1),
    (".gitignore", "# fetched by font.sh", "# fetched by scripts/font.sh", 1),
    # inside font.sh -- read at its CURRENT path, written at the new one
    ("font.sh", "# font.sh — fetch", "# scripts/font.sh — fetch", 1),
    ("font.sh", "#   ./font.sh ", "#   ./scripts/font.sh ", 3),
]

assert SRC.exists(), "font.sh is not at the repo root -- already moved, or wrong directory"
assert not DST.exists(), "scripts/font.sh already exists"

# ---------------------------------------------------------- verify everything first
planned, problems = {}, []
for path, old, new, want in EDITS:
    p = ROOT / path
    if not p.exists():
        problems.append(f"{path}: file not found")
        continue
    s = planned.get(path, p.read_text(encoding="utf-8"))
    got = s.count(old)
    if got != want:
        problems.append(f"{path}: expected {want} of {old.strip()!r}, found {got}")
        continue
    planned[path] = s.replace(old, new)

if problems:
    print("REFUSING -- nothing has been touched.\n")
    for p in problems:
        print("  " + p)
    print("\nAn anchor has drifted since 2026-08-23. Re-read the file and fix the")
    print("anchor rather than loosening it; a loosened anchor is how the trigger")
    print("path gets missed.")
    sys.exit(1)

print(f"all {len(EDITS)} anchors found across {len(planned)} files\n")
for path in planned:
    print(f"  {path}")

if not APPLY:
    print("\nDRY RUN -- nothing written. Re-run with --apply.")
    sys.exit(0)

# ------------------------------------------------------------------ move, then write
font_body = planned.pop("font.sh")
r = subprocess.run(["git", "mv", "font.sh", "scripts/font.sh"], capture_output=True, text=True)
if r.returncode != 0:
    print("git mv failed, nothing else written:\n" + r.stderr)
    sys.exit(1)
DST.write_text(font_body, encoding="utf-8")
for path, body in planned.items():
    (ROOT / path).write_text(body, encoding="utf-8")

# --------------------------------------------------------------------- proof gate
# Enumerated from `git ls-files`, not from the directory. The gate's question is
# "does anything that SHIPS still point at the old path" -- and this script does
# not ship. Walking the tree scans it, its own docstring names the old path
# twenty times explaining what it is replacing, and the gate false-fails on a
# move that worked. A guard that false-fails gets loosened, and a loosened guard
# is how the real miss gets through. Check the tracked set, not the disk.
tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
stray = []
for rel in tracked:
    f = ROOT / rel
    if not f.is_file():
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if "font.sh" in line.replace("scripts/font.sh", ""):
            stray.append(f"{rel}:{i}: {line.strip()}")

assert DST.exists() and not SRC.exists(), "the move did not take"
import os
assert os.access(DST, os.X_OK), "the executable bit did not survive git mv"

if stray:
    print("\nPROOF GATE FAILED -- these still point at the old path:")
    for s in stray:
        print("  " + s)
    print("\nRecover with: git mv scripts/font.sh font.sh && git checkout -- .")
    sys.exit(1)

print("\nmoved. no reference to the old path remains, executable bit intact.")
print("Commit the move and the YAML edit TOGETHER -- GitHub runs a workflow from")
print("the commit that triggered it, and splitting them leaves a window where CI")
print("runs `bash font.sh` against a file that is gone.")
