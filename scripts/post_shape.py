#!/usr/bin/env python3
"""
post_shape.py — the reference rule and the shown-markup rule, as functions.

WHY THIS IS A LIBRARY AND NOT A TEST
  Two consumers read a post for references: tests/test_post_shape.py, which
  walks the whole tree in build-feed, and the RNV publishing agent, which
  checks the one document it is about to push. The agent holds the
  irreversible step; this repo's check runs after Pages has already served
  the commit.

  The alternative was for the agent to keep its own copy of these two
  functions, kept honest by a shared vector file. That was rejected on
  evidence rather than taste: the semantics moved twice in three days —
  srcset became a list, and escaped markup stopped being a reference — and
  the second move is exactly the kind a copy survives quietly, reporting a
  file nobody ever wrote while being wrong about the post's real defect.
  A second checker is the same defect as a second card renderer, one layer
  down; that debt was retired for generate_card.py and is not re-taken here.

  So: one implementation, two consumers. The agent resolves BLOG_REPO to a
  sibling checkout and cannot publish without it, so this file is in hand at
  exactly the moment the check runs, and a change here reaches the agent when
  the operator pulls.

THE INTERFACE IS PUBLIC. TREAT IT THAT WAY.
  sibling_refs(html)        -> list of references resolving inside the post's
                               own folder. A publish carries the HTML only, so
                               every one of these is a file that will 404.
  shown_outside_code(html)  -> list of escaped markup found outside <code> or
                               <pre>. A wrapper mistake, not a missing file.

  Both take an HTML string and return a list of strings. Neither touches the
  filesystem, git, or the network, and importing this module does nothing at
  all — tests/test_post_shape.py pins that, because an import-time side effect
  here is a dead publish over there.

  Renaming either function, or changing what it takes or returns, breaks the
  agent's publish. That is the trade taken deliberately: a loud break beats a
  silent divergence. Send a note in the same change.

THE RULES THEMSELVES live in _templates/post-template.RULES.md, under "What a
post consists of". This file implements them; it does not define them.

USAGE (from the repo root)
  python scripts/post_shape.py blog/squish/index.html [more.html ...]

Exit code 0 = nothing found, 1 = findings printed.
"""

import re
import sys

# Schemes and roots that resolve somewhere other than the post's own folder.
# Whatever is left is a sibling, which is the whole point of this test.
ELSEWHERE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|/|#)", re.I)

# Attributes the browser fetches, plus CSS url(). Deliberately NOT a blanket
# content= sweep: most meta content is prose, and a check that fires on a page
# title is one somebody turns off.
REFS = re.compile(
    r"""(?:\bsrc|\bhref|\bposter|\bdata-src)\s*=\s*["']([^"']+)["']"""
    r"""|\burl\(\s*["']?([^"')]+)["']?\s*\)""",
    re.I,
)

# srcset is a comma-separated list with size descriptors, so the value as a
# whole is never a path. Testing it whole fails OPEN: one absolute entry at the
# front makes the rest of the list invisible.
LIST_REFS = re.compile(
    r"""(?:\bsrcset|\bimagesrcset)\s*=\s*["']([^"']+)["']""", re.I)

# Markup shown to a reader is escaped, so its attributes survive verbatim in the
# bytes: a post explaining <img src="hero.png"> carries that string without ever
# fetching it. Use and mention look identical to a regex, so the elements that
# mean "this is being shown" are cut before scanning.
SHOWN = re.compile(r"<(pre|code)\b[^>]*>.*?</\1\s*>", re.I | re.S)

# Escaped markup, tag-shaped, anywhere it survives the cut above. It is never
# a real reference, so it is neutralised before scanning; and outside <code>
# or <pre> it is the house rule being broken, which is reported on its own.
# [^<>] keeps a match from crossing a real tag, so cutting one can never
# swallow the document between two of them -- the greedy-span failure again.
# "x &lt; y" is prose, not markup, and is deliberately not matched.
ESCAPED_TAG = re.compile(r"&lt;/?[a-zA-Z][^<>]*?&gt;")

# A self-contained payload carries its own url() and quotes; scanning inside it
# reports references to things that are not files.
DATA_URI = re.compile(
    r"""url\(\s*(["'])\s*data:.*?\1\s*\)|(?:\bsrc|\bhref)\s*=\s*(["'])data:.*?\2""",
    re.I | re.S,
)

META = re.compile(r"<meta\b[^>]*>", re.I)

META_KEY = re.compile(r"""\b(?:property|name)\s*=\s*["']([^"']+)["']""", re.I)

META_VAL = re.compile(r"""\bcontent\s*=\s*["']([^"']+)["']""", re.I)

IMAGE_KEYS = {"og:image", "og:image:url", "og:image:secure_url", "twitter:image",
              "twitter:image:src", "og:audio", "og:video"}

def shown_outside_code(html):
    """Markup shown to a reader that is not marked as shown.

    Escaping hides the angle brackets, not the attributes, so this is what
    makes the reference check possible at all. Reported separately because
    the honest message is "this belongs in <code>", not "this file is
    missing" -- a refusal that names a file nobody wrote is how a correct
    guard gets read as a broken one.
    """
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = SHOWN.sub(" ", html)
    html = DATA_URI.sub(" ", html)
    return ESCAPED_TAG.findall(html)

def sibling_refs(html):
    """Every reference in the document that resolves inside the post's folder."""
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = SHOWN.sub(" ", html)
    html = ESCAPED_TAG.sub(" ", html)
    html = DATA_URI.sub(" ", html)
    found = []
    for match in REFS.finditer(html):
        ref = (match.group(1) or match.group(2) or "").strip()
        if ref and not ELSEWHERE.match(ref):
            found.append(ref)
    for match in LIST_REFS.finditer(html):
        for candidate in match.group(1).split(","):
            ref = candidate.strip().split()[0] if candidate.strip() else ""
            if ref and not ELSEWHERE.match(ref):
                found.append(ref)
    for tag in META.findall(html):
        key = META_KEY.search(tag)
        val = META_VAL.search(tag)
        if key and val and key.group(1).lower() in IMAGE_KEYS:
            ref = val.group(1).strip()
            if ref and not ELSEWHERE.match(ref):
                found.append(ref)
    return found


def _report(path, refs, shown):
    for ref in refs:
        print("%s: references %r, which resolves beside the post" % (path, ref[:80]))
    for snip in shown:
        print("%s: shows %r outside <code>/<pre>" % (path, snip[:60]))


def main(argv):
    if not argv:
        print(__doc__.strip().splitlines()[-3].strip())
        return 2
    found = False
    for path in argv:
        try:
            html = open(path, encoding="utf-8").read()
        except OSError as exc:
            print("%s: %s" % (path, exc))
            found = True
            continue
        refs, shown = sibling_refs(html), shown_outside_code(html)
        if refs or shown:
            found = True
            _report(path, refs, shown)
    if not found:
        print("clean: %d file(s)" % len(argv))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
