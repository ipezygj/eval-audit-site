#!/usr/bin/env python3
"""ledger_claims - every number a ledger card states must be re-derivable from its lane's evidence files.

A correction written from memory repeats the error, and the ledger is the most public place a
remembered number can land. check_ledger proves the page's counters; this proves the CLAIMS: for
each card mapped in ledger_sources.json, every number in the card text must appear in that lane's
evidence files (RESULTS.md, results*, PREREG*, README*, replies/, comment/). A number that cannot
be traced is listed; fix the page or the mapping, never this check.

    python ledger_claims.py             report per mapped card; exit 1 if any number is untraceable
    python ledger_claims.py --selftest  the refusal must bite on a card with an invented number
"""
import json
import re
import sys
from html import unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = HERE.parent

SKIP = re.compile(r"doi:\S+|10\.5281/zenodo\.\d+|EF-\d+|arXiv:\S+|EDK/\S+|#\d+")
NUM = re.compile(r"\d+(?:[.,]\d+)?")
YEAR = re.compile(r"^(19|20)\d\d$")


def cards(html):
    # entries contain nested divs (class="tag"), so a lazy </div> match would cut before the h3:
    # take each chunk from one entry opening to the next opening or the section's end
    for chunk in html.split('<div class="entry">')[1:]:
        block = re.split(r"</section>", chunk)[0]
        h3 = re.search(r"<h3>(.*?)</h3>", block, re.S)
        text = unescape(re.sub(r"<[^>]+>", " ", block))
        yield (unescape(re.sub(r"<[^>]+>", " ", h3.group(1))).strip() if h3 else ""), text


def numbers(text):
    text = SKIP.sub(" ", text)
    out = []
    for t in NUM.findall(text):
        t = t.replace(",", ".")
        if YEAR.match(t) or float(t) < 2:           # years and tiny counts are prose, not results
            continue
        out.append(t)
    return sorted(set(out))


def evidence(lane_dir):
    pats = ("RESULTS.md", "results*", "PREREG*", "README*", "FINDINGS.md", "NOTES.md",
            "EVIDENCE*.md", "*out.txt", "*results.txt")
    files = [p for pat in pats for p in lane_dir.glob(pat) if p.is_file()]
    for sub in ("results", "replies", "comment", "code", "paper"):
        d = lane_dir / sub
        if d.is_dir():
            files += [p for p in d.rglob("*") if p.is_file() and p.suffix in (".md", ".txt", ".json", ".py")]
    txt = ""
    for f in files:
        try:
            txt += f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
    return txt.replace(",", "."), len(files)


def check(html, sources, root):
    bad = 0
    unmapped = []
    for h3, text in cards(html):
        key = next((k for k in sources if not k.startswith("_") and k in h3), None)
        if key is None:
            unmapped.append(h3[:60])
            continue
        src = sources[key]
        if isinstance(src, str):
            src = {"lane": src}
        allow = set(src.get("allow", []))
        lanes = src["lane"] if isinstance(src["lane"], list) else [src["lane"]]
        missing_dir = [ln for ln in lanes if not (root / ln).is_dir()]
        if missing_dir:
            print(f"[BAD] {key}: lane directory missing: {missing_dir}")
            bad += 1
            continue
        ev, nfiles = "", 0
        for ln in lanes:
            e, n = evidence(root / ln)
            ev += e
            nfiles += n
        lane = root / lanes[0]
        if not nfiles:
            print(f"[BAD] {key}: no evidence files found in {'+'.join(lanes)}")
            bad += 1
            continue
        def traced(n):
            if n in allow:                       # a derived value; its derivation is noted in ledger_sources.json
                return True
            forms = {n}
            if "." in n:                         # a percentage on the page may live as a fraction in the files
                forms.add(("%.10g" % (float(n) / 100)))
            return any(re.search(r"(?<![\d.])" + re.escape(f) + r"(?![\d])", ev) for f in forms)
        missing = [n for n in numbers(text) if not traced(n)]
        if missing:
            print(f"[BAD] {key} ({lane.name}, {nfiles} files): untraceable numbers: {', '.join(missing)}")
            bad += 1
        else:
            print(f"[OK ] {key} ({lane.name}): all {len(numbers(text))} numbers traced in {nfiles} files")
    if unmapped:
        print(f"[INFO] {len(unmapped)} cards not yet mapped in ledger_sources.json")
    return bad


def selftest():
    import tempfile
    html = ('<div class="entry"><h3>good card</h3><p>rate 55.1% over 653 boards</p></div>'
            '<div class="entry"><h3>bad card</h3><p>rate 99.9% over 653 boards</p></div>')
    with tempfile.TemporaryDirectory() as td:
        lane = Path(td) / "lane"
        lane.mkdir()
        (lane / "RESULTS.md").write_text("main: 55.1 % of 653 boards", encoding="utf-8")
        src = {"good card": "lane", "bad card": "lane"}
        bad = check(html, src, Path(td))
        ok = bad == 1
        print(f"[{'OK ' if ok else 'BAD'}] selftest: exactly the invented number was refused")
        return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    html = (HERE / "ledger.html").read_text(encoding="utf-8")
    sources = json.loads((HERE / "ledger_sources.json").read_text(encoding="utf-8"))
    return 1 if check(html, sources, HOME) else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
