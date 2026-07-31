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


def _mojibake(pages):
    """Find UTF-8 that was decoded as latin-1 somewhere upstream.

    The tell is a stray Â/Ã/â immediately followed by another high character —
    an em dash arriving as â€". Real accented prose does not produce that pair,
    so this does not fire on Väätäinen. Found live on three Glama listings,
    where the corrupted description is the first thing a visitor reads.
    """
    SUSPECT = {0x00E2, 0x00C3, 0x00C2, 0x20AC, 0x2122}
    out = []
    for page in pages:
        t = page.read_text(encoding="utf-8", errors="replace")
        for i, c in enumerate(t):
            if ord(c) in SUSPECT and i + 1 < len(t) and ord(t[i + 1]) > 0x7F:
                out.append((page.name, t[max(0, i - 25):i + 15].replace("\n", " ")))
                break
    return out


# case studies arrive with their own number on the preview; everything else shares the brand card
PAGE_CARDS = {"curse.html": "og-curse.png", "basefail.html": "og-basefail.png",
              "dimensions.html": "og-dimensions.png", "helm.html": "og-helm.png"}


def _card_for(name: str) -> str:
    return PAGE_CARDS.get(name, "og-card.png")


def _head_metadata(pages):
    """Every page must declare where it canonically lives, and where a share links to.

    GitHub Pages happily serves the same page under more than one URL, and a search
    engine that cannot tell which is authoritative splits the ranking between them.
    og:url is the other half: without it a link posted to LinkedIn or X can preview
    as the wrong page, which is the one moment the funnel depends on.
    """
    out = []
    for page in pages:
        t = page.read_text(encoding="utf-8", errors="replace")
        want = SITE if page.name == "index.html" else SITE + page.name
        for tag, value, needle in (
                ("canonical", want, f'rel="canonical" href="{want}"'),
                ("og:url", want, f'property="og:url" content="{want}"'),
                ("og:image", SITE + _card_for(page.name),
                 f'property="og:image" content="{SITE}{_card_for(page.name)}"'),
                ("twitter:card", "summary_large_image",
                 'name="twitter:card" content="summary_large_image"')):
            if needle not in t:
                out.append(f"{page.name}: missing or wrong {tag} (expected {value})")
    return out


def _api_claims():
    """llms.txt advertises the status API to agents. Hold it to what the API serves.

    An agent reads that file to decide whether this endpoint answers its question.
    "for 8 public boards" plus a list of names is a promise, and a board added or
    renamed in the generator would break it silently — the JSON stays valid and
    the prose quietly stops being true.
    """
    api, doc = ROOT / "status.json", ROOT / "llms.txt"
    if not (api.exists() and doc.exists()):
        return []
    import json
    boards = [b["board"] for b in json.loads(api.read_text(encoding="utf-8"))["leaderboards"]]
    text = doc.read_text(encoding="utf-8")
    out = []

    m = re.search(r"for (\d+) public boards", text)
    if not m:
        out.append("llms.txt no longer states how many boards the API covers")
    elif int(m.group(1)) != len(boards):
        out.append(f"llms.txt says {m.group(1)} public boards, status.json serves {len(boards)}")

    # every board must be findable in the prose by its distinguishing word
    flat = re.sub(r"[^a-z0-9]+", " ", text.lower())
    for b in boards:
        word = re.sub(r"[^a-z0-9]+", " ", b.lower()).split()[-1]
        if word not in flat.split():
            out.append(f"status.json serves {b!r}, llms.txt never mentions {word!r}")
    return out


_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
          "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def _counted_claims():
    """The front page counts things on other pages. Make it recount them.

    "Eight audits", "all six checks" — every one of those numbers is a promise about
    a different file, and adding a case study or a calculator card silently makes the
    older sentence wrong. Nobody edits a page to break these; they break by growth.
    """
    index, calc = ROOT / "index.html", ROOT / "calculator.html"
    if not index.exists():
        return []
    text = index.read_text(encoding="utf-8")
    out = []

    cards = text.count('class="file"')
    m = re.search(r"section-h\">(\w+) audits\.", text)
    if not m:
        out.append("index.html no longer says how many audits it shows")
    elif _WORDS.get(m.group(1).lower()) != cards:
        out.append(f"index.html says {m.group(1)!r} audits, the page shows {cards} case files")

    # the method section numbers its probes 01..NN; the heading must agree with them
    probes = len(re.findall(r'class="n">\s*(\d\d)\s*·', text))
    m = re.search(r"section-h\">(\w+) questions I ask", text)
    if not m:
        out.append("index.html no longer says how many questions the method asks")
    elif _WORDS.get(m.group(1).lower()) != probes:
        out.append(f"index.html says {m.group(1)!r} questions, the method section numbers {probes}")

    if calc.exists():
        checks = calc.read_text(encoding="utf-8").count('class="calc"')
        for m in re.finditer(r"all (\w+) checks|(\w+) of the\s+checks I run", text):
            word = (m.group(1) or m.group(2) or "").lower()
            if _WORDS.get(word) != checks:
                out.append(f"index.html says {word!r} browser checks, calculator.html has {checks}")
    return out


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

    garbled = _mojibake(pages)
    stale_claims = _api_claims() + _counted_claims() + _head_metadata(pages)

    print(f"{len(pages)} pages, {len(external)} external links")

    if "--list" in sys.argv:
        for url in sorted(external):
            print(f"  ext  {url}  <- {', '.join(sorted(set(external[url])))}")

    if missing:
        print(f"\nBROKEN ({len(missing)}):")
        for url, srcs in sorted(missing.items()):
            print(f"  {url}  <- {', '.join(sorted(set(srcs)))}")

    if garbled:
        print(f"\nGARBLED TEXT ({len(garbled)}):")
        for name, ctx in garbled:
            print(f"  {name}: ...{ctx}...")

    if stale_claims:
        print(f"\nSTALE CLAIMS ({len(stale_claims)}):")
        for c in stale_claims:
            print(f"  {c}")

    if missing or garbled or stale_claims:
        return 1

    print("links resolve, text is clean, and every counted claim recounts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
