#!/usr/bin/env python3
"""Fail if any page links to something this repo does not contain.

A dead link on a sales page costs a customer and says nothing while it does it.
The pages also reference their own assets by absolute URL — badges, llms.txt,
status.json — which no relative-path check would ever look at, so those are
rewritten back to repo paths and checked too.

External hosts are listed, never fetched: a link checker that needs the network
is a link checker nobody runs.

    python check_links.py          # exit 1 if anything is missing
    python check_links.py --list   # also print the external links
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
SITE = "https://ipezygj.github.io/eval-audit-site/"
SKIP_PREFIXES = ("#", "mailto:", "tel:", "data:", "javascript:")
REF = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')


def _targets(page: Path):
    for raw in REF.findall(page.read_text(encoding="utf-8", errors="replace")):
        url = raw.strip()
        if not url or url.startswith(SKIP_PREFIXES):
            continue
        if url.startswith(SITE):  # our own site, written absolutely
            yield raw, url[len(SITE):], True
        elif url.startswith(("http://", "https://", "//")):
            yield raw, url, None
        else:
            yield raw, url, True


def main() -> int:
    missing: dict[str, list[str]] = defaultdict(list)
    external: dict[str, list[str]] = defaultdict(list)
    pages = sorted(ROOT.glob("*.html"))

    for page in pages:
        for raw, target, is_local in _targets(page):
            if is_local is None:
                external[target].append(page.name)
                continue
            path = unquote(target.split("#")[0].split("?")[0])
            if not path:  # bare fragment on our own site
                continue
            if not (ROOT / path).exists():
                missing[raw].append(page.name)

    print(f"{len(pages)} pages, {len(external)} external links")

    if "--list" in sys.argv:
        for url in sorted(external):
            print(f"  ext  {url}  <- {', '.join(sorted(set(external[url])))}")

    if missing:
        print(f"\nBROKEN ({len(missing)}):")
        for url, srcs in sorted(missing.items()):
            print(f"  {url}  <- {', '.join(sorted(set(srcs)))}")
        return 1

    print("no broken internal links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
