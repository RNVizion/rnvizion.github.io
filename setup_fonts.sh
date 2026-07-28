#!/usr/bin/env bash
#
# setup_fonts.sh — one-shot cleanup after restoring font.sh.
#
# Does all of it in one go:
#   1. verifies font.sh is present at the repo root (CI calls `bash font.sh`
#      with no path, so anywhere else silently breaks build-og.yml)
#   2. marks font.sh executable in git's index
#   3. stops tracking assets/fonts/ and deletes it from the working tree
#   4. adds assets/fonts/ to .gitignore so an accidental ./font.sh run can
#      never stage the TTFs again
#   5. commits, scoped to only these paths
#   6. pushes, which fires build-og.yml (font.sh is one of its trigger paths)
#
#   ./setup_fonts.sh              # show the plan, confirm, then do it
#   ./setup_fonts.sh --yes        # skip the confirmation
#   ./setup_fonts.sh --no-push    # commit locally, don't push
#   ./setup_fonts.sh --dry-run    # show the plan and stop
#
set -euo pipefail

ASSUME_YES=0; DO_PUSH=1; DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y)  ASSUME_YES=1 ;;
    --no-push) DO_PUSH=0 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

say()  { printf '%s\n' "$*"; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# --- must be inside a git repo, and we operate from its root ----------------
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not inside a git repository."
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
say "repo: $ROOT"

# --- font.sh must exist, at the root ---------------------------------------
if [ ! -f "font.sh" ]; then
  if find . -name font.sh -not -path './.git/*' | grep -q .; then
    found="$(find . -name font.sh -not -path './.git/*' | head -1)"
    fail "font.sh is at $found but CI runs 'bash font.sh' from the repo root.
       Move it:  git mv \"$found\" font.sh"
  fi
  fail "font.sh not found at the repo root. Save it there first, then re-run."
fi

# --- work out what actually needs doing ------------------------------------
FONTS_TRACKED=0
git ls-files --error-unmatch assets/fonts >/dev/null 2>&1 && FONTS_TRACKED=1
TRACKED_COUNT=$(git ls-files assets/fonts | wc -l | tr -d ' ')

GITIGNORE_NEEDED=1
if [ -f .gitignore ] && grep -qxF 'assets/fonts/' .gitignore; then
  GITIGNORE_NEEDED=0
fi

FONTSH_TRACKED=0
git ls-files --error-unmatch font.sh >/dev/null 2>&1 && FONTSH_TRACKED=1

# warn about unrelated work; we stage by path, so it won't be swept in
DIRTY="$(git status --porcelain | grep -vE '^.. (font\.sh|\.gitignore|assets/fonts/)' || true)"

# --- plan -------------------------------------------------------------------
say ""
say "plan"
say "----"
[ "$FONTSH_TRACKED" -eq 1 ] && say "  · font.sh          already tracked; ensuring +x" \
                            || say "  · font.sh          add to git, mode +x"
[ "$FONTS_TRACKED" -eq 1 ]  && say "  · assets/fonts/    untrack + delete ($TRACKED_COUNT file(s))" \
                            || say "  · assets/fonts/    not tracked; nothing to remove"
[ "$GITIGNORE_NEEDED" -eq 1 ] && say "  · .gitignore       add 'assets/fonts/'" \
                              || say "  · .gitignore       already ignores assets/fonts/"
say "  · commit           scoped to the paths above"
[ "$DO_PUSH" -eq 1 ] && say "  · push             triggers build-og.yml" \
                     || say "  · push             skipped (--no-push)"

if [ -n "$DIRTY" ]; then
  say ""
  say "note: other uncommitted changes are present and will NOT be included:"
  printf '%s\n' "$DIRTY" | sed 's/^/       /'
fi

if [ "$DRY_RUN" -eq 1 ]; then
  say ""
  say "dry run — nothing changed."
  exit 0
fi

if [ "$ASSUME_YES" -eq 0 ]; then
  say ""
  printf 'proceed? [y/N] '
  read -r reply
  case "$reply" in [yY]*) ;; *) say "aborted."; exit 0 ;; esac
fi

# --- do it ------------------------------------------------------------------
say ""

chmod +x font.sh 2>/dev/null || true
git add --chmod=+x font.sh
say "  font.sh staged (+x)"

if [ "$FONTS_TRACKED" -eq 1 ]; then
  git rm -r --quiet assets/fonts
  say "  assets/fonts/ untracked and removed"
else
  rm -rf assets/fonts 2>/dev/null || true
  say "  assets/fonts/ not tracked; local copy cleared"
fi

if [ "$GITIGNORE_NEEDED" -eq 1 ]; then
  [ -f .gitignore ] && [ -n "$(tail -c1 .gitignore)" ] && printf '\n' >> .gitignore
  printf '# fetched by font.sh; never commit\nassets/fonts/\n' >> .gitignore
  git add .gitignore
  say "  .gitignore updated"
fi

if git diff --cached --quiet; then
  say ""
  say "nothing staged — everything was already in the desired state."
  exit 0
fi

say ""
say "staged:"
git diff --cached --name-status | sed 's/^/  /'

git commit --quiet -m "restore font.sh, stop tracking fetched fonts

font.sh is a build-og.yml dependency and must live at the repo root.
assets/fonts/ is fetched at CI time, so it no longer belongs in git."
say ""
say "committed: $(git rev-parse --short HEAD)"

# --- push -------------------------------------------------------------------
if [ "$DO_PUSH" -eq 1 ]; then
  if ! git remote get-url origin >/dev/null 2>&1; then
    say "no 'origin' remote; skipping push."
    exit 0
  fi
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  say "pushing $BRANCH…"
  if git push origin "$BRANCH"; then
    say ""
    say "done. font.sh is a build-og.yml trigger path, so this push starts a run."
    say "watch it:  gh run watch    (or the Actions tab)"
    say "green means OG images regenerated and committed back to assets/og/."
  else
    say ""
    say "push failed. The commit is safe locally; resolve and push again."
    exit 1
  fi
else
  say "not pushed. When ready:  git push"
fi
