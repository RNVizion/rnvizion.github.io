#!/usr/bin/env python3
"""American spelling, second pass, rnvizion.github.io: a test name and a fixture comment.
Built from: rnvizion.github.io@81f9626 · AI Engineering Practices rev 27 §7.7
(existing names are renamed). Run from the repo root. All or nothing.
The vector id is read only by tests/test_post_shape.py in this repo; the publishing
agent calls scripts/post_shape.py and keeps no copy of the vectors. The fixture edit
is in its HTML comment, which is not part of the card it pins; test_card_contract
passes after it."""
import pathlib
EDITS = {
 "tests/fixtures/post-shape-vectors.json": [('"id": "script-is-behaviour"', '"id": "script-is-behavior"')],
 "tests/fixtures/golden-post/index.html": [("pin generate_card.py's rendering behaviour.", "pin generate_card.py's rendering behavior.")],
}
out = {}
for path, edits in EDITS.items():
    s = pathlib.Path(path).read_text(encoding="utf-8")
    for old, new in edits:
        n = s.count(old)
        assert n == 1, f"{path}: expected 1 of {old!r}, found {n} (already applied, or the file moved: re-read it)"
        s = s.replace(old, new)
    out[path] = s
for path, s in out.items():
    pathlib.Path(path).write_text(s, encoding="utf-8")
print("ok: 2 edits in 2 files; now run the three tests in tests/")
