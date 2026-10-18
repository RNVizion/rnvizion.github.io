#!/usr/bin/env python3
"""American spelling in code comments, rnv-live.
Built from: rnv-live@82143bc, read 2026-10-18. Run from the repo root.
All or nothing: every edit is checked (count == 1) before the file is written."""
import pathlib
PATH = "src/pages/index.astro"
EDITS = [
 ("unnoticed because everyone was looking at the colour. */", "unnoticed because everyone was looking at the color. */"),
 ("It is still clearly a different colour", "It is still clearly a different color"),
 ("the colour is claiming something the word contradicts", "the color is claiming something the word contradicts"),
 ("it has to agree with the colour and the label", "it has to agree with the color and the label"),
 ("fight its own colour --", "fight its own color --"),
]
s = pathlib.Path(PATH).read_text(encoding="utf-8")
for old, new in EDITS:
    n = s.count(old)
    assert n == 1, f"{PATH}: expected 1 of {old!r}, found {n} (already applied, or the file moved: re-read it)"
    s = s.replace(old, new)
    assert s.count(new) == 1, f"{PATH}: {new!r} not unique after the edit"
assert "colour" not in s, f"{PATH}: a 'colour' remains"
pathlib.Path(PATH).write_text(s, encoding="utf-8")
print(f"ok: {len(EDITS)} edits in {PATH}")
