#!/usr/bin/env python3
"""Finish the prose-link pass by walking, and retire a comment the last one made false.

Built against rnvizion.github.io @ main, read 2026-09-12. Run from repo root.

    python3 fix.py            # DRY RUN
    python3 fix.py --apply

TWO THINGS, BOTH LEFT BY THE EARLIER PASS.

1. IT WALKS. The earlier pass carried a hardcoded list of six posts, built from a
   blog-index scrape done in August. Two posts shipped since -- honest-and-wrong
   and the-margin-not-the-price -- and the list could not know that. There are
   eight, six got the rule, two did not.

   This is Domain 1's own rule, ignored by the project that wrote it:
   **enumerate by walking the repo, never from a list; a list is wrong the day a
   page is added and cannot be checked.** It was written about the nav dot in
   August and set aside a month later, because a list that was right once feels
   like knowledge rather than a snapshot.

   So: glob blog/*/index.html, report the total, edit what is missing, and let
   the number be whatever it is.

2. A COMMENT THE LAST CHANGE MADE FALSE. The code rule's header still reads
   "Existing tokens only; no new colours or faces." True when the rule used
   var(--accent); false since --code: #00b0a0 was introduced by the same pass
   that left it standing -- and it sits INSIDE the rule that contradicts it,
   which is the one place a reader will trust it over the code.

   Retire a phrase in the same change that makes it stale. This is that change,
   one pass late.
"""
import pathlib
import sys

APPLY = "--apply" in sys.argv
ROOT = pathlib.Path(".")

RULE_MARK = "article p a, article li a, .bio a"
ANCHOR = "    a:hover { text-decoration: underline; text-underline-offset: 3px; }"
ADDITION = ANCHOR + """

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

OLD_COMMENT = """    /* Inline code token, for markup names, file paths and identifiers in prose:
       <code>&lt;article&gt;</code>. Existing tokens only; no new colours or faces. */"""
NEW_COMMENT = """    /* Inline code token, for markup names, file paths and identifiers in prose:
       <code>&lt;article&gt;</code>. Carries its own colour -- --code, registered
       upstream as BRAND_WEB_CODE and emitted there as --rnv-code. It used to say
       "existing tokens only; no new colours or faces", which was true while this
       rule used var(--accent) and false from the moment --code arrived. The
       sentence outlived its change by one pass, sitting inside the rule that
       contradicted it. */"""

posts = sorted(ROOT.glob("blog/*/index.html"))
assert posts, "no posts found -- run from the repo root"

missing, present = [], []
for p in posts:
    body = p.read_text(encoding="utf-8")
    (present if RULE_MARK in body else missing).append(p)

print(f"posts found by walking: {len(posts)}")
print(f"  already have the rule: {len(present)}")
print(f"  missing it:            {len(missing)}")
for p in missing:
    print(f"     {p}")

planned = {}
problems = []
for p in missing:
    body = p.read_text(encoding="utf-8")
    c = body.count(ANCHOR)
    if c != 1:
        problems.append(f"{p}: expected 1 anchor, found {c}")
        continue
    planned[p] = body.replace(ANCHOR, ADDITION)

tpl = ROOT / "_templates/post-template.html"
if not tpl.exists():
    problems.append("_templates/post-template.html: not found")
else:
    body = tpl.read_text(encoding="utf-8")
    c = body.count(OLD_COMMENT)
    if c != 1:
        problems.append(f"template comment: expected 1 match, found {c}")
    else:
        planned[tpl] = body.replace(OLD_COMMENT, NEW_COMMENT)
        print("\n  template: retiring the 'existing tokens only' comment")

if problems:
    print("\nREFUSING -- nothing written.\n")
    for x in problems:
        print("  " + x)
    sys.exit(1)

if not planned:
    print("\nnothing to do.")
    sys.exit(0)

if not APPLY:
    print("\nDRY RUN -- nothing written. Re-run with --apply.")
    sys.exit(0)

for p, body in planned.items():
    p.write_text(body, encoding="utf-8")

still = [p for p in sorted(ROOT.glob("blog/*/index.html"))
         if RULE_MARK not in p.read_text(encoding="utf-8")]
assert not still, f"still missing the rule: {still}"
t = tpl.read_text(encoding="utf-8")
# Assert on the BLOCK replaced, not on a phrase. The new comment quotes the old
# sentence as history -- house style throughout these registers -- so a bare
# absence check finds the quotation and fails a change that worked. Eighth time
# this trap has fired here. The habit: assert on the structure you replaced,
# never on a phrase your own prose might quote.
assert OLD_COMMENT not in t, "the old comment block survives"
assert "Carries its own colour" in t, "the replacement did not land"
assert "color: var(--code);" in t, "the code rule was disturbed"

print(f"\n{len(planned)} files written. Every post under blog/ now carries the rule.")
