#!/usr/bin/env python3
"""Give resume/index.html the mobile nav every other page already has.

    python resume_mobile_nav.py            # check: writes nothing
    python resume_mobile_nav.py --apply    # write

Run from the rnvizion.github.io repo root.

WHY
  Measured across the site: index, bio, blog and demos each carry 1-5 @media
  blocks, the .nav-toggle button and the toggle script. resume/index.html
  carries none of the three. At 390px it overflows horizontally by 38px, the
  wordmark collides with "About", and "Resume" runs off the right edge -- and
  adding the Demos link made it worse by putting a fifth item in a row that was
  already too wide for the viewport.

  This is a port, not a design decision. The CSS, the markup and the script are
  the ones already live on index.html.

THE DROPDOWN OFFSET WAS MEASURED, NOT COPIED -- AND THE MEASUREMENT AGREED
  The shared @media block positions the panel with `top: 73px`, the nav height
  on the pages it was written for. This page's nav measures 56px, so a verbatim
  copy looked like it would leave a gap.

  It does not. The 40px button is what sets the height: with the toggle in
  place this nav renders at exactly 73px too, and a render after the change
  confirms the panel sits flush. The first measurement was accurate about the
  page as it stood and wrong about the page being built -- confirm the state
  from the finished artifact, not from the one in front of you.

  Worth recording separately: `73px` is a magic number duplicated across
  fifteen files now, with nothing deriving it from the nav's actual height. It
  is correct in all fifteen today and wrong the day nav padding changes on any
  one of them, with nothing reporting it.

WHAT IT DELIBERATELY DOES NOT DO
  It does not touch the other pages. They already have this and their value is
  right for them.
  It does not commit, stage, or push. Four edits, each asserting exactly one
  match, aborting the whole run if any is off -- a half-applied nav is worse
  than an unstyled one.
"""

import sys
from pathlib import Path

PAGE = Path("resume/index.html")

# Measured from a render of this page WITH the toggle button in place.
NAV_H = "73px"

EDITS = [
    # 1. the script needs an id to find the list
    (
        "nav-links gains an id",
        '      <div class="nav-links">\n',
        '      <div class="nav-links" id="nav-links">\n',
    ),
    # 2. the hamburger button, markup copied from index.html
    (
        "hamburger button added",
        '        <a href="/resume/" class="active">R\u00e9sum\u00e9</a>\n      </div>\n',
        '        <a href="/resume/" class="active">R\u00e9sum\u00e9</a>\n      </div>\n'
        '      <button class="nav-toggle" id="nav-toggle" aria-label="Toggle menu" aria-expanded="false">\n'
        '        <span></span><span></span><span></span>\n'
        '      </button>\n',
    ),
    # 3. the button's own CSS and the breakpoint
    (
        "nav-toggle CSS + @media block",
        "    .nav-links a.active { color: var(--accent); }\n",
        "    .nav-links a.active { color: var(--accent); }\n"
        "    .nav-toggle { display: none; background: transparent; border: 1px solid var(--border);"
        " border-radius: 6px; width: 40px; height: 40px; cursor: pointer; padding: 0;"
        " flex-direction: column; justify-content: center; align-items: center; gap: 5px;"
        " transition: border-color 0.2s ease; }\n"
        "    .nav-toggle:hover { border-color: var(--accent); }\n"
        "    .nav-toggle span { display: block; width: 18px; height: 1.5px;"
        " background: var(--text); transition: transform 0.25s ease, opacity 0.25s ease; }\n"
        "    @media (max-width: 640px) {\n"
        "      .nav-toggle { display: flex; }\n"
        "      /* 73px is this nav's measured height with the toggle in place,\n"
        "         which matches the other pages. Measured, not assumed: this\n"
        "         nav is 56px WITHOUT the button, and the button is what\n"
        "         closes the difference. */\n"
        "      .nav-links { position: fixed; top: " + NAV_H + "; left: 0; right: 0;"
        " background: rgba(10, 10, 15, 0.96); backdrop-filter: blur(20px);"
        " border-bottom: 1px solid var(--border-soft); flex-direction: column; gap: 0;"
        " padding: 16px 32px 24px; transform: translateY(-12px); opacity: 0;"
        " pointer-events: none; transition: transform 0.25s ease, opacity 0.25s ease; }\n"
        "      .nav-links.open { transform: translateY(0); opacity: 1; pointer-events: auto; }\n"
        "      .nav-links a { padding: 14px 0; font-size: 15px;"
        " border-bottom: 1px solid var(--border-soft); }\n"
        "      .nav-links a:last-child { border-bottom: none; }\n"
        "    }\n",
    ),
    # 4. the toggle behaviour, copied from index.html and closing on link tap
    (
        "toggle script added",
        "  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>",
        "  <script>\n"
        "    document.getElementById('year').textContent = new Date().getFullYear();\n"
        "    const navToggle = document.getElementById('nav-toggle');\n"
        "    const navLinks = document.getElementById('nav-links');\n"
        "    navToggle.addEventListener('click', () => {\n"
        "      const open = navLinks.classList.toggle('open');\n"
        "      navToggle.classList.toggle('open', open);\n"
        "      navToggle.setAttribute('aria-expanded', open);\n"
        "    });\n"
        "    navLinks.querySelectorAll('a').forEach(a => {\n"
        "      a.addEventListener('click', () => {\n"
        "        navLinks.classList.remove('open');\n"
        "        navToggle.classList.remove('open');\n"
        "        navToggle.setAttribute('aria-expanded', false);\n"
        "      });\n"
        "    });\n"
        "  </script>",
    ),
]

MARKER = 'id="nav-toggle"'

G, R, Y, C, D, N = ("\033[32m", "\033[31m", "\033[33m",
                    "\033[36m", "\033[2m", "\033[0m")


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"{D}resume_mobile_nav.py -- ports the hamburger nav onto "
          f"resume/index.html{N}")
    if not Path(".git").is_dir():
        print(f"{R}Run this from the rnvizion.github.io repo root.{N}")
        return 2
    if not PAGE.is_file():
        print(f"{R}{PAGE} not found. Nothing written.{N}")
        return 2

    src = PAGE.read_text(encoding="utf-8")
    print(f"{C}== {PAGE} =={N}")

    # Idempotent by a marker that exists only in the patched form.
    if MARKER in src:
        print(f"  {Y}skip{N}   this page already has the toggle. Nothing to do.")
        return 0

    # Count every anchor BEFORE writing anything. A nav that gets the button
    # but not the breakpoint is worse than a nav with neither.
    out = src
    for label, old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"  {R}stop{N}   {label}: anchor matched {n} time(s), expected 1")
            print(f"{D}           nothing written; the page is not shaped the way{N}")
            print(f"{D}           this script believes and a partial nav is worse{N}")
            print(f"{D}           than no nav.{N}")
            return 1
        out = out.replace(old, new, 1)
        print(f"  {G}ok{N}     {label}")

    if not apply:
        print(f"\n{Y}Check only. Nothing written.{N}")
        print("  Re-run with --apply to write.")
        return 0

    PAGE.write_text(out, encoding="utf-8")
    print(f"\n{G}wrote{N}  {PAGE}")
    print(f"\n{G}Nothing staged, nothing committed.{N}")
    print("  git diff --stat")
    print(f"{D}  Check it at phone width before committing: the menu should open{D}")
    print(f"{D}  flush under the bar with no gap.{N}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
