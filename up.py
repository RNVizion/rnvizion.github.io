#!/usr/bin/env python3
"""up.py -- make the shown-markup rule enforce itself, and report as itself.

Built against rnvizion.github.io @ main 82d0db2. Three files move:

  tests/test_post_shape.py                  eight guarded edits
  tests/fixtures/post-shape-vectors.json    replaced; 21 vectors -> 26
  _templates/post-template.RULES.md         one guarded hunk

The gap this closes. RULES.md now says markup shown to a reader belongs in
<code> or <pre>, and nothing enforced it. A post breaking that rule was still
refused -- but by the reference check, which reported the escaped attribute as
a missing sibling file. The author would go looking for a file nobody wrote.

  A refusal that names the wrong thing is worse than no refusal. It sends
  someone to fix the wrong artifact, and the guard gets read as broken
  rather than the post.

So: escaped markup is neutralised before the reference scan and reported on its
own, pointing back at the rule. "x &lt; y" is prose, not markup, and is
deliberately not matched -- the pattern is tag-shaped and cannot cross a real
tag, which also stops a cut from swallowing the document between two of them.

Five vectors arrive with it, including the one proving both faults report
independently when a post carries each.

Every anchor is verified before anything is written; if any is missing or
ambiguous the script refuses and leaves all three files untouched. Re-running
is a no-op.

NOTE: this file is itself tracked at the repo root from the previous round.
A one-shot runner should not live in the repo -- see the closing lines.
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

EDITS = json.loads(r'''[["SHOWN = re.compile(r\"<(pre|code)\\b[^>]*>.*?</\\1\\s*>\", re.I | re.S)\n\n", "SHOWN = re.compile(r\"<(pre|code)\\b[^>]*>.*?</\\1\\s*>\", re.I | re.S)\n\n# Escaped markup, tag-shaped, anywhere it survives the cut above. It is never\n# a real reference, so it is neutralised before scanning; and outside <code>\n# or <pre> it is the house rule being broken, which is reported on its own.\n# [^<>] keeps a match from crossing a real tag, so cutting one can never\n# swallow the document between two of them -- the greedy-span failure again.\n# \"x &lt; y\" is prose, not markup, and is deliberately not matched.\nESCAPED_TAG = re.compile(r\"&lt;/?[a-zA-Z][^<>]*?&gt;\")\n\n"], ["    return [p for p in out.splitlines() if p.strip()]\n\n\n", "    return [p for p in out.splitlines() if p.strip()]\n\n\ndef shown_outside_code(html):\n    \"\"\"Markup shown to a reader that is not marked as shown.\n\n    Escaping hides the angle brackets, not the attributes, so this is what\n    makes the reference check possible at all. Reported separately because\n    the honest message is \"this belongs in <code>\", not \"this file is\n    missing\" -- a refusal that names a file nobody wrote is how a correct\n    guard gets read as a broken one.\n    \"\"\"\n    html = re.sub(r\"<!--.*?-->\", \" \", html, flags=re.S)\n    html = SHOWN.sub(\" \", html)\n    html = DATA_URI.sub(\" \", html)\n    return ESCAPED_TAG.findall(html)\n\n\n"], ["    \"\"\"Every reference in the document that resolves inside the post's folder.\"\"\"\n    html = re.sub(r\"<!--.*?-->\", \" \", html, flags=re.S)\n    html = SHOWN.sub(\" \", html)\n", "    \"\"\"Every reference in the document that resolves inside the post's folder.\"\"\"\n    html = re.sub(r\"<!--.*?-->\", \" \", html, flags=re.S)\n    html = SHOWN.sub(\" \", html)\n    html = ESCAPED_TAG.sub(\" \", html)\n"], ["        want = sorted(vector[\"catches\"])\n        got = sorted(sibling_refs(vector[\"html\"]))\n        if got != want:\n            failures.append(\n                \"vector %s: expected %s, got %s -- %s\"\n                % (vector[\"id\"], want, got, vector[\"why\"]))\n", "        for label, fn, key in ((\"refs\", sibling_refs, \"catches\"),\n                               (\"shown\", shown_outside_code, \"shows\")):\n            want = sorted(vector.get(key, []))\n            got = sorted(fn(vector[\"html\"]))\n            if got != want:\n                failures.append(\n                    \"vector %s [%s]: expected %s, got %s -- %s\"\n                    % (vector[\"id\"], label, want, got, vector[\"why\"]))\n"], ["#    cannot see -- and it is the case that actually reaches a reader.\n", "#    cannot see -- and it is the case that actually reaches a reader.\n# 4. Markup shown to a reader sits in <code> or <pre>. Checked in the same pass\n#    so the two are never confused: escaped markup in a bare <p> is a wrapper\n#    mistake, and reporting it as a missing file sends the author looking for\n#    something that was never meant to exist.\n"], ["    for ref in sibling_refs((ROOT / post).read_text(encoding=\"utf-8\")):\n", "    html = (ROOT / post).read_text(encoding=\"utf-8\")\n    for ref in sibling_refs(html):\n"], ["            \"carries the html only\" % (post, ref[:80]))\n", "            \"carries the html only\" % (post, ref[:80]))\n    for shown in shown_outside_code(html):\n        failures.append(\n            \"%s shows %r outside <code>/<pre>; wrap it, per \\\"What a post \"\n            \"consists of\\\" in _templates/post-template.RULES.md\"\n            % (post, shown[:60]))\n"], ["print(\"post shape OK: %d post(s), one tracked file each, no sibling refs; \"\n      \"%d shared vector(s) green\" % (len(posts), vector_count))\n", "print(\"post shape OK: %d post(s); one tracked file each, no sibling refs, \"\n      \"no unwrapped markup; %d shared vector(s) green\"\n      % (len(posts), vector_count))\n"]]''')
VECTOR_JSON = r'''{
  "_": [
    "Shared reference vectors for the post shape rule. This file is the site",
    "repo's, and the publishing agent runs the same file against its own",
    "implementation. If the two disagree on a vector, one of them is wrong and",
    "the disagreement is visible. Agreement on these vectors is a floor, not a",
    "proof: two parsers can still diverge anywhere no vector reaches.",
    "",
    "'catches' lists the references that must be reported: paths resolving inside",
    "the post's own folder. 'shows' lists escaped markup found outside <code> or",
    "<pre>. Either may be omitted and defaults to []. Each entry says why it",
    "exists, because a vector whose reason is forgotten is the first one somebody",
    "deletes."
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
    },
    {
      "id": "shown-markup-bare-paragraph",
      "why": "the wrapper rule itself: escaped markup in prose is a wrapper mistake, and must report AS one rather than as a missing file",
      "html": "<p>Add &lt;link rel=\"stylesheet\" href=\"post.css\"&gt; to the head.</p>",
      "catches": [],
      "shows": [
        "&lt;link rel=\"stylesheet\" href=\"post.css\"&gt;"
      ]
    },
    {
      "id": "shown-markup-bare-element-name",
      "why": "a tag named in prose is still shown markup; the current post does this correctly inside <code>",
      "html": "<p>the &lt;article&gt; element</p>",
      "catches": [],
      "shows": [
        "&lt;article&gt;"
      ]
    },
    {
      "id": "escaped-less-than-is-prose",
      "why": "CONTROL: a comparison is not markup; flagging it would make the rule unusable in a post about thresholds",
      "html": "<p>fails when x &lt; y and again when a &gt; b</p>",
      "catches": [],
      "shows": []
    },
    {
      "id": "escaped-cut-does-not-span-real-tags",
      "why": "neutralising escaped markup must not swallow the document between two of them -- the greedy-span failure in a second costume",
      "html": "<p>x &lt; y</p><img src=\"real.png\"><p>a &gt; b</p>",
      "catches": [
        "real.png"
      ],
      "shows": []
    },
    {
      "id": "escaped-then-real-ref",
      "why": "a post can break the wrapper rule AND carry a real sibling; both must report, neither may mask the other",
      "html": "<p>&lt;img src=\"ghost.png\"&gt;</p><img src=\"real.png\">",
      "catches": [
        "real.png"
      ],
      "shows": [
        "&lt;img src=\"ghost.png\"&gt;"
      ]
    }
  ]
}
'''
RULES_OLD = r'''elements that mean *this is being shown* are what tell the two apart. Put shown markup anywhere else
and a correct post gets refused — and a guard that refuses correct work is the one that gets
switched off.
'''
RULES_NEW = r'''elements that mean *this is being shown* are what tell the two apart, and that is why this is a rule
rather than a style note — it is what makes the reference check possible at all.

**It is enforced, and it reports as itself.** Escaped markup outside `<code>` or `<pre>` fails with
*shows … outside `<code>`/`<pre>`*, pointing back at this section. It does **not** report as a
missing file, which is what it did for the four hours this rule existed unenforced: the check read
the escaped attribute as a real reference and refused the post by naming a file nobody had written.
**A refusal that names the wrong thing is worse than no refusal** — it sends the author looking for a
file that was never meant to exist, and the guard gets read as broken rather than the post.
A comparison in prose (`x &lt; y`) is not markup and is deliberately not matched.
'''
DONE_MARK = "ESCAPED_TAG = re.compile("
BASE_MARK = "LIST_REFS = re.compile("


def main():
    for path in (TEST, RULES, VECTORS):
        if not path.exists():
            sys.exit("%s not found. This script is for rnvizion.github.io at "
                     "or after cf84717." % path)

    test = TEST.read_text(encoding="utf-8")
    rules = RULES.read_text(encoding="utf-8")

    if DONE_MARK in test and RULES_NEW in rules:
        print("already applied -- nothing to do.")
        return 0

    if BASE_MARK not in test:
        sys.exit("test_post_shape.py does not carry the srcset fix, so this "
                 "script is cut against the wrong base. Apply the previous "
                 "round first, or ask for this one to be re-cut.")

    # Verify every anchor BEFORE writing anything. A half-applied change to a
    # guard is worse than an unapplied one: it still reports green.
    #
    # Each anchor is checked against the file as earlier edits have already
    # left it, rather than against the original. Deriving them the other way
    # collided on the fifth edit of the previous round: an inserted function
    # contained the lines a later anchor matched on.
    staged = test
    for n, (old, new) in enumerate(EDITS, 1):
        count = staged.count(old)
        assert count == 1, (
            "edit %d matches %d time(s) in test_post_shape.py, expected 1. "
            "The file has moved; re-cut this script against live." % (n, count))
        staged = staged.replace(old, new, 1)

    count = rules.count(RULES_OLD)
    assert count == 1, (
        "the paragraph this replaces appears %d time(s) in "
        "post-template.RULES.md, expected 1." % count)

    VECTORS.write_text(VECTOR_JSON, encoding="utf-8")
    TEST.write_text(staged, encoding="utf-8")
    RULES.write_text(rules.replace(RULES_OLD, RULES_NEW, 1), encoding="utf-8")

    print("wrote   %s (%d vectors)" % (
        VECTORS.relative_to(ROOT), len(json.loads(VECTOR_JSON)["vectors"])))
    print("patched %s (%d edits)" % (TEST.relative_to(ROOT), len(EDITS)))
    print("patched %s (stale caution retired)" % RULES.relative_to(ROOT))
    print()

    for name in ("test_post_shape.py", "test_template_pairing.py"):
        r = subprocess.run([sys.executable, str(ROOT / "tests" / name)])
        if r.returncode != 0:
            print()
            print("%s fails on the tree as it stands. Read it before "
                  "committing." % name)
            return r.returncode

    print()
    print("Commit the three together; the rule, its vectors and the check that")
    print("asserts it are one change.")
    print("  git add tests/test_post_shape.py \\")
    print("          tests/fixtures/post-shape-vectors.json \\")
    print("          _templates/post-template.RULES.md")
    print('  git commit -m "fix(ci): enforce the shown-markup rule, and report '
          'it as itself"')
    print()
    print("Then drop this runner. It is a one-shot delivery script sitting at")
    print("the repo root, it is spent once the commit above lands, and the")
    print("copy in git is the superseded version of it:")
    print("  git rm up.py && git commit -m \"chore: drop spent runner\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
