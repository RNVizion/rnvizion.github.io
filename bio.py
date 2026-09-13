#!/usr/bin/env python3
"""bio/index.html: the prose-link rule, which the earlier pass missed.

Built against rnvizion.github.io/bio/index.html @ main, fetched 2026-09-12.
Run from repo root.

    python3 bio.py            # DRY RUN
    python3 bio.py --apply

WHY IT WAS MISSED, because the reason matters more than the fix. The earlier
pass enumerated prose links with a regex that matched `<p...>` followed
immediately by `<a `. It could not see past an intervening tag, so a link later
in a paragraph was invisible to it. bio/index.html reported ONE prose link and
has FOUR; three of them sit after a `<strong>` or mid-sentence on the same line.

  **An enumeration that undercounts reports success, not failure.** A search that
  misses returns fewer hits, which looks exactly like a smaller problem. Nothing
  about the output says the method was wrong.

AND THE PAGE NEEDED NO NEW SELECTOR AT ALL. Its prose sits inside `<article>`,
the same as every post, so `article p a` already covers it -- bio was simply
absent from the file list. The earlier pass recorded it as needing "its own
selectors", which was a conclusion drawn from a bad count rather than from
reading the page.

aiii/index.html NEEDS NOTHING AND NEVER DID. Its `.byline a` and `footer.foot a`
both carry `border-bottom: 1px solid var(--hair)` -- a non-colour cue at rest,
which is what 1.4.1 asks for. It has no links inside `<article>` at all. It was
listed as failing on the same bad enumeration.
"""
import pathlib
import sys

APPLY = "--apply" in sys.argv
P = pathlib.Path("bio/index.html")

assert P.exists(), "run from the repo root"
s = P.read_text(encoding="utf-8")

assert "article p a, article li a, .bio a" not in s, "the rule is already present"
assert "<article>" in s, "bio's prose is not in an <article>; the selector would not reach it"

OLD = "    a:hover { text-decoration: underline; text-underline-offset: 3px; }"
NEW = OLD + """

    /* Links in RUNNING TEXT are underlined at rest. Gold against body text is
       1.517:1 where WCAG 1.4.1 wants 3:1 when colour is the only cue, and a
       hover underline is not a cue: it does not exist on touch and is absent
       while the page is being read.

       Identical to the rule in _templates/post-template.html and every post --
       this page's prose is inside <article> like theirs, so it takes the same
       selector. It was missed in the first pass by an enumeration that
       undercounted, not by needing anything different.

       Scoped to prose on purpose. nav, footer and post-footer are link REGIONS
       -- position tells you they are links, so colour is not doing it alone.
       Do not promote this to a bare `a`. */
    article p a, article li a, .bio a {
      text-decoration: underline;
      text-underline-offset: 3px;
      text-decoration-thickness: 1px;
    }"""

n = s.count(OLD)
assert n == 1, f"expected 1 anchor, found {n}. Base has moved."

import re
prose_links = len(re.findall(r"<a ", s[s.index("<article>"):s.index("</article>")]))
print(f"prose links inside <article>: {prose_links}")

if not APPLY:
    print("anchor found. DRY RUN -- nothing written. Re-run with --apply.")
    sys.exit(0)

s = s.replace(OLD, NEW)
P.write_text(s, encoding="utf-8")

after = P.read_text(encoding="utf-8")
assert "article p a, article li a, .bio a {" in after, "rule did not land"
assert after.count("a:hover { text-decoration: underline") == 1, "hover rule disturbed"
print("bio/index.html: prose links underlined at rest.")
print("aiii/index.html: nothing to do -- its links already carry a border-bottom.")
