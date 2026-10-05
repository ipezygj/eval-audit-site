"""Gate for ledger.html: the hero counters must equal what the page's own entries say, and every DOI on the
page must resolve. Built 2026-09-28 from a real failure: the counters were first written from memory (26/7/12/7)
and were wrong; the recount gave 31/5/19/6. Run before every push:  python check_ledger.py  (exit 1 = do not push).
--selftest proves the gate can refuse: it recounts a mutated copy and must fail on it."""
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
COUNTS = json.loads((Path(__file__).resolve().parent / "ledger_counts.json").read_text(encoding="utf-8"))


def recount(html):
    # Entries inside HTML comments are not on the page. 2026-09-28..10-05 the held Kela entry was counted
    # from inside its comment, so the live counters said 31 claims / 6 open while 30 / 5 were visible.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    counters = {v.strip(): int(k) for k, v in re.findall(r"<b>(\d+)</b><span>([^<]+)</span>", html)}
    titles = [re.sub(r"&[a-z]+;", " ", t) for t in re.findall(r"<h3>([^<]+)</h3>", html)]
    keys = [k for k in COUNTS if not k.startswith("_")]
    errors = []
    used = {}
    for t in titles:
        hits = [k for k in keys if k in t]
        if len(hits) != 1:
            errors.append(f"entry '{t[:60]}' matches {len(hits)} sidecar keys — update ledger_counts.json")
            continue
        if hits[0] in used:
            errors.append(f"sidecar key '{hits[0]}' matches two entries")
        used[hits[0]] = t
    for k in keys:
        if k not in used:
            errors.append(f"sidecar key '{k}' matches no entry on the page — removed or retitled?")
    sums = [sum(COUNTS[k][i] for k in used) for i in range(4)]
    return dict(claims=sums[0], held=sums[1], over=sums[2], open=sums[3], key_errors=errors,
                counters=dict(claims=counters.get("claims re-measured"),
                              held=counters.get("held as published"),
                              over=counters.get("overstated or not supported"),
                              open=counters.get("open / in correspondence")))


def check_dois(html):
    bad = []
    for doi in sorted(set(re.findall(r"10\.5281/zenodo\.(\d+)", html))):
        try:
            urllib.request.urlopen(f"https://zenodo.org/api/records/{doi}", timeout=30)
        except Exception:
            # concept DOIs are not API records; resolve via search
            try:
                r = urllib.request.urlopen(
                    f'https://zenodo.org/api/records?q=conceptdoi:"10.5281/zenodo.{doi}"&size=1', timeout=30)
                if not json.loads(r.read())["hits"]["hits"]:
                    bad.append(doi)
            except Exception:
                bad.append(doi)
    return bad


def run(html):
    r = recount(html)
    errors = list(r["key_errors"])
    for k in ("claims", "held", "over", "open"):
        if r[k] != r["counters"][k]:
            errors.append(f"counter '{k}': page says {r['counters'][k]}, entries say {r[k]}")
    return r, errors


if __name__ == "__main__":
    html = (HERE / "ledger.html").read_text(encoding="utf-8")
    if "--selftest" in sys.argv:
        mutated = html.replace("<b>31</b><span>claims re-measured</span>",
                               "<b>26</b><span>claims re-measured</span>", 1)
        _, errs = run(mutated)
        ok = bool(errs)
        print(f"[{'OK ' if ok else 'BAD'}] selftest: mutated counter {'refused' if ok else 'PASSED SILENTLY'}")
        _, errs2 = run(html)
        print(f"[{'OK ' if not errs2 else 'BAD'}] selftest: real page {'passes' if not errs2 else errs2}")
        sys.exit(0 if ok and not errs2 else 1)
    r, errors = run(html)
    for e in errors:
        print("FAIL", e)
    bad = check_dois(html)
    for d in bad:
        print("FAIL doi does not resolve: 10.5281/zenodo." + d)
    if not errors and not bad:
        print(f"OK counters {r['counters']} match entries; all DOIs resolve")
    sys.exit(1 if (errors or bad) else 0)
