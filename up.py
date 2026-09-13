#!/usr/bin/env python3
"""Site: mirror web-code into the template, and underline prose links.

Built against rnvizion.github.io @ main, every file fetched 2026-09-12.
Run from repo root.

    python3 code.py            # DRY RUN -- reports, writes nothing
    python3 code.py --apply

TWO CHANGES, ONE PASS, because they touch the same rules in the same files.

1. WEB-CODE STOPS BORROWING THE ACCENT. `engine/brand.py` registered
   BRAND_WEB_CODE = #00b0a0 on 2026-09-12 and emits --rnv-code. The site mirrors
   brand values into its own unprefixed :root, so it gets `--code`. Until now the
   value was registered and the page was still painting code gold.

   The border goes with it. Measured 1.049:1 against its own chip and rendered at
   4x against the real faces: bordered and unbordered are indistinguishable. The
   chip stays -- at 1.147:1 it reads plainly, which is the same arithmetic and the
   opposite outcome, because area and stroke width change what a ratio buys.

   Only _templates/post-template.html defines `article code`. No published post
   uses <code> at all, so this token has never rendered on a live page.

2. PROSE LINKS GET A REST-STATE UNDERLINE. Gold on body text is 1.517:1 where
   WCAG 1.4.1 wants 3:1 when colour is the only distinguishing feature. The site
   sets `text-decoration: none` and underlines on hover -- and hover does not
   exist on touch and is absent while a page is being read.

   SCOPED TO RUNNING TEXT, deliberately. `article p a`, `article li a` and
   `.bio a` -- not nav, footer or post-footer, which are link REGIONS rather than
   links embedded in prose, where colour is not the only cue because position is.

WHAT THIS PASS DOES NOT COVER, enumerated rather than left implied:
  bio/index.html   1 prose link
  aiii/index.html  2 prose links
Both carry prose links outside any <article> and outside .bio, so they need their
own selectors. resume/, index.html and blog/index.html have none -- their links
are all in regions. Left for a second pass rather than guessed at.
"""
import pathlib
import sys

APPLY = "--apply" in sys.argv
ROOT = pathlib.Path(".")

TEMPLATE = "_templates/post-template.html"
POSTS = [
    "blog/sloth/index.html",
    "blog/squish/index.html",
    "blog/fit-over-default/index.html",
    "blog/i-lacked-the-tools/index.html",
    "blog/the-job-was-never-coding/index.html",
    "blog/ask-the-corpus/index.html",
]

TOKEN_OLD = "      --accent: #d2bc93;"
TOKEN_NEW = ("      --accent: #d2bc93;\n"
             "      /* Inline code. Registered as BRAND_WEB_CODE 2026-09-12 and emitted\n"
             "         upstream as --rnv-code; mirrored here under the site's unprefixed\n"
             "         names. Reads 6.3277:1 on --bg-3, which is the only ground it ever\n"
             "         sits on because code is always chipped. Clears AA at 14.96px; it\n"
             "         would clear AAA unchipped at 7.2588, and the chip is worth the 0.93. */\n"
             "      --code: #00b0a0;")

CODE_OLD = """    article code {
      font-family: var(--font-mono);
      font-size: 0.88em;
      color: var(--accent);
      background: var(--bg-3);
      border: 1px solid var(--border-soft);
      border-radius: 4px;
      padding: 1px 6px;
    }"""
CODE_NEW = """    article code {
      font-family: var(--font-mono);
      /* 0.88em is an optical correction, not a shrink: mono carries a larger
         x-height than Inter, so parity makes code look bigger than its text.
         At 17px body this is 14.96px -- NORMAL text, so the floor is 4.5. */
      font-size: 0.88em;
      color: var(--code);
      /* The chip does the separating; a border used to sit here and did not.
         1.049:1 against this background, indistinguishable at 4x against the
         real faces. The chip is 1.147:1 and reads plainly -- same arithmetic,
         opposite outcome, because area and stroke width change what a ratio
         buys. Do not add it back to "define" the chip; it never defined it. */
      background: var(--bg-3);
      border-radius: 4px;
      padding: 1px 6px;
    }"""

LINK_ANCHOR = "    a:hover { text-decoration: underline; text-underline-offset: 3px; }"
LINK_NEW = LINK_ANCHOR + """

    /* Links in RUNNING TEXT are underlined at rest. Gold against body text is
       1.517:1 where WCAG 1.4.1 wants 3:1 when colour is the only cue, and a
       hover underline is not a cue: it does not exist on touch and is absent
       while the page is being read.

       Scoped to prose on purpose. nav, footer and post-footer are link REGIONS
       -- position tells you they are links, so colour is not doing it alone.
       Do not promote this to a bare `a`. */
    article p a, article li a, .bio a {
      text-decoration: underline;
      text-underline-offset: 3px;
      text-decoration-thickness: 1px;
    }"""

planned, problems, notes = {}, [], []

def plan(path, old, new, label):
    p = ROOT / path
    if not p.exists():
        problems.append(f"{path}: not found")
        return
    body = planned.get(path, p.read_text(encoding="utf-8"))
    c = body.count(old)
    if c != 1:
        problems.append(f"{path}: {label} -- expected 1 anchor, found {c}")
        return
    planned[path] = body.replace(old, new)
    notes.append(f"{path}: {label}")

# 1. the code token -- template only
plan(TEMPLATE, TOKEN_OLD, TOKEN_NEW, "add --code to :root")
plan(TEMPLATE, CODE_OLD, CODE_NEW, "article code -> var(--code), border removed")

# 2. prose links -- template and every post
for f in [TEMPLATE] + POSTS:
    plan(f, LINK_ANCHOR, LINK_NEW, "underline prose links")

if problems:
    print("REFUSING -- nothing written.\n")
    for x in problems:
        print("  " + x)
    sys.exit(1)

print("all anchors found\n")
for x in notes:
    print("  " + x)

if not APPLY:
    print("\nDRY RUN. Re-run with --apply.")
    sys.exit(0)

for path, body in planned.items():
    (ROOT / path).write_text(body, encoding="utf-8")

t = (ROOT / TEMPLATE).read_text(encoding="utf-8")
assert "--code: #00b0a0;" in t, "token did not land"
assert "color: var(--code);" in t, "code rule still points at the accent"
assert "border: 1px solid var(--border-soft);\n      border-radius: 4px;" not in t, "border survived"
for f in [TEMPLATE] + POSTS:
    assert "article p a, article li a, .bio a {" in (ROOT / f).read_text(encoding="utf-8"), f"{f}: link rule missing"

print("\n%d files written." % len(planned))
print("Not covered, and not guessed at: bio/index.html (1 prose link) and")
print("aiii/index.html (2) carry prose outside <article> and .bio. Second pass.")
