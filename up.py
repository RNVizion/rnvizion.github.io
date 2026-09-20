#!/usr/bin/env python3
"""up.py -- extract the post-shape rule into a shared library the agent imports.

Built against rnvizion.github.io @ main dcf4413. Five files:

  scripts/post_shape.py                     NEW -- the two functions, as a library
  tests/test_post_shape.py                  rewritten; imports the library
  _templates/post-template.RULES.md         one hunk
  .gitignore                                one hunk
  .github/workflows/build-feed.yml          one hunk

WHY. The publishing agent was going to keep its own copy of the reference check,
kept honest by the shared vector file. Dropped on evidence: the semantics moved
twice in three days, and the second move is the kind a copy survives quietly --
it reports ghost.png, a file nobody ever wrote, while being wrong about the
post's real defect. A second checker is a second card renderer one layer down,
and that debt was retired for generate_card.py rather than re-taken here.

One implementation, two consumers. The agent resolves BLOG_REPO to a sibling
checkout, so the file is in hand when the check runs.

TWO THINGS THE EXTRACTION DRAGS IN, both landing in this same change:

  .gitignore gains __pycache__. A test that imports a library writes bytecode,
  in both folders, and again in whatever checkout the agent holds.

  build-feed.yml gains scripts/post_shape.py as a trigger path. Its test lives
  in tests/, so without that line a change to the rule would not run the check
  that pins it -- the generator-outside-its-own-trigger-path defect, third
  instance in this repo after generate_card.py and font.sh.

ON THE GUARD MECHANISM, AND THIS IS A JUDGMENT CALL WORTH ARGUING WITH.
The repo rule is exact-string edits with assert count == 1, because a complete
file overwrites a concurrent change silently. test_post_shape.py is rewritten
here, not edited: deriving anchors for it produced twenty, and twenty brittle
anchors on one file is a false-fail surface, which is the failure mode that
gets guards loosened. So that one file is replaced whole, guarded by a
sha256 of the content it expects to find. That refuses on ANY drift, where
twenty anchors refuse only on drift that happens to touch an anchor -- strictly
more refusing, not less. The other three files keep anchors, one each.

This is not a silent local exception: it should go back to the practices doc as
a third delivery mode, or be rejected there. Either way it is stated here.

Nothing is written until every guard passes. Re-running is a no-op.
"""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, check=True).stdout.strip())

PAYLOAD = json.loads(r'''{"anchored": {"_templates/post-template.RULES.md": ["**Who asserts this.** `tests/test_post_shape.py` checks the whole tree in `build-feed`. The\npublishing agent checks the reference rule alone, against the one document it is about to push.\nBoth run `tests/fixtures/post-shape-vectors.json`, which is this repo's file; if the two\nimplementations ever disagree on a vector, one of them is wrong and the disagreement is legible.\n**Agreeing on the vectors is a floor, not a proof** \u2014 two parsers can still diverge anywhere no\nvector reaches, which is how the vector for two code spans with a live reference between them came\nto exist.\n", "**Who asserts this, and there is only one implementation.** The two functions live in\n`scripts/post_shape.py`. `tests/test_post_shape.py` imports them and walks the whole tree in\n`build-feed`; the publishing agent imports the same file from its `BLOG_REPO` checkout and checks\nthe reference rule alone, against the one document it is about to push.\n\n**The agent was going to keep its own copy, kept honest by shared vectors. That was dropped on\nevidence.** The semantics moved twice in three days \u2014 `srcset` became a list, escaped markup stopped\nbeing a reference \u2014 and the second move is the kind a copy survives quietly: it reports `ghost.png`,\na file nobody ever wrote, while being wrong about the post's actual defect. **A second checker is a\nsecond card renderer one layer down**, and that debt was retired for `generate_card.py` rather than\nre-taken here. `tests/fixtures/post-shape-vectors.json` remains \u2014 as this library's contract test,\nnot as a treaty between two parsers.\n\n**The cost of importing, stated so nobody pays it by surprise.** Renaming either function, or\nchanging what it takes or returns, breaks the agent's publish. That is the trade taken deliberately:\na loud break beats a silent divergence. Send a note in the same change. And the module must import\nsilently and do nothing \u2014 check 0 of the test pins that in a subprocess, because an import-time side\neffect here is a dead publish over there, and it ran *before* the split: importing the guard walked\nthe tree and exited the caller, over a defect in a different post than the one being published.\n"], ".gitignore": ["assets/fonts/\n", "assets/fonts/\n\n# Bytecode. tests/test_post_shape.py imports scripts/post_shape.py, so running\n# the guard writes __pycache__ into both folders; the publishing agent importing\n# the same file does it again in whatever checkout it holds.\n__pycache__/\n*.py[cod]\n"], ".github/workflows/build-feed.yml": ["      - \"scripts/generate_card.py\"               # the shared card renderer\n", "      - \"scripts/generate_card.py\"               # the shared card renderer\n      - \"scripts/post_shape.py\"                   # the shared post-shape library;\n                                                  # its test lives in tests/, so without\n                                                  # this line a change to the rule would\n                                                  # not run the check that pins it\n"]}, "hashed": {"tests/test_post_shape.py": {"sha256_before": "11e40a4436c9ddcefcfdac11132d44f06606f670793320fd232a788ad6cf0292", "content": "#!/usr/bin/env python3\n\"\"\"A post is one tracked file, and it references nothing beside itself.\n\nThe publishing agent builds one commit carrying exactly blog/<slug>/index.html.\nThat is lossless only while a post IS that one path. If a post ever gains a\nsibling -- an image, a per-post stylesheet, a script -- the publish pushes the\nHTML and silently drops the rest, and the post goes live referencing files that\nare not there.\n\nThe agent asked to be told in the same change if what a post consists of ever\nchanges. An obligation on nobody in particular fires into an empty room, so it\nis attached to the event instead: build-feed.yml already triggers on blog/**,\nso this runs on the publish commit itself.\n\nAn OG card is not a counterexample. Every post references one, but by absolute\nURL under /assets/, committed by build-og on a different path. The post's second\nfile has a second writer. That is what makes one path enough -- not that a post\nis simple, but that nothing it needs is waiting on the publish to carry it.\n\nA FAILURE HERE IS NOT A BUG TO SILENCE. It means a post's shape changed, which\nis exactly the moment the agent chat needs a note; its staged set has to move in\nthe same change. Fix the post, or send the note and widen this test with it.\n\nTHE RULE ITSELF LIVES IN _templates/post-template.RULES.md, under \"What a post\nconsists of\". The two functions that implement it live in scripts/post_shape.py,\nwhich the publishing agent imports rather than reimplements -- so this file\ntests a library it shares rather than one it owns. Hence check 0: importing that\nmodule must do nothing, because an import-time side effect here is a dead\npublish over there.\n\nRun: python tests/test_post_shape.py\n\"\"\"\nimport pathlib\nimport re\nimport subprocess\nimport sys\n\nROOT = pathlib.Path(__file__).resolve().parent.parent\nsys.path.insert(0, str(ROOT / \"scripts\"))\n\n# 0. The import contract, and it runs BEFORE this file imports the library.\n#    The agent imports post_shape into a live publish, so anything that module\n#    does at import time runs inside that process. Probed in a subprocess\n#    because an import cannot be observed twice -- and probed first, because a\n#    side effect fatal enough to matter is fatal enough to kill this file's own\n#    import and take the report with it. Checking after the import can only\n#    catch the harmless cases.\n#\n#    Bought with a demonstration rather than an argument: before the split,\n#    importing the guard ran the whole tree walk and exited the caller -- over\n#    a defect in a different post than the one being published.\n_probe = subprocess.run(\n    [sys.executable, \"-c\",\n     \"import sys; sys.path.insert(0, %r); import post_shape; \"\n     \"print('NAMES', hasattr(post_shape, 'sibling_refs'), \"\n     \"hasattr(post_shape, 'shown_outside_code'))\" % str(ROOT / \"scripts\")],\n    capture_output=True, text=True, cwd=str(ROOT))\nif _probe.returncode != 0 or _probe.stdout.strip() != \"NAMES True True\":\n    print(\"POST SHAPE FAILED\")\n    print()\n    print(\"  scripts/post_shape.py broke its import contract.\")\n    print(\"  It must import silently, exit 0, and expose sibling_refs and\")\n    print(\"  shown_outside_code. The publishing agent imports it mid-publish;\")\n    print(\"  anything it does on import happens inside that process.\")\n    print()\n    print(\"    exit code: %d\" % _probe.returncode)\n    print(\"    stdout:    %r\" % _probe.stdout.strip()[:300])\n    if _probe.stderr.strip():\n        print(\"    stderr:    %s\" % _probe.stderr.strip().splitlines()[-1][:200])\n    sys.exit(1)\n\nfrom post_shape import shown_outside_code, sibling_refs  # noqa: E402\n\n\n\n\n\n\n\n\n\ndef tracked(pattern):\n    out = subprocess.run(\n        [\"git\", \"-C\", str(ROOT), \"ls-files\", pattern],\n        capture_output=True, text=True, check=True).stdout\n    return [p for p in out.splitlines() if p.strip()]\n\n\n\n\n\n\nVECTORS = ROOT / \"tests/fixtures/post-shape-vectors.json\"\nLIB = ROOT / \"scripts/post_shape.py\"\nvector_count = 0\n\nfailures = []\n\n# 1. The vectors. They are written by hand as an independent statement of\n#    what the rule means -- never derived from this file -- because a test that\n#    reads its expectations out of the thing it tests cannot detect a change to\n#    that thing -- and this file now tests a shared library, which is exactly\n#    when a contract test earns its place.\nif not VECTORS.exists():\n    failures.append(\"%s is missing; the vectors are this library's contract \"\n                    \"test and the agent imports the library\" % VECTORS.name)\nelse:\n    import json\n    loaded = json.loads(VECTORS.read_text(encoding=\"utf-8\"))[\"vectors\"]\n    vector_count = len(loaded)\n    for vector in loaded:\n        for label, fn, key in ((\"refs\", sibling_refs, \"catches\"),\n                               (\"shown\", shown_outside_code, \"shows\")):\n            want = sorted(vector.get(key, []))\n            got = sorted(fn(vector[\"html\"]))\n            if got != want:\n                failures.append(\n                    \"vector %s [%s]: expected %s, got %s -- %s\"\n                    % (vector[\"id\"], label, want, got, vector[\"why\"]))\n\nposts = tracked(\"blog/*/index.html\")\nif not posts:\n    failures.append(\"no posts found under blog/ -- has the layout moved?\")\n\n# 2. Nothing under blog/ is anything but an index.html.\nfor path in tracked(\"blog/*\"):\n    if not path.endswith(\"/index.html\"):\n        failures.append(\n            \"%s is tracked under blog/ and is not an index.html; a publish \"\n            \"commits one path and would not carry it\" % path)\n\n# 3. Each post folder holds exactly one tracked file.\nfor post in posts:\n    folder = post.rsplit(\"/\", 1)[0]\n    siblings = [p for p in tracked(folder + \"/*\") if p != post]\n    if siblings:\n        failures.append(\n            \"%s/ holds %d file(s) beside index.html: %s\"\n            % (folder, len(siblings), \", \".join(siblings)))\n\n# 4. No post references a path that resolves inside its own folder. This one\n#    fires before the sibling is committed, which is the case checks 2 and 3\n#    cannot see -- and it is the case that actually reaches a reader.\n# 5. Markup shown to a reader sits in <code> or <pre>. Checked in the same pass\n#    so the two are never confused: escaped markup in a bare <p> is a wrapper\n#    mistake, and reporting it as a missing file sends the author looking for\n#    something that was never meant to exist.\nfor post in posts:\n    html = (ROOT / post).read_text(encoding=\"utf-8\")\n    for ref in sibling_refs(html):\n        failures.append(\n            \"%s references %r, which resolves beside the post; a publish \"\n            \"carries the html only\" % (post, ref[:80]))\n    for shown in shown_outside_code(html):\n        failures.append(\n            \"%s shows %r outside <code>/<pre>; wrap it, per \\\"What a post \"\n            \"consists of\\\" in _templates/post-template.RULES.md\"\n            % (post, shown[:60]))\n\nif failures:\n    unique = sorted(set(failures))\n    print(\"POST SHAPE FAILED\")\n    print()\n    for f in unique[:20]:\n        print(\"  \" + f)\n    if len(unique) > 20:\n        print(\"  ... and %d more\" % (len(unique) - 20))\n    print()\n    print(\"A post is blog/<slug>/index.html and nothing else. If that is\")\n    print(\"changing on purpose, the publishing agent's staged set has to move\")\n    print(\"in the same change -- send the note, then widen this test.\")\n    sys.exit(1)\n\nprint(\"post shape OK: %d post(s); one tracked file each, no sibling refs, \"\n      \"no unwrapped markup; %d vector(s) green, import clean\"\n      % (len(posts), vector_count))\n"}}, "new": {"scripts/post_shape.py": "#!/usr/bin/env python3\n\"\"\"\npost_shape.py \u2014 the reference rule and the shown-markup rule, as functions.\n\nWHY THIS IS A LIBRARY AND NOT A TEST\n  Two consumers read a post for references: tests/test_post_shape.py, which\n  walks the whole tree in build-feed, and the MCP publishing agent, which\n  checks the one document it is about to push. The agent holds the\n  irreversible step; this repo's check runs after Pages has already served\n  the commit.\n\n  The alternative was for the agent to keep its own copy of these two\n  functions, kept honest by a shared vector file. That was rejected on\n  evidence rather than taste: the semantics moved twice in three days \u2014\n  srcset became a list, and escaped markup stopped being a reference \u2014 and\n  the second move is exactly the kind a copy survives quietly, reporting a\n  file nobody ever wrote while being wrong about the post's real defect.\n  A second checker is the same defect as a second card renderer, one layer\n  down; that debt was retired for generate_card.py and is not re-taken here.\n\n  So: one implementation, two consumers. The agent resolves BLOG_REPO to a\n  sibling checkout and cannot publish without it, so this file is in hand at\n  exactly the moment the check runs, and a change here reaches the agent when\n  the operator pulls.\n\nTHE INTERFACE IS PUBLIC. TREAT IT THAT WAY.\n  sibling_refs(html)        -> list of references resolving inside the post's\n                               own folder. A publish carries the HTML only, so\n                               every one of these is a file that will 404.\n  shown_outside_code(html)  -> list of escaped markup found outside <code> or\n                               <pre>. A wrapper mistake, not a missing file.\n\n  Both take an HTML string and return a list of strings. Neither touches the\n  filesystem, git, or the network, and importing this module does nothing at\n  all \u2014 tests/test_post_shape.py pins that, because an import-time side effect\n  here is a dead publish over there.\n\n  Renaming either function, or changing what it takes or returns, breaks the\n  agent's publish. That is the trade taken deliberately: a loud break beats a\n  silent divergence. Send a note in the same change.\n\nTHE RULES THEMSELVES live in _templates/post-template.RULES.md, under \"What a\npost consists of\". This file implements them; it does not define them.\n\nUSAGE (from the repo root)\n  python scripts/post_shape.py blog/squish/index.html [more.html ...]\n\nExit code 0 = nothing found, 1 = findings printed.\n\"\"\"\n\nimport re\nimport sys\n\n# Schemes and roots that resolve somewhere other than the post's own folder.\n# Whatever is left is a sibling, which is the whole point of this test.\nELSEWHERE = re.compile(r\"^(?:[a-z][a-z0-9+.-]*:|//|/|#)\", re.I)\n\n# Attributes the browser fetches, plus CSS url(). Deliberately NOT a blanket\n# content= sweep: most meta content is prose, and a check that fires on a page\n# title is one somebody turns off.\nREFS = re.compile(\n    r\"\"\"(?:\\bsrc|\\bhref|\\bposter|\\bdata-src)\\s*=\\s*[\"']([^\"']+)[\"']\"\"\"\n    r\"\"\"|\\burl\\(\\s*[\"']?([^\"')]+)[\"']?\\s*\\)\"\"\",\n    re.I,\n)\n\n# srcset is a comma-separated list with size descriptors, so the value as a\n# whole is never a path. Testing it whole fails OPEN: one absolute entry at the\n# front makes the rest of the list invisible.\nLIST_REFS = re.compile(\n    r\"\"\"(?:\\bsrcset|\\bimagesrcset)\\s*=\\s*[\"']([^\"']+)[\"']\"\"\", re.I)\n\n# Markup shown to a reader is escaped, so its attributes survive verbatim in the\n# bytes: a post explaining <img src=\"hero.png\"> carries that string without ever\n# fetching it. Use and mention look identical to a regex, so the elements that\n# mean \"this is being shown\" are cut before scanning.\nSHOWN = re.compile(r\"<(pre|code)\\b[^>]*>.*?</\\1\\s*>\", re.I | re.S)\n\n# Escaped markup, tag-shaped, anywhere it survives the cut above. It is never\n# a real reference, so it is neutralised before scanning; and outside <code>\n# or <pre> it is the house rule being broken, which is reported on its own.\n# [^<>] keeps a match from crossing a real tag, so cutting one can never\n# swallow the document between two of them -- the greedy-span failure again.\n# \"x &lt; y\" is prose, not markup, and is deliberately not matched.\nESCAPED_TAG = re.compile(r\"&lt;/?[a-zA-Z][^<>]*?&gt;\")\n\n# A self-contained payload carries its own url() and quotes; scanning inside it\n# reports references to things that are not files.\nDATA_URI = re.compile(\n    r\"\"\"url\\(\\s*([\"'])\\s*data:.*?\\1\\s*\\)|(?:\\bsrc|\\bhref)\\s*=\\s*([\"'])data:.*?\\2\"\"\",\n    re.I | re.S,\n)\n\nMETA = re.compile(r\"<meta\\b[^>]*>\", re.I)\n\nMETA_KEY = re.compile(r\"\"\"\\b(?:property|name)\\s*=\\s*[\"']([^\"']+)[\"']\"\"\", re.I)\n\nMETA_VAL = re.compile(r\"\"\"\\bcontent\\s*=\\s*[\"']([^\"']+)[\"']\"\"\", re.I)\n\nIMAGE_KEYS = {\"og:image\", \"og:image:url\", \"og:image:secure_url\", \"twitter:image\",\n              \"twitter:image:src\", \"og:audio\", \"og:video\"}\n\ndef shown_outside_code(html):\n    \"\"\"Markup shown to a reader that is not marked as shown.\n\n    Escaping hides the angle brackets, not the attributes, so this is what\n    makes the reference check possible at all. Reported separately because\n    the honest message is \"this belongs in <code>\", not \"this file is\n    missing\" -- a refusal that names a file nobody wrote is how a correct\n    guard gets read as a broken one.\n    \"\"\"\n    html = re.sub(r\"<!--.*?-->\", \" \", html, flags=re.S)\n    html = SHOWN.sub(\" \", html)\n    html = DATA_URI.sub(\" \", html)\n    return ESCAPED_TAG.findall(html)\n\ndef sibling_refs(html):\n    \"\"\"Every reference in the document that resolves inside the post's folder.\"\"\"\n    html = re.sub(r\"<!--.*?-->\", \" \", html, flags=re.S)\n    html = SHOWN.sub(\" \", html)\n    html = ESCAPED_TAG.sub(\" \", html)\n    html = DATA_URI.sub(\" \", html)\n    found = []\n    for match in REFS.finditer(html):\n        ref = (match.group(1) or match.group(2) or \"\").strip()\n        if ref and not ELSEWHERE.match(ref):\n            found.append(ref)\n    for match in LIST_REFS.finditer(html):\n        for candidate in match.group(1).split(\",\"):\n            ref = candidate.strip().split()[0] if candidate.strip() else \"\"\n            if ref and not ELSEWHERE.match(ref):\n                found.append(ref)\n    for tag in META.findall(html):\n        key = META_KEY.search(tag)\n        val = META_VAL.search(tag)\n        if key and val and key.group(1).lower() in IMAGE_KEYS:\n            ref = val.group(1).strip()\n            if ref and not ELSEWHERE.match(ref):\n                found.append(ref)\n    return found\n\n\ndef _report(path, refs, shown):\n    for ref in refs:\n        print(\"%s: references %r, which resolves beside the post\" % (path, ref[:80]))\n    for snip in shown:\n        print(\"%s: shows %r outside <code>/<pre>\" % (path, snip[:60]))\n\n\ndef main(argv):\n    if not argv:\n        print(__doc__.strip().splitlines()[-3].strip())\n        return 2\n    found = False\n    for path in argv:\n        try:\n            html = open(path, encoding=\"utf-8\").read()\n        except OSError as exc:\n            print(\"%s: %s\" % (path, exc))\n            found = True\n            continue\n        refs, shown = sibling_refs(html), shown_outside_code(html)\n        if refs or shown:\n            found = True\n            _report(path, refs, shown)\n    if not found:\n        print(\"clean: %d file(s)\" % len(argv))\n    return 1 if found else 0\n\n\nif __name__ == \"__main__\":\n    sys.exit(main(sys.argv[1:]))\n"}}''')
DONE_MARK = "scripts/post_shape.py"


def main():
    anchored = PAYLOAD["anchored"]
    hashed = PAYLOAD["hashed"]
    created = PAYLOAD["new"]

    for rel in list(anchored) + list(hashed):
        if not (ROOT / rel).exists():
            sys.exit("%s not found. This script is for rnvizion.github.io at "
                     "dcf4413." % rel)

    lib = ROOT / "scripts/post_shape.py"
    if lib.exists() and DONE_MARK in (ROOT / ".github/workflows/build-feed.yml").read_text(
            encoding="utf-8"):
        print("already applied -- nothing to do.")
        return 0

    # --- verify everything before writing anything -------------------------
    staged = {}

    for rel, (old, new) in anchored.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        count = text.count(old)
        assert count == 1, (
            "%s: the anchored passage appears %d time(s), expected 1. The file "
            "has moved; re-cut this script against live." % (rel, count))
        staged[rel] = text.replace(old, new, 1)

    for rel, spec in hashed.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        got = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert got == spec["sha256_before"], (
            "%s is not the file this was built against.\n"
            "  expected sha256 %s\n"
            "  found          %s\n"
            "Something changed it since dcf4413. Re-cut this script against "
            "live rather than overwriting work you cannot see." % (
                rel, spec["sha256_before"], got))
        staged[rel] = spec["content"]

    for rel in created:
        if (ROOT / rel).exists():
            sys.exit("%s already exists; this script creates it. Inspect it "
                     "before re-running." % rel)

    # --- write -------------------------------------------------------------
    for rel, content in created.items():
        (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / rel).write_text(content, encoding="utf-8")
        print("created %s (%d bytes)" % (rel, len(content)))
    for rel, content in sorted(staged.items()):
        (ROOT / rel).write_text(content, encoding="utf-8")
        print("patched %s" % rel)
    print()

    for name in ("test_post_shape.py", "test_template_pairing.py",
                 "test_card_contract.py"):
        r = subprocess.run([sys.executable, str(ROOT / "tests" / name)])
        if r.returncode != 0:
            print()
            print("%s fails on the tree as it stands. Read it before "
                  "committing." % name)
            return r.returncode

    print()
    print("Commit the five together. The library, the test that pins its")
    print("import contract, the rule it implements, and the trigger path that")
    print("runs the test are one change; splitting them ships a rule nothing")
    print("checks.")
    print("  git add scripts/post_shape.py tests/test_post_shape.py \\")
    print("          _templates/post-template.RULES.md .gitignore \\")
    print("          .github/workflows/build-feed.yml")
    print('  git commit -m "refactor: post_shape becomes a library the agent '
          'imports"')
    print()
    print("Then drop this runner:  git rm --cached up.py 2>/dev/null; rm -f up.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
