#!/usr/bin/env python3
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

G, R, Y, C, D, N = ("\033[32m", "\033[31m", "\033[33m",
                    "\033[36m", "\033[2m", "\033[0m")


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


def main() -> int:
    apply = "--apply" in sys.argv
    if not Path(".git").is_dir():
        print(f"{R}Run this from the rnvizion.github.io repo root.{N}")
        return 2
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
