#!/usr/bin/env python3
"""shape2.py -- close two gaps in the post-shape guard and give the rule a home.

Three files move, all in rnvizion.github.io:

  tests/test_post_shape.py                  six guarded edits
  tests/fixtures/post-shape-vectors.json    new; the shared vectors
  _templates/post-template.RULES.md         one guarded insertion

What changes and why:

  srcset was matched as one value, but it is a comma-separated list, so an
  absolute entry at the front made every sibling behind it invisible. That is
  the fail-open direction. Reported by the publishing agent; confirmed, and it
  is wider than reported -- a root-relative front entry does the same, and
  imagesrcset was named in the pattern without ever being matched.

  Escaped example markup was read as a real reference. A post explaining
  <img src="hero.png"> carries that string verbatim, so a post about HTML
  could not be published. That is the fail-closed direction and the worse of
  the two: a guard that refuses correct work is the one that gets switched
  off. Markup shown to a reader now has to sit in <code> or <pre>, which is
  what tells use from mention, and that rule is written down in RULES.md.

  The rule's only statement used to be this test's docstring. A rule that
  lives inside one implementation cannot be asserted by a second one without
  copying the implementation. It now lives in RULES.md; the test cites it.

Every edit is verified before anything is written: if any anchor is missing or
ambiguous the script refuses and leaves all three files untouched. Re-running
is a no-op.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, check=True).stdout.strip())

TEST = ROOT / "tests/test_post_shape.py"
VECTORS = ROOT / "tests/fixtures/post-shape-vectors.json"
RULES = ROOT / "_templates/post-template.RULES.md"

EDITS = json.loads(r'''[["Run: python tests/test_post_shape.py\n\"\"\"", "THE RULE ITSELF LIVES IN _templates/post-template.RULES.md, under \"What a post\nconsists of\". This file asserts it; it does not define it. The publishing agent\nasserts the same rule one step earlier, against the document it is about to\npush, and both sides run the vectors in tests/fixtures/post-shape-vectors.json.\nShared vectors prove the two agree where they were asked; they do not prove the\ntwo parsers agree everywhere.\n\nRun: python tests/test_post_shape.py\n\"\"\""], ["    r\"\"\"(?:\\bsrc|\\bhref|\\bposter|\\bdata-src|\\bsrcset)\\s*=\\s*[\"']([^\"']+)[\"']\"\"\"\n    r\"\"\"|\\burl\\(\\s*[\"']?([^\"')]+)[\"']?\\s*\\)\"\"\",\n    re.I,\n)\n", "    r\"\"\"(?:\\bsrc|\\bhref|\\bposter|\\bdata-src)\\s*=\\s*[\"']([^\"']+)[\"']\"\"\"\n    r\"\"\"|\\burl\\(\\s*[\"']?([^\"')]+)[\"']?\\s*\\)\"\"\",\n    re.I,\n)\n\n# srcset is a comma-separated list with size descriptors, so the value as a\n# whole is never a path. Testing it whole fails OPEN: one absolute entry at the\n# front makes the rest of the list invisible.\nLIST_REFS = re.compile(\n    r\"\"\"(?:\\bsrcset|\\bimagesrcset)\\s*=\\s*[\"']([^\"']+)[\"']\"\"\", re.I)\n\n# Markup shown to a reader is escaped, so its attributes survive verbatim in the\n# bytes: a post explaining <img src=\"hero.png\"> carries that string without ever\n# fetching it. Use and mention look identical to a regex, so the elements that\n# mean \"this is being shown\" are cut before scanning.\nSHOWN = re.compile(r\"<(pre|code)\\b[^>]*>.*?</\\1\\s*>\", re.I | re.S)\n"], ["    html = re.sub(r\"<!--.*?-->\", \" \", html, flags=re.S)\n    html = DATA_URI.sub(\" \", html)\n", "    html = re.sub(r\"<!--.*?-->\", \" \", html, flags=re.S)\n    html = SHOWN.sub(\" \", html)\n    html = DATA_URI.sub(\" \", html)\n"], ["        if ref and not ELSEWHERE.match(ref):\n            found.append(ref)\n    for tag in META.findall(html):", "        if ref and not ELSEWHERE.match(ref):\n            found.append(ref)\n    for match in LIST_REFS.finditer(html):\n        for candidate in match.group(1).split(\",\"):\n            ref = candidate.strip().split()[0] if candidate.strip() else \"\"\n            if ref and not ELSEWHERE.match(ref):\n                found.append(ref)\n    for tag in META.findall(html):"], ["failures = []\n\nposts = tracked(\"blog/*/index.html\")", "VECTORS = ROOT / \"tests/fixtures/post-shape-vectors.json\"\nvector_count = 0\n\nfailures = []\n\n# 0. The vectors first. They are written by hand as an independent statement of\n#    what the rule means -- never derived from this file -- because a test that\n#    reads its expectations out of the thing it tests cannot detect a change to\n#    that thing. The publishing agent runs this same file.\nif not VECTORS.exists():\n    failures.append(\"%s is missing; the shared vectors are how two \"\n                    \"implementations of this rule stay honest\" % VECTORS.name)\nelse:\n    import json\n    loaded = json.loads(VECTORS.read_text(encoding=\"utf-8\"))[\"vectors\"]\n    vector_count = len(loaded)\n    for vector in loaded:\n        want = sorted(vector[\"catches\"])\n        got = sorted(sibling_refs(vector[\"html\"]))\n        if got != want:\n            failures.append(\n                \"vector %s: expected %s, got %s -- %s\"\n                % (vector[\"id\"], want, got, vector[\"why\"]))\n\nposts = tracked(\"blog/*/index.html\")"], ["print(\"post shape OK: %d post(s), one tracked file each, no sibling refs\" % len(posts))", "print(\"post shape OK: %d post(s), one tracked file each, no sibling refs; \"\n      \"%d shared vector(s) green\" % (len(posts), vector_count))"]]''')
VECTOR_JSON = r'''{
  "_": [
    "Shared reference vectors for the post shape rule. This file is the site",
    "repo's, and the publishing agent runs the same file against its own",
    "implementation. If the two disagree on a vector, one of them is wrong and",
    "the disagreement is visible. Agreement on these vectors is a floor, not a",
    "proof: two parsers can still diverge anywhere no vector reaches.",
    "",
    "'catches' lists the references that must be reported. [] means the vector",
    "must be reported clean. Each entry says why it exists, because a vector",
    "whose reason is forgotten is the first one somebody deletes."
  ],
  "vectors": [
    {
      "id": "rel-img",
      "why": "the base case: a sibling image a publish would drop",
      "html": "<img src=\"hero.png\">",
      "catches": [
        "hero.png"
      ]
    },
    {
      "id": "rel-stylesheet",
      "why": "a per-post stylesheet, same failure as an image",
      "html": "<link rel=\"stylesheet\" href=\"post.css\">",
      "catches": [
        "post.css"
      ]
    },
    {
      "id": "rel-css-url",
      "why": "the inline style block is real CSS and is scanned",
      "html": "<style>body{background:url(bg.png)}</style>",
      "catches": [
        "bg.png"
      ]
    },
    {
      "id": "rel-og-image",
      "why": "og:image rewritten relative; the meta branch",
      "html": "<meta property=\"og:image\" content=\"og.png\">",
      "catches": [
        "og.png"
      ]
    },
    {
      "id": "abs-og-image",
      "why": "the real og:image is absolute and is build-og's to deliver; it must never gate a publish",
      "html": "<meta property=\"og:image\" content=\"https://rnvizion.dev/assets/og/x.png\">",
      "catches": []
    },
    {
      "id": "meta-prose",
      "why": "a title is not a path; a check that fires on a headline gets turned off",
      "html": "<meta property=\"og:title\" content=\"Nine and counting\"><meta name=\"author\" content=\"Christian Smith\">",
      "catches": []
    },
    {
      "id": "root-relative",
      "why": "served from repo root by another writer, not a sibling",
      "html": "<img src=\"/assets/og/x.png\"><a href=\"/resume/\">r</a>",
      "catches": []
    },
    {
      "id": "absolute-and-anchor",
      "why": "off-site and in-page; neither is a file beside the post",
      "html": "<a href=\"https://x.test/y\">y</a><a href=\"#top\">t</a><a href=\"mailto:a@b.test\">m</a>",
      "catches": []
    },
    {
      "id": "protocol-relative",
      "why": "scheme-relative is still off-site",
      "html": "<script src=\"//cdn.test/a.js\"></script>",
      "catches": []
    },
    {
      "id": "data-uri-with-nested-url",
      "why": "a self-contained payload carries its own url(); scanning inside it invents references",
      "html": "<style>body{background:url(\"data:image/svg+xml,%3Csvg viewBox='0 0 2 2'%3E%3Crect filter='url(%23n)'/%3E%3C/svg%3E\")}</style>",
      "catches": []
    },
    {
      "id": "commented-out",
      "why": "an HTML comment is not fetched",
      "html": "<!-- <img src=\"ghost.png\"> -->",
      "catches": []
    },
    {
      "id": "srcset-sibling-first",
      "why": "list form, sibling in the first entry",
      "html": "<img srcset=\"diagram.png 1x, other.png 2x\">",
      "catches": [
        "diagram.png",
        "other.png"
      ]
    },
    {
      "id": "srcset-sibling-after-absolute",
      "why": "FAILS OPEN if the list is tested whole: one absolute entry hides every sibling behind it",
      "html": "<img srcset=\"https://rnvizion.dev/assets/og/a.png 1x, diagram.png 2x\">",
      "catches": [
        "diagram.png"
      ]
    },
    {
      "id": "srcset-sibling-after-rootrel",
      "why": "same root cause as above; the front entry need not be a scheme",
      "html": "<img srcset=\"/assets/a.png 1x, diagram.png 2x\">",
      "catches": [
        "diagram.png"
      ]
    },
    {
      "id": "srcset-all-absolute",
      "why": "control: a legitimate list must not fire",
      "html": "<img srcset=\"https://rnvizion.dev/a.png 1x, https://rnvizion.dev/b.png 2x\">",
      "catches": []
    },
    {
      "id": "imagesrcset",
      "why": "same list grammar on link rel=preload; named in the pattern, so it must actually be covered",
      "html": "<link rel=\"preload\" as=\"image\" imagesrcset=\"diagram.png 1x\">",
      "catches": [
        "diagram.png"
      ]
    },
    {
      "id": "shown-markup-block",
      "why": "FALSE FAIL: escaped example markup keeps its attributes verbatim, so use and mention look identical to a regex",
      "html": "<pre><code>&lt;img src=\"hero.png\" alt=\"x\"&gt;</code></pre>",
      "catches": []
    },
    {
      "id": "shown-markup-inline",
      "why": "same in prose; this blog explains checks for a living",
      "html": "<p>Add <code>&lt;link rel=\"stylesheet\" href=\"post.css\"&gt;</code> to the head.</p>",
      "catches": []
    },
    {
      "id": "shown-markup-does-not-hide-real",
      "why": "cutting shown markup must not cut the document around it",
      "html": "<p>Like <code>&lt;img src=\"a.png\"&gt;</code></p><img src=\"real.png\">",
      "catches": [
        "real.png"
      ]
    },
    {
      "id": "shown-markup-spans-do-not-merge",
      "why": "a greedy strip eats from the first <code> to the LAST </code>, swallowing real references in between; no other vector reaches that",
      "html": "<p><code>&lt;a&gt;</code></p><img src=\"real.png\"><p><code>&lt;b&gt;</code></p>",
      "catches": [
        "real.png"
      ]
    },
    {
      "id": "script-is-behaviour",
      "why": "every post carries the nav toggle; a script fetching a sibling is a real defect, not a sample",
      "html": "<script>new Image().src='tracker.png'</script>",
      "catches": [
        "tracker.png"
      ]
    }
  ]
}
'''
RULES_ANCHOR = "## The body\n"
RULES_SECTION = r'''## What a post consists of

**A post is `blog/<slug>/index.html` and nothing else.** One file, one folder, no siblings.

**Why it is a rule and not a habit.** The publishing agent builds one commit carrying that single
path. If a post ever gains a file beside it — an image, a per-post stylesheet, a script — the
publish pushes the HTML and drops the rest without saying so, and the post goes live referencing
files that are not there.

**The OG card is not an exception, and the reason matters.** Every post references one, at
`https://rnvizion.dev/assets/og/<slug>.png`. So a post already consists of two files. What makes one
path enough is not that a post is simple; it is that the second file has a second writer — `build-og`
commits it, on a different path, after the publish. So the condition to watch is narrower than "a
post gained a file":

> **a post gains a file that no other writer commits.**

**The reference rule.** Nothing in a post may reference a path that resolves inside the post's own
folder. Absolute URLs, root-relative paths, protocol-relative URLs, in-page anchors and `data:` URIs
are all fine — each resolves somewhere another writer is responsible for. A bare `hero.png` does not.

**Markup shown to a reader goes inside `<code>` or `<pre>`.** Escaping hides the angle brackets, not
the attributes: a paragraph explaining `&lt;img src="hero.png"&gt;` carries that exact string in the
page bytes without ever fetching anything. Use and mention are identical to a checker, so the
elements that mean *this is being shown* are what tell the two apart. Put shown markup anywhere else
and a correct post gets refused — and a guard that refuses correct work is the one that gets
switched off.

**Who asserts this.** `tests/test_post_shape.py` checks the whole tree in `build-feed`. The
publishing agent checks the reference rule alone, against the one document it is about to push.
Both run `tests/fixtures/post-shape-vectors.json`, which is this repo's file; if the two
implementations ever disagree on a vector, one of them is wrong and the disagreement is legible.
**Agreeing on the vectors is a floor, not a proof** — two parsers can still diverge anywhere no
vector reaches, which is how the vector for two code spans with a live reference between them came
to exist.

**Which check actually prevents anything.** Pages serves the publish commit directly, so by the time
`build-feed` runs, the post is already live: the site's own check is a backstop that reports, not a
gate that stops. The agent holds the irreversible step, so its copy is the one that can turn *post
live, feed stale, workflow red* into *nothing published*. Both are kept. The later one still fires
if the earlier one goes stale.

**If a post ever needs to be more than one file, that is a decision, not a fix.** Tell the
publishing agent in the same change so its staged set moves with it, then widen the test. Do not
loosen either check to make a red build go green.

'''
DONE_MARK = "LIST_REFS = re.compile("


def main():
    for path in (TEST, RULES):
        if not path.exists():
            sys.exit("%s not found -- wrong repo? This script is for "
                     "rnvizion.github.io." % path)

    test = TEST.read_text(encoding="utf-8")
    rules = RULES.read_text(encoding="utf-8")

    if DONE_MARK in test and VECTORS.exists() and RULES_SECTION in rules:
        print("already applied -- nothing to do.")
        return 0

    # Verify every anchor BEFORE writing anything. A half-applied change to a
    # guard is worse than an unapplied one: it still reports green.
    staged = test
    for n, (old, new) in enumerate(EDITS, 1):
        count = staged.count(old)
        assert count == 1, (
            "edit %d matches %d time(s) in test_post_shape.py, expected 1. "
            "The file has moved; re-cut this script against live." % (n, count))
        staged = staged.replace(old, new, 1)

    count = rules.count(RULES_ANCHOR)
    assert count == 1, (
        "'## The body' appears %d time(s) in post-template.RULES.md, "
        "expected 1." % count)
    assert RULES_SECTION not in rules, "the rule section is already present"

    VECTORS.parent.mkdir(parents=True, exist_ok=True)
    VECTORS.write_text(VECTOR_JSON, encoding="utf-8")
    TEST.write_text(staged, encoding="utf-8")
    RULES.write_text(rules.replace(RULES_ANCHOR, RULES_SECTION + RULES_ANCHOR, 1),
                     encoding="utf-8")

    print("wrote   %s (%d vectors)" % (
        VECTORS.relative_to(ROOT), len(json.loads(VECTOR_JSON)["vectors"])))
    print("patched %s (%d edits)" % (TEST.relative_to(ROOT), len(EDITS)))
    print("patched %s (rule section)" % RULES.relative_to(ROOT))
    print()

    for name in ("test_post_shape.py", "test_template_pairing.py"):
        r = subprocess.run([sys.executable, str(ROOT / "tests" / name)])
        if r.returncode != 0:
            print()
            print("%s fails on the tree as it stands. Read it before "
                  "committing." % name)
            return r.returncode

    print()
    print("Commit all three together; the rule, its vectors and the check that")
    print("asserts it are one change.")
    print("  git add tests/test_post_shape.py \\")
    print("          tests/fixtures/post-shape-vectors.json \\")
    print("          _templates/post-template.RULES.md")
    print('  git commit -m "fix(ci): srcset lists and shown markup in post shape guard"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
