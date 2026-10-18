#!/usr/bin/env python3
"""American spelling in code comments and template docs, rnvizion.github.io.
Built from: rnvizion.github.io@4c3e3d0, read 2026-10-18. Run from the repo root.
All or nothing: every edit is checked (count == 1) before any file is written.
Left as written, on purpose: page copy and captions on demos/rnv-publishing-agent/
(voice), tests/fixtures/golden-post/index.html (frozen fixture), and the vector id
"script-is-behaviour" (an identifier)."""
import pathlib
EDITS = {
 ".devcontainer/devcontainer.json": [("// neighbouring repo.", "// neighboring repo.")],
 "_templates/post-card-template.RULES.md": [("was travelling into the blog index", "was traveling into the blog index")],
 "_templates/post-template.RULES.md": [
   ("**Colour is `var(--code)`", "**Color is `var(--code)`"),
   ("WCAG 1.4.1 wants 3:1 when colour is\nthe only cue", "WCAG 1.4.1 wants 3:1 when color is\nthe only cue"),
   ("so colour is not doing the work alone there", "so color is not doing the work alone there"),
   ("because every pass was about\ncolour.", "because every pass was about\ncolor.")],
 "bio/index.html": [
   ("wants 3:1 when colour is the only cue", "wants 3:1 when color is the only cue"),
   ("so colour is not doing it alone.", "so color is not doing it alone.")],
 "index.html": [("without it this\n         colour fails.", "without it this\n         color fails.")],
 "scripts/build_feed.py": [("forward elsewhere and canonicalise away", "forward elsewhere and canonicalize away")],
 "scripts/font.sh": [("# Target directory honours OG_FONT_DIR", "# Target directory honors OG_FONT_DIR")],
 "scripts/post_shape.py": [("so it is neutralised before scanning", "so it is neutralized before scanning")],
 "tests/fixtures/post-shape-vectors.json": [('"why": "neutralising escaped markup', '"why": "neutralizing escaped markup')],
}
out = {}
for path, edits in EDITS.items():
    s = pathlib.Path(path).read_text(encoding="utf-8")
    for old, new in edits:
        n = s.count(old)
        assert n == 1, f"{path}: expected 1 of {old!r}, found {n} (already applied, or the file moved: re-read it)"
        s = s.replace(old, new)
        assert s.count(new) == 1, f"{path}: {new!r} not unique after the edit"
    out[path] = s
for path, s in out.items():
    pathlib.Path(path).write_text(s, encoding="utf-8")
print(f"ok: {sum(len(e) for e in EDITS.values())} edits in {len(EDITS)} files")
