#!/usr/bin/env python3
"""Strip reasoning and instructions from the template and every post.
Structural markers stay.

Built against rnvizion.github.io @ main, read 2026-09-15. Run from repo root.

    python3 strip.py                      # DRY RUN
    python3 strip.py --apply
    python3 strip.py --apply path/to/draft/index.html

RUN _templates/post-template.RULES.md FIRST. This removes the only copy of
reasoning that prevented four real errors in the week before it was written.
The script refuses if the paired file is absent.

THE LINE THIS DRAWS. A comment that LABELS a section stays. A comment that
EXPLAINS a decision or INSTRUCTS an author goes -- the first is navigation for
anyone reading the page, the second is addressed to whoever edits the template
and has no audience in a published post.

  KEPT, by explicit allowlist rather than by heuristic:
      <!-- Open Graph -->               x8 across the posts
      <!-- Fonts -->                    x8
      <!-- Blog-index card teaser. -->  x3
      <!-- Standing author bio. -->     normalised, see below

  STRIPPED: every /* */ in <style>, and every HTML comment not on the list --
  the template header block, the post-body spine note, the drop-cap note, the
  repeat-blocks note.

AN ALLOWLIST, NOT A RULE ABOUT LENGTH. "Short comments stay" would be a
heuristic, and the first four-word instruction would defeat it silently. Four
names, checked exactly. A fifth marker is a deliberate decision someone makes by
adding a line here.

TWO NORMALISATIONS, because a label and an instruction currently share a comment:

  <!-- Standing author bio. Ships on every post; keep in sync with /bio/. -->
      -> <!-- Standing author bio. -->
  The label is navigation. "Keep in sync with /bio/" is an instruction and lives
  in RULES.md.

  The template's four-line card-teaser comment -> <!-- Blog-index card teaser. -->
  matching what the posts already carry. The reasoning -- that it is not
  og:description, that curly quotes protect the attribute -- is in RULES.md.

  Both leave the template and the posts carrying the same four markers, which
  they do not today.

IT WALKS blog/*/index.html plus the template plus any path given as an argument.
No hardcoded list: one built today is wrong the day a post ships, and that has
already happened on this repo.

THE DATA-URI IS PROTECTED. body::after holds an SVG noise texture in a quoted
attribute. Quoted values are held aside before the CSS stripper runs, and a
post-condition asserts feTurbulence survives in every file.
"""
import pathlib
import re
import sys

APPLY = "--apply" in sys.argv
EXTRA = [a for a in sys.argv[1:] if not a.startswith("--")]
ROOT = pathlib.Path(".")

RULES = ROOT / "_templates" / "post-template.RULES.md"
assert RULES.exists(), (
    "_templates/post-template.RULES.md is missing. It is the new home for every\n"
    "comment this script removes. Land it first; this refuses rather than lose it."
)

KEEP = {
    "<!-- Open Graph -->",
    "<!-- Fonts -->",
    "<!-- Blog-index card teaser. -->",
    "<!-- Standing author bio. -->",
}

NORMALISE = [
    (re.compile(r"<!--\s*Standing author bio\..*?-->", re.S), "<!-- Standing author bio. -->"),
    (re.compile(r"<!--\s*Blog-index card teaser\..*?-->", re.S), "<!-- Blog-index card teaser. -->"),
]

CSS_C = re.compile(r"[ \t]*/\*.*?\*/[ \t]*\n?", re.S)
HTML_C = re.compile(r"[ \t]*<!--.*?-->[ \t]*\n?", re.S)


def strip(text):
    for pat, rep in NORMALISE:
        text = pat.sub(rep, text)

    m = re.search(r"(<style>)(.*?)(</style>)", text, re.S)
    if m:
        head, css, tail = m.group(1), m.group(2), m.group(3)
        holds = []

        def hold(x):
            holds.append(x.group(0))
            return "\x00%d\x00" % (len(holds) - 1)

        css = re.sub(r'"[^"]*"', hold, css)
        css = CSS_C.sub("", css)
        css = re.sub(r"\x00(\d+)\x00", lambda x: holds[int(x.group(1))], css)
        css = re.sub(r"\n{3,}", "\n\n", css)
        text = text[: m.start()] + head + css + tail + text[m.end():]

    def drop(match):
        body = match.group(0).strip()
        return match.group(0) if body in KEEP else ""

    text = HTML_C.sub(drop, text)
    return re.sub(r"\n{3,}", "\n\n", text)


targets = sorted(ROOT.glob("blog/*/index.html"))
tpl = ROOT / "_templates" / "post-template.html"
if tpl.exists():
    targets.append(tpl)
targets += [pathlib.Path(p) for p in EXTRA if pathlib.Path(p).exists()]
assert targets, "nothing found -- run from the repo root"

rows, planned = [], {}
for p in targets:
    body = p.read_text(encoding="utf-8")
    out = strip(body)
    rows.append((p,
                 body.count("/*") - out.count("/*"),
                 body.count("<!--") - out.count("<!--"),
                 len(body) - len(out)))
    if out != body:
        planned[p] = out

print("%-42s %6s %6s %8s" % ("file", "css", "html", "bytes"))
for p, c, h, b in rows:
    print("  %-40s %6d %6d %8d" % (p, c, h, b))
print("\n%d files to change" % len(planned))

if not APPLY:
    print("\nDRY RUN -- nothing written. Re-run with --apply.")
    sys.exit(0)

for p, out in planned.items():
    p.write_text(out, encoding="utf-8")

for p in targets:
    after = p.read_text(encoding="utf-8")
    left = {c.strip() for c in HTML_C.findall(after)}
    stray = left - KEEP
    assert not stray, "%s: unexpected comment survives: %s" % (p, stray)
    style = re.search(r"<style>(.*?)</style>", after, re.S)
    if style:
        css = re.sub(r'"[^"]*"', "", style.group(1))
        assert "/*" not in css, "%s: a CSS comment survives" % p
    assert "feTurbulence" in after, "%s: the noise data-URI was mangled" % p
    assert "</html>" in after, "%s: the document was truncated" % p
    assert "<!-- Open Graph -->" in after, "%s: a marker was eaten" % p

print("\n%d files written. Markers kept; the rules live in %s." % (len(planned), RULES))
