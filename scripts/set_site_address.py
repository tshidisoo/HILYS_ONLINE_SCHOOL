"""Changes the website's address everywhere it is written: link previews, sitemap and search information.

Run it once when the site moves to its own domain, then deploy:

    python scripts/set_site_address.py https://hilys.com

The current address is read from public/robots.txt.
"""
import re
import sys
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
new = sys.argv[1].rstrip("/")
if not re.fullmatch(r"https://[a-z0-9.-]+", new):
    sys.exit("Give the full address starting with https://, for example https://hilys.com")
old = re.search(r"Sitemap: (https://\S+)/sitemap\.xml", (PUBLIC / "robots.txt").read_text()).group(1)

changed = 0
for path in [*PUBLIC.glob("*.html"), PUBLIC / "sitemap.xml", PUBLIC / "robots.txt"]:
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        changed += 1
print("Changed %s to %s in %d files" % (old, new, changed))
