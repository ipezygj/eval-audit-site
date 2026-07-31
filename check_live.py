#!/usr/bin/env python3
"""Fail if the published site is not serving what this repo says it should.

check_links.py reads the repo. This one reads the internet, because those are
different claims: a page can be perfect in git and absent in production — a
failed Pages build, a file never committed, a path that only resolves on a
case-insensitive filesystem. The status page already went eight days stale
while every local check passed.

Verifies every URL in sitemap.xml resolves, every social card the pages point
at exists, and that the live copy of each page carries the canonical URL and
og:image the repo intends.

    python check_live.py           # exit 1 on any live failure
    python check_live.py --quiet   # only print failures

Not run on push: Pages has not deployed that commit yet. It belongs on the
schedule, where it is asking "is production still right", not "did my push work".
"""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://ipezygj.github.io/eval-audit-site/"
TIMEOUT = 30
UA = {"User-Agent": "eval-audit-site-checker"}


def _fetch(url: str, head: bool = False):
    req = urllib.request.Request(url, headers=UA, method="HEAD" if head else "GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, (b"" if head else r.read())
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return type(e).__name__, b""


def _sitemap_urls():
    x = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", x)


def _expected_card(name: str) -> str:
    """Whatever the repo's own copy of the page points at — no second source of truth."""
    local = ROOT / (name or "index.html")
    if not local.exists():
        return ""
    m = re.search(r'property="og:image" content="[^"]*/([^"/]+)"', local.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def main() -> int:
    quiet = "--quiet" in sys.argv
    bad = []

    urls = _sitemap_urls()
    if not urls:
        print("sitemap.xml lists no URLs")
        return 1

    for url in urls:
        code, _ = _fetch(url, head=True)
        if code != 200:
            bad.append(f"{url} -> {code}")
        elif not quiet:
            print(f"  200  {url}")

    cards = sorted({m for p in ROOT.glob("*.html")
                    for m in re.findall(r'property="og:image" content="([^"]+)"',
                                        p.read_text(encoding="utf-8"))})
    for url in cards:
        code, _ = _fetch(url, head=True)
        if code != 200:
            bad.append(f"social card {url} -> {code}")
        elif not quiet:
            print(f"  200  {url}")

    for url in urls:
        name = url[len(SITE):] if url.startswith(SITE) else ""
        code, body = _fetch(url)
        if code != 200:
            continue
        html = body.decode("utf-8", "replace")
        if f'rel="canonical" href="{url}"' not in html:
            bad.append(f"{url}: live page does not declare itself canonical")
        want = _expected_card(name)
        if want and f"/{want}" not in html:
            bad.append(f"{url}: live og:image is not {want}")

    print(f"\n{len(urls)} pages, {len(cards)} cards checked against production")
    if bad:
        print(f"LIVE FAILURES ({len(bad)}):")
        for line in bad:
            print(f"  {line}")
        return 1
    print("production serves every page and card, with the metadata the repo intends")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
