#!/usr/bin/env python3
<<<<<<< HEAD
"""Normalise the post description to Brand Book section 5, row 18.

    python up.py            # check: writes nothing
    python up.py --apply    # write

Run from the rnvizion.github.io repo root.

Row 18 registers the line as:

    Gate what you're judging -- warn about what you're waiting on.

Capital G, em dash, lowercase "warn". This repairs the description to that form
from ANY punctuation or capitalisation it currently carries -- comma, semicolon,
hyphen, literal em dash, entity em dash, capital or lowercase G. An earlier
script fixed the dash and left the capital, which is a third variant rather than
a repair; matching on one exact form could not see the result of its own
predecessor.

The dash it writes matches the apostrophe encoding already in the line: entity
apostrophes get `&#8212;`, literal ones get a literal em dash. Where a file has
a house encoding, the file's encoding wins.

WHEN IT FINDS NOTHING IT PRINTS WHAT IS THERE. A script that reports only what
it failed to match tells you nothing about the state you are actually in, which
is the dead end this replaces.

It does not commit, stage, or push. It writes one named file and reports every
other occurrence in the repo without touching it -- feed.xml is generated from
og:description by scripts/build_feed.py and rebuilds itself on push.
"""

import re
import sys
from pathlib import Path

POST = Path("blog/the-warning-not-the-gate/index.html")

APOS = r"(?:&#8217;|\u2019|')"
SEP = r"(?:,|;|&#8212;|&mdash;|\u2014|\u2013|--|-)"

PAT = re.compile(
    r"(blocking:\s*)"
    r"[Gg](ate what you)(" + APOS + r")(re judging)"
    r"\s*" + SEP + r"\s*"
    r"(warn about)"
)

# Anything carrying the line at all, in any form, for the report and for the
# "what is actually there" dump.
ANY = re.compile(r"judging\s*(?:,|;|&#8212;|&mdash;|\u2014|\u2013|--|-)\s*warn about")

=======
"""Point the resume at the publishing-agent demo. Two guarded edits.

    python resume_demo.py            # check: writes nothing
    python resume_demo.py --apply    # write

Run from the rnvizion.github.io repo root.

WHAT IT CHANGES
  1. The nav gains a Demos link, after Work. Every other page carrying a nav
     already has one; resume/index.html is the only one that does not, because
     its nav block is `<div class="nav-links">` with no id and the earlier pass
     matched on the id. That pass named this file in its no-nav list and the
     file was never fixed -- printing a finding is not applying one.

  2. The RNV Publishing Agent entry gains the demo URL, in the same shape the
     AIII entry already uses for a second link: url-as-text, `proj-url` class,
     at the end of the prose.

THE SENTENCE IS YOURS. It is a named constant below, on its own line. Reword it
before running; the guards do not depend on its content. The entry already uses
the word "demo" for the self-contained chain test that runs in CI, so this one
says "walkthrough" -- two things called demo in one paragraph is a name
collision, not a style question.

WHAT IT DELIBERATELY DOES NOT DO
  It does not commit, stage, or push. Each edit asserts exactly one match and
  aborts otherwise. It is idempotent by a marker unique to the patched form,
  never by an anchor that survives the patch.

  It does not touch the resume's missing mobile layout. That page carries zero
  @media queries and no nav toggle where every other page has both, so the nav
  it is gaining will sit unwrapped on a phone. Reported, not fixed: it is a
  different change and it is not what was asked for.
"""

import sys
from pathlib import Path

PAGE = Path("resume/index.html")
URL = "https://rnvizion.dev/demos/rnv-publishing-agent/"

# --- edit 1: nav -----------------------------------------------------------
NAV_ANCHOR = '        <a href="/#work">Work</a>\n'
NAV_ADD = '        <a href="/demos/">Demos</a>\n'

# --- edit 2: the project entry ---------------------------------------------
PROSE_ANCHOR = "and CI runs both on every push."

# Reword this freely. It is appended to the sentence that already ends the
# entry, matching the AIII entry's "Source at <url>" shape.
PROSE_ADD = (
    ' Recorded walkthrough at <a class="proj-url" href="'
    + URL
    + '">rnvizion.dev/demos/rnv-publishing-agent</a>.'
)

>>>>>>> 7fa62b9afda2797032c225872dfa7fcd7b8d46f0
G, R, Y, C, D, N = ("\033[32m", "\033[31m", "\033[33m",
                    "\033[36m", "\033[2m", "\033[0m")


<<<<<<< HEAD
def fix(m: re.Match) -> str:
    apos = m.group(3)
    dash = "&#8212;" if apos == "&#8217;" else "\u2014"
    return f"{m.group(1)}G{m.group(2)}{apos}{m.group(4)} {dash} {m.group(5)}"


def show(path: Path, text: str, label: str) -> None:
    print(f"{D}  {label}{N}")
    hit = False
    for i, ln in enumerate(text.splitlines(), 1):
        if "judging" in ln or "warn about" in ln:
            hit = True
            s = ln.strip()
            at = max(s.find("blocking:"), 0)
            print(f"{D}    {i:>4}: ...{s[at:at + 110]}{N}")
    if not hit:
        print(f"{D}      (no line in this file mentions the aphorism at all){N}")


=======
>>>>>>> 7fa62b9afda2797032c225872dfa7fcd7b8d46f0
def main() -> int:
    apply = "--apply" in sys.argv
    if not Path(".git").is_dir():
        print(f"{R}Run this from the rnvizion.github.io repo root.{N}")
        return 2
<<<<<<< HEAD
    if not POST.is_file():
        print(f"{R}{POST} not found. Nothing written.{N}")
        return 2

    src = POST.read_text(encoding="utf-8")
    out, n = PAT.subn(fix, src)

    print(f"{C}== {POST} =={N}")
    if n == 0:
        print(f"  {R}no description form matched.{N}")
        show(POST, src, "every line in the file that mentions the line:")
        print(f"\n{Y}Nothing written. Send the block above and I will match it exactly.{N}")
        return 1

    if out == src:
        print(f"  {G}already in the registry form{N}  ({n} occurrence(s) checked)")
        changed = False
    else:
        print(f"  {G}{n} occurrence(s){N} -> capital G + em dash")
        show(POST, src, "before:")
        show(POST, out, "after:")
        changed = True

    others = []
    me = Path(__file__).resolve()
    for p in sorted(Path(".").rglob("*")):
        if not p.is_file() or ".git" in p.parts or p.resolve() == me or p == POST:
            continue
        if p.suffix.lower() not in (".html", ".xml", ".vtt", ".json", ".md", ".txt"):
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        bad = [m.group(0) for m in ANY.finditer(s)
               if "&#8212;" not in m.group(0) and "\u2014" not in m.group(0)]
        if bad:
            others.append((p, len(bad)))

    if others:
        print(f"\n{Y}== carries an old form, not written ({len(others)}) =={N}")
        for p, c in others:
            print(f"  {Y}{p}{N}  x{c}")
        print(f"{D}      Generated from the post by scripts/build_feed.py;{N}")
        print(f"{D}      build-feed.yml rebuilds these on any push under blog/**.{N}")

    if not apply:
        print(f"\n{Y}Check only. Nothing written.{N}")
        print("  Re-run with --apply to write." if changed else "  Nothing to write.")
        return 0

    if changed:
        POST.write_text(out, encoding="utf-8")
        print(f"\n{G}wrote{N}  {POST}")
        print(f"\n{G}Nothing staged, nothing committed.{N}")
        print("  git diff --stat")
    else:
        print(f"\n{G}Nothing to write.{N}")
=======
    if not PAGE.is_file():
        print(f"{R}{PAGE} not found. Nothing written.{N}")
        return 2

    src = PAGE.read_text(encoding="utf-8")
    out = src
    did = []
    print(f"{C}== {PAGE} =={N}")

    # 1. nav ----------------------------------------------------------------
    if 'href="/demos/"' in out:
        print(f"  {Y}skip{N}   nav already carries Demos")
    else:
        n = out.count(NAV_ANCHOR)
        if n != 1:
            print(f"  {R}stop{N}   nav Work link found {n} time(s), expected 1")
            print(f"{D}           the nav is not shaped the way this script believes;{N}")
            print(f"{D}           nothing written.{N}")
            return 1
        out = out.replace(NAV_ANCHOR, NAV_ANCHOR + NAV_ADD, 1)
        did.append("nav: Demos added after Work")

    # 2. project entry ------------------------------------------------------
    if URL in out:
        print(f"  {Y}skip{N}   entry already links the demo")
    else:
        n = out.count(PROSE_ANCHOR)
        if n != 1:
            print(f"  {R}stop{N}   entry anchor found {n} time(s), expected 1")
            print(f"{D}           the RNV Publishing Agent prose has moved;{N}")
            print(f"{D}           nothing written.{N}")
            return 1
        out = out.replace(PROSE_ANCHOR, PROSE_ANCHOR + PROSE_ADD, 1)
        did.append("entry: demo URL appended to the prose")

    if not did:
        print(f"\n  {G}nothing to change.{N}")
        return 0

    for d in did:
        print(f"  {G}ok{N}     {d}")

    # Show both edits as they will read, so the wording is reviewed before it
    # is written rather than after it is pushed.
    a = out.find('<div class="nav-links"')
    b = out.find("</div>", a)
    print(f"\n{D}  nav, after:{N}")
    for ln in out[a:b].splitlines():
        if ln.strip():
            print(f"{D}    {ln.rstrip()}{N}")

    print(f"\n{D}  entry, after:{N}")
    i = out.find(PROSE_ANCHOR)
    print(f"{D}    ...{out[i:i + 170]}{N}")

    if not apply:
        print(f"\n{Y}Check only. Nothing written.{N}")
        print("  Re-run with --apply once the wording above is what you want.")
        return 0

    PAGE.write_text(out, encoding="utf-8")
    print(f"\n{G}wrote{N}  {PAGE}")
    print(f"\n{G}Nothing staged, nothing committed.{N}")
    print("  git diff --stat")
>>>>>>> 7fa62b9afda2797032c225872dfa7fcd7b8d46f0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
