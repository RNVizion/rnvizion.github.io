cd rnvizion.github.io
git log --before=2026-07-27 --format='%h %ad %s' --date=short -- resume/index.html | head
git show <sha>:resume/index.html > /tmp/resume-june.html
