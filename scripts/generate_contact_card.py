#!/usr/bin/env python3
"""
generate_contact_card.py — builds the RNVizion handoff surface from profile.json.

NAME: deliberately not generate_card.py. That name is taken in this repo by the
blog-index post-card builder, and generate_project_card.py takes the other
obvious one. Three unrelated things in this codebase are called a card.

Outputs (all generated, none hand-edited):
    card/index.html            the public handoff page
    card/rnvizion.vcf          the vCard the save button downloads
    card/card-qr.png           QR encoding https://rnvizion.dev/card/
    card/print/index.html      print sheet, 3.5x2in + bleed, front and back

Standing rule this implements: a handoff surface is generated from the manifest,
because the facts it carries are exactly the facts that change.

Built against profile.json v1.2.7 (fetched 2026-08-10). If the manifest has moved
past that, re-read it before trusting the key paths in the ADAPTER block below.

Usage:
    python3 scripts/generate_contact_card.py --profile ../rnv-brand/profile.json --out .

CROSS-REPO DEPENDENCY: profile.json lives in rnv-brand, not here. Running this
in CI needs that repo checked out to a second path or fetched raw; build-og.yml
checks out this repo only. That is why this stays hand-run for now.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# ADAPTER — every profile.json key path this script depends on lives here.
#
# Two of the facts this surface needs are NOT in the manifest yet, and how they
# get encoded is the Brand Infrastructure project's dispatch call, not this
# script's. Until they land, they come from CARD_OVERRIDES below and the script
# says so loudly on every run. When they land, delete the override and point the
# path at the real key. Nothing else in this file changes.
# ---------------------------------------------------------------------------

PATHS = {
    "name":     ("identity", "name"),
    "brand":    ("identity", "brand"),
    "long":     ("identity", "brand_long"),
    "site":     ("identity", "site"),
    "linkedin": ("identity", "linkedin"),
    "github":   ("identity", "github"),
    # Public inbound address. Lives under identity.role_emails as a key.
    "email":    ("identity", "role_emails", "inquiries@rnvizion.dev"),
}

# NEVER read identity.phone. That is the personal cell (301). The card carries
# the brand routing number and nothing else. This is enforced, not advised.
FORBIDDEN_PATHS = [("identity", "phone")]

CARD_OVERRIDES = {
    # PENDING MANIFEST: brand routing number (Google Voice, created 2026-08-10).
    # Distinct fact from identity.phone. Suggested shape only; dispatch is theirs.
    "brand_phone_display": "(202) 987-9948",
    "brand_phone_e164": "+12029879948",
    # PENDING MANIFEST: the card line. Registry row Banked until the card ships.
    "line": "Vizion, built not borrowed.",
    # PENDING MANIFEST: the discipline kicker.
    "kicker": "AI · SOFTWARE · WEB · BRAND",
}

CARD_URL = "https://rnvizion.dev/card/"

# The manifest lives in another repo, so a relative path only resolves when both
# repos are checked out side by side. That is true on a laptop and false in a
# Codespace, which checks out one repo into /workspaces/<repo>. The local file
# still wins when it exists; this is the fallback, and it announces itself every
# time, because silently building from main while you are editing a local copy
# would be a false all-clear.
PROFILE_URL = ("https://raw.githubusercontent.com/RNVizion/rnv-brand/"
               "main/profile.json")

# Brand tokens. Mirrored from engine/brand.py; re-check on any color change.
GOLD = "#d2bc93"
BG_0 = "#0a0a0f"
BG_1 = "#11111a"
RULE_ALPHA = 0.18


# ---------------------------------------------------------------------------
# Manifest reading
# ---------------------------------------------------------------------------

def dig(data: dict, path: tuple):
    """Walk a key path. Returns None on any miss rather than raising."""
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def read_manifest(path: Path, url: str, offline: bool) -> tuple[dict, str]:
    """Local file wins; network is the fallback. Returns (data, source)."""
    if path.is_file():
        raw, source = path.read_text(encoding="utf-8"), str(path)
    elif offline:
        sys.exit(f"REFUSED: no manifest at {path}, and --offline forbids fetching. "
                 "The card is generated from profile.json or not at all.")
    else:
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            sys.exit(f"REFUSED: no manifest at {path}, and fetching {url} failed "
                     f"({exc}). The card is generated from profile.json or not "
                     "at all.")
        source = url

    try:
        return json.loads(raw), source
    except json.JSONDecodeError as exc:
        sys.exit(f"REFUSED: manifest at {source} is not valid JSON ({exc}). "
                 "Check for curly quotes; they have done this before.")


def require_qrcode() -> None:
    """Preflight. A missing QR library must fail before anything is written.

    Both imports, not just qrcode: `pip install qrcode` does NOT pull Pillow in
    (it is the [pil] extra), and qrcode imports PIL lazily inside make_image.
    Checking only qrcode would pass here and then die after three files were
    already on disk, which is the exact failure this preflight exists to stop.
    """
    missing = []
    for module, package in (("qrcode", "qrcode"), ("PIL", "Pillow")):
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        sys.exit(f"REFUSED: not installed -> {', '.join(missing)}\n"
                 f"  pip install --user {' '.join(missing)}\n"
                 "Checked up front on purpose: failing partway would leave a card "
                 "page committed alongside a QR image that does not exist.")


def load_facts(profile_path: Path, profile_url: str = PROFILE_URL,
               offline: bool = False) -> tuple[dict, list[str], str]:
    """Read the manifest. Refuses rather than guesses when a fact is missing."""
    data, source = read_manifest(profile_path, profile_url, offline)

    facts, missing = {}, []
    for name, path in PATHS.items():
        value = dig(data, path)
        if value is None or not str(value).strip():
            missing.append(f"{name} -> {'.'.join(path)}")
        else:
            facts[name] = str(value).strip()

    if missing:
        sys.exit("REFUSED: manifest is missing facts this surface needs:\n  "
                 + "\n  ".join(missing)
                 + "\n\nResolve or refuse, never guess. Fix the manifest or the "
                   "ADAPTER paths; do not hardcode the value here.")

    # The inquiries@ value in role_emails is a description, not the address.
    # The address is the key itself.
    facts["email"] = PATHS["email"][-1]

    for path in FORBIDDEN_PATHS:
        if dig(data, path) is not None:
            facts.setdefault("_forbidden_present", True)

    facts["_manifest_version"] = str(data.get("version", "unknown"))
    facts["_manifest_updated"] = str(data.get("updated", "unknown"))
    facts.update(CARD_OVERRIDES)
    return facts, sorted(CARD_OVERRIDES), source


# ---------------------------------------------------------------------------
# vCard 3.0
# ---------------------------------------------------------------------------

def vcard_escape(value: str) -> str:
    """Escape per RFC 2426. The comma in the card line makes this load-bearing."""
    return (value.replace("\\", "\\\\")
                 .replace(";", "\\;")
                 .replace(",", "\\,")
                 .replace("\n", "\\n"))


def fold(line: str, limit: int = 73) -> str:
    """Fold long lines; continuations begin with a single space."""
    if len(line.encode("utf-8")) <= limit:
        return line
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > limit:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n".join(out)


def build_vcard(f: dict) -> str:
    """vCard 3.0 — the widest-compatibility target across iOS and Android."""
    given, _, family = f["name"].partition(" ")
    rows = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{vcard_escape(family)};{vcard_escape(given)};;;",
        f"FN:{vcard_escape(f['name'])}",
        f"ORG:{vcard_escape(f['brand'])}",
        f"EMAIL;TYPE=INTERNET,WORK:{f['email']}",
        f"TEL;TYPE=WORK,VOICE:{f['brand_phone_e164']}",
        f"URL;TYPE=WORK:https://{f['site']}",
        f"URL;TYPE=WORK:https://{f['linkedin']}",
        f"URL;TYPE=WORK:https://{f['github']}",
        # ASCII separator here on purpose: the middle dot is safe on the web
        # surfaces but mangles in older vCard parsers, which assume no charset.
        f"NOTE:{vcard_escape(f['line'] + ' ' + f['kicker'].replace(' · ', ' / '))}",
        "END:VCARD",
    ]
    # CRLF is required by the spec; some Android parsers reject bare LF.
    return "\r\n".join(fold(r) for r in rows) + "\r\n"


# ---------------------------------------------------------------------------
# QR
# ---------------------------------------------------------------------------

def build_qr(out_path: Path, *, dark: str, light: str, box: int = 10) -> None:
    try:
        import qrcode
    except ImportError:
        sys.exit("REFUSED: qrcode not installed. pip install qrcode")
    q = qrcode.QRCode(
        # M tolerates ~15% damage; a card lives in a wallet, so this is the floor.
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box,
        border=2,
    )
    q.add_data(CARD_URL)
    q.make(fit=True)
    q.make_image(fill_color=dark, back_color=light).save(out_path)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

# Montserrat Black (900) carries the mark, per the Brand Book lockup template:
# mark letterforms in Montserrat Black above a hairline rule, spelled-out name
# beneath in tracked JetBrains Mono. Same hand as the AIII mark.
FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@900&"
         "family=JetBrains+Mono:wght@400;500&"
         "family=Instrument+Serif:ital@1&display=swap")


def build_page(f: dict) -> str:
    rows = [
        ("Email", f["email"], f"mailto:{f['email']}"),
        ("Phone", f["brand_phone_display"], f"tel:{f['brand_phone_e164']}"),
        ("Site", f["site"], f"https://{f['site']}"),
        ("LinkedIn", f["linkedin"], f"https://{f['linkedin']}"),
        ("GitHub", f["github"], f"https://{f['github']}"),
    ]
    contact = "\n".join(
        f'      <a class="row" href="{href}">'
        f'<span class="k">{label}</span>'
        f'<span class="v">{value}</span></a>'
        for label, value, href in rows
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{f['name']} — {f['brand']}</title>
<meta name="description" content="{f['line']} {f['kicker']}">
<meta name="robots" content="noindex,follow">
<meta property="og:title" content="{f['name']} — {f['brand']}">
<meta property="og:description" content="{f['line']}">
<meta property="og:url" content="{CARD_URL}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>
  :root {{ --gold:{GOLD}; --bg0:{BG_0}; --bg1:{BG_1};
           --rule:rgba(210,188,147,{RULE_ALPHA}); }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; min-height:100vh; display:grid; place-items:center;
          background:var(--bg0); color:var(--gold);
          font-family:"JetBrains Mono",ui-monospace,monospace;
          padding:2rem 1.25rem; }}
  main {{ width:min(26rem,100%); }}
  .mark {{ font-family:"Montserrat",system-ui,sans-serif; font-weight:900;
           font-size:2.15rem; letter-spacing:.06em; margin:0; }}
  hr {{ border:0; border-top:1px solid var(--rule); margin:.85rem 0; }}
  .long {{ font-size:.62rem; letter-spacing:.34em; text-transform:uppercase;
           opacity:.72; margin:0 0 2.4rem; }}
  .name {{ font-size:1.05rem; font-weight:500; margin:0 0 .5rem; }}
  .kicker {{ font-size:.6rem; letter-spacing:.24em; opacity:.72; margin:0 0 1.1rem; }}
  .line {{ font-family:"Instrument Serif",Georgia,serif; font-style:italic;
           font-size:1.5rem; line-height:1.25; margin:0 0 2.2rem; }}
  .row {{ display:flex; justify-content:space-between; gap:1rem;
          padding:.72rem 0; border-bottom:1px solid var(--rule);
          color:inherit; text-decoration:none; font-size:.78rem; }}
  .row:first-of-type {{ border-top:1px solid var(--rule); }}
  .row:hover,.row:focus-visible {{ background:var(--bg1); }}
  .k {{ opacity:.6; letter-spacing:.1em; text-transform:uppercase;
        font-size:.6rem; align-self:center; }}
  .v {{ text-align:right; word-break:break-all; }}
  .save {{ display:block; width:100%; margin:2rem 0 0; padding:.9rem;
           background:transparent; border:1px solid var(--gold);
           color:var(--gold); font:inherit; font-size:.72rem;
           letter-spacing:.2em; text-transform:uppercase; text-align:center;
           text-decoration:none; cursor:pointer; }}
  .save:hover,.save:focus-visible {{ background:var(--gold); color:var(--bg0); }}
  figure {{ margin:2.4rem 0 0; text-align:center; }}
  figure img {{ width:8.5rem; height:auto; image-rendering:pixelated; }}
  figcaption {{ font-size:.55rem; letter-spacing:.2em; opacity:.5;
                text-transform:uppercase; margin-top:.7rem; }}
  @media (prefers-reduced-motion:no-preference) {{
    .row,.save {{ transition:background .15s ease,color .15s ease; }} }}
</style>
</head>
<body>
<main>
  <h1 class="mark">{f['brand']}</h1>
  <hr>
  <p class="long">{f['long']}</p>

  <p class="name">{f['name']}</p>
  <p class="kicker">{f['kicker']}</p>
  <p class="line">{f['line']}</p>

  <nav>
{contact}
  </nav>

  <a class="save" href="rnvizion.vcf" download>Save contact</a>

  <figure>
    <img src="card-qr.png" alt="QR code linking to {CARD_URL}" width="240" height="240">
    <figcaption>{f['site']}/card</figcaption>
  </figure>
</main>
</body>
</html>
"""


def build_print(f: dict) -> str:
    """3.5x2in US standard, 0.125in bleed per edge, front and back."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{f['brand']} — print card, 3.5x2in + bleed</title>
<link rel="stylesheet" href="{FONTS}">
<style>
  @page {{ size:3.75in 2.25in; margin:0; }}
  :root {{ --gold:{GOLD}; --bg0:{BG_0}; --rule:rgba(210,188,147,{RULE_ALPHA}); }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#555;
          font-family:"JetBrains Mono",ui-monospace,monospace;
          -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  .card {{ width:3.75in; height:2.25in; background:var(--bg0); color:var(--gold);
           padding:.3125in; display:flex; flex-direction:column;
           page-break-after:always; position:relative; overflow:hidden; }}
  /* Trim guide. Screen only; never prints. */
  .card::after {{ content:""; position:absolute; inset:.125in;
                  outline:1px dashed rgba(255,255,255,.28); pointer-events:none; }}
  @media print {{ .card::after {{ display:none; }} body {{ background:#fff; }} }}

  .front {{ align-items:center; justify-content:center; text-align:center; }}
  .front .mark {{ font-family:"Montserrat",system-ui,sans-serif; font-weight:900;
                  font-size:25pt; letter-spacing:.06em; margin:0; }}
  .front hr {{ border:0; border-top:.5pt solid var(--rule);
               width:1.5in; margin:7pt auto; }}
  .front .long {{ font-size:5.2pt; letter-spacing:.34em;
                  text-transform:uppercase; opacity:.8; margin:0; }}

  .back {{ justify-content:space-between; }}
  .back .name {{ font-size:9.5pt; font-weight:500; margin:0 0 3pt; }}
  .back .kicker {{ font-size:5pt; letter-spacing:.2em; opacity:.8; margin:0; }}
  .back .line {{ font-family:"Instrument Serif",Georgia,serif; font-style:italic;
                 font-size:12.5pt; line-height:1.2; margin:9pt 0 0; }}
  .foot {{ display:flex; justify-content:space-between; align-items:flex-end;
           gap:10pt; }}
  .foot ul {{ list-style:none; margin:0; padding:0; font-size:6.2pt;
              line-height:1.65; }}
  .foot img {{ width:.62in; height:.62in; image-rendering:pixelated; }}
</style>
</head>
<body>

<section class="card front">
  <div>
    <p class="mark">{f['brand']}</p>
    <hr>
    <p class="long">{f['long']}</p>
  </div>
</section>

<section class="card back">
  <div>
    <p class="name">{f['name']}</p>
    <p class="kicker">{f['kicker']}</p>
    <p class="line">{f['line']}</p>
  </div>
  <div class="foot">
    <ul>
      <li>{f['email']}</li>
      <li>{f['brand_phone_display']}</li>
      <li>{f['site']}</li>
      <li>{f['linkedin']}</li>
    </ul>
    <img src="../card-qr-print.png" alt="">
  </div>
</section>

</body>
</html>
"""


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate the RNVizion contact-card surface from profile.json.")
    ap.add_argument("--profile", default="../rnv-brand/profile.json",
                    help="path to profile.json")
    ap.add_argument("--profile-url", default=PROFILE_URL,
                    help="raw URL used when --profile is not on disk")
    ap.add_argument("--offline", action="store_true",
                    help="refuse rather than fetch; use when the local copy must win")
    ap.add_argument("--out", default=".", help="site root; writes into <out>/card/")
    args = ap.parse_args()

    require_qrcode()
    facts, overrides, source = load_facts(Path(args.profile), args.profile_url,
                                          args.offline)

    card = Path(args.out) / "card"
    (card / "print").mkdir(parents=True, exist_ok=True)

    (card / "index.html").write_text(build_page(facts), encoding="utf-8")
    (card / "rnvizion.vcf").write_text(build_vcard(facts), encoding="utf-8",
                                       newline="")
    (card / "print" / "index.html").write_text(build_print(facts), encoding="utf-8")

    build_qr(card / "card-qr.png", dark=GOLD, light=BG_0, box=10)
    # Print QR is black on white: dark-on-dark scans badly under shop lighting,
    # and cheap scanners fail it outright. The screen version keeps brand color.
    build_qr(card / "card-qr-print.png", dark="#000000", light="#ffffff", box=12)

    print(f"manifest: {source}")
    if source.startswith("http"):
        print("  ^ fetched from main; no local copy at the --profile path.")
    print(f"version:  {facts['_manifest_version']} ({facts['_manifest_updated']})")
    print(f"built -> {card}/")
    for name in ("index.html", "rnvizion.vcf", "card-qr.png",
                 "card-qr-print.png", "print/index.html"):
        print(f"  {name}")

    if overrides:
        print("\nNOT YET IN THE MANIFEST — these came from CARD_OVERRIDES:")
        for key in overrides:
            print(f"  {key} = {CARD_OVERRIDES[key]!r}")
        print("  Encoding is the Brand Infrastructure project's call. Until it\n"
              "  lands, this surface is outside drift detection.")


if __name__ == "__main__":
    main()
