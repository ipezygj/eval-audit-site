#!/usr/bin/env python3
"""Fail if the browser calculator stops agreeing with evalgate.

calculator.html tells visitors these checks "run the same math as evalgate". That
sentence is a claim about two independent implementations — one in Python, one
re-typed in JavaScript — and nothing re-checks it. Copies drift; the day they
disagree, one of them is quietly wrong on someone's real numbers and nothing says
which.

Only the pure helpers are compared. The per-card handlers read the DOM, so they
cannot be called headless without a browser; those are covered by rendering the
page instead. What is compared here is the arithmetic underneath them.

    python check_calc_parity.py          # exit 1 on any disagreement
    python check_calc_parity.py --show   # print both sides

Skips (exit 0) when node or evalgate is unavailable, so a machine without them
does not report a failure it did not measure.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOL = 1e-9

CASES = {
    "sidak": [(0.009, 23), (0.05, 2), (0.001, 100), (0.5, 3)],
    "bonferroni": [(0.009, 23), (0.05, 2), (0.4, 10)],
    "binomTwoSided": [(68, 100, 0.5), (10, 10, 0.5), (0, 10, 0.5), (252, 400, 0.5)],
    "probit": [(0.975,), (0.5,), (0.05,), (0.999,)],
    "mde": [(200, 0.85, 0.05, 0.8), (18, 0.94, 0.05, 0.8)],
}

# constantBaseline returns an object, so it is compared field by field
KEYS = [
    ["D"] * 41 + ["A"] * 22 + ["B"] * 22 + ["C"] * 15,   # the HELM shape
    ["A", "B", "C", "D"] * 25,                            # uniform: floor must equal chance
    ["B", "A", "B", "A"],                                 # a tie, which must break the same way
    ["x", "x", "y"],
]

# (scores, se) -> the margin half of the winner's-curse check. The resampling half is
# random by design and is verified by rendering the page instead.
MARGINS = [
    ([70.3, 70.3, 69.8, 69.1], 2.1),   # an exact tie at the top
    ([80.0, 60.0, 55.0], 1.0),          # a leader many SEs clear
    ([74.6, 74.2, 73.9], 1.1),          # the sample report's internal board
    ([50.0, 50.0], 0.0),                # no error bar at all: margin is infinite
]


def _script() -> str:
    html = (ROOT / "calculator.html").read_text(encoding="utf-8")
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    if not blocks:
        raise SystemExit("calculator.html has no <script> block")
    return max(blocks, key=len)


def _js_results(show: bool) -> dict:
    harness = _script() + "\nconst __out={};\n"
    for fn, args in CASES.items():
        harness += f"__out[{fn!r}]=[" + ",".join(f"{fn}({','.join(map(repr, a))})" for a in args) + "];\n"
    harness += ("__out['constantBaseline']=[" + ",".join(
        "(k => {const r = constantBaseline(k); return [r.best, r.floor, r.chance];})(%s)" % json.dumps(k)
        for k in KEYS) + "];\n")
    harness += ("__out['curseMargin']=[" + ",".join(
        "(a => {const r = curseMargin(a[0], a[1]); return [r.gap, r.gapSe === Infinity ? 'inf' : r.gapSe];})(%s)"
        % json.dumps([s, se]) for s, se in MARGINS) + "];\n")
    harness += "console.log(JSON.stringify(__out));\n"
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "harness.mjs"
        # The page defines its own `$` over document, so stub document only — declaring
        # `$` here collides with the page's const and the whole module fails to parse.
        f.write_text("const __el={value:'',innerHTML:'',addEventListener(){}};\n"
                     "globalThis.document={getElementById:()=>__el,addEventListener(){}};\n"
                     + harness, encoding="utf-8")
        p = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise SystemExit(f"node failed:\n{p.stderr[-800:]}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    if show:
        print("  js :", json.dumps(out)[:300])
    return out


def _py_results(show: bool) -> dict:
    from evalgate import checks as C
    out = {
        "sidak": [C.sidak(p, n) for p, n in CASES["sidak"]],
        "bonferroni": [C.bonferroni(p, n) for p, n in CASES["bonferroni"]],
        "binomTwoSided": [C.binomial_test(k, n) for k, n, _ in CASES["binomTwoSided"]],
        "probit": [C._probit(p) for (p,) in CASES["probit"]],
        "mde": [C.min_detectable_effect(n, p) for n, p, _, _ in CASES["mde"]],
    }
    from evalgate import leaderboard as L
    out["__unavailable__"] = [n for n, attr in (("curseMargin", "selection_audit"),
                                                ("constantBaseline", "constant_baseline"))
                              if not hasattr(L, attr)]
    if hasattr(L, "selection_audit"):
        out["curseMargin"] = []
        for s, se in MARGINS:
            a = L.selection_audit(s, se, trials=1)
            out["curseMargin"].append([a.gap, "inf" if a.gap_in_se == float("inf") else a.gap_in_se])
    if hasattr(L, "constant_baseline"):
        out["constantBaseline"] = [[(a := L.constant_baseline(k)).answer, a.score, a.chance]
                                   for k in KEYS]
    if show:
        print("  py :", json.dumps(out)[:300])
    return out


def main() -> int:
    # --strict: a check that could not run is a FAILURE, not a pass. Skipping is fine on a
    # laptop with no node and a stale evalgate; in CI the whole point is that the check ran,
    # and a skip printed into a log nobody reads is indistinguishable from a green tick.
    strict = "--strict" in sys.argv

    if shutil.which("node") is None:
        print("node not installed — parity not measured, skipping")
        return 1 if strict else 0
    try:
        import evalgate  # noqa: F401
    except ModuleNotFoundError:
        print("evalgate not installed — parity not measured, skipping")
        return 1 if strict else 0

    show = "--show" in sys.argv
    js, py = _js_results(show), _py_results(show)

    bad = []
    # A pair one side never produced is not agreement — it is a comparison that did not
    # happen. This harness claimed 37 agreeing values while 8 of them were never compared,
    # because a silent string replacement had dropped the JS half.
    # A pair the installed evalgate genuinely does not have yet is "not measured", and is
    # reported as such below. A pair that vanished for any OTHER reason is a broken harness.
    unavailable = set(py.get("__unavailable__", []))
    for name in (set(js) | set(py)) - {"__unavailable__"} - unavailable:
        if bool(js.get(name)) != bool(py.get(name)):
            bad.append(f"{name}: present on only one side "
                       f"(browser={'yes' if js.get(name) else 'no'}, "
                       f"evalgate={'yes' if py.get(name) else 'no'}) — nothing was compared")
    for name in CASES:
        for args, a, b in zip(CASES[name], js[name], py[name]):
            if a is None or abs(a - b) > TOL:
                bad.append(f"{name}{args}: browser {a!r} vs evalgate {b!r}")

    # constant_baseline ships in evalgate 0.6.0. An older installed copy cannot be compared,
    # and saying so is honest where silently passing would claim a check that never ran.
    for name in sorted(unavailable):
        print(f"installed evalgate has no {name} yet — that pair NOT measured")
    for i, (key, a, b) in enumerate(zip(KEYS, js.get("constantBaseline", []),
                                        py.get("constantBaseline", []))):
        label = f"constantBaseline[{i}] ({len(key)} items)"   # index too: two keys are 100 items long
        if a[0] != b[0]:
            bad.append(f"{label}: browser answers {a[0]!r}, evalgate answers {b[0]!r}")
        for field, x, y in zip(("floor", "chance"), a[1:], b[1:]):
            # evalgate rounds its reported score to 6 dp; compare at that resolution
            if abs(round(x, 6) - round(y, 6)) > 1e-9:
                bad.append(f"{label} {field}: browser {x!r} vs evalgate {y!r}")

    for i, ((s, se), a, b) in enumerate(zip(MARGINS, js.get("curseMargin", []),
                                            py.get("curseMargin", []))):
        label = f"curseMargin[{i}] ({len(s)} scores, se={se})"
        for field, x, y in zip(("gap", "gap_in_se"), a, b):
            if x is None or y is None:            # NaN crosses JSON as null; a value that is
                same = False                      # not a number is a failure, not a crash
            elif isinstance(x, str) or isinstance(y, str):
                same = x == y
            else:
                same = abs(round(x, 4) - round(y, 4)) <= 1e-9
            if not same:
                bad.append(f"{label} {field}: browser {x!r} vs evalgate {y!r}")

    if unavailable:
        print(f"({len(unavailable)} pair(s) skipped — install evalgate from source to measure them)")

    total = (sum(len(v) for v in CASES.values())
             + 3 * len(py.get("constantBaseline", []))
             + 2 * len(py.get("curseMargin", [])))
    if bad:
        print(f"\nDIVERGED ({len(bad)} of {total}):")
        for line in bad:
            print(f"  {line}")
        return 1
    if unavailable and strict:
        print(f"\nNOT MEASURED ({len(unavailable)} pair(s)): "
              f"{', '.join(sorted(unavailable))}. CI installs evalgate from source, so a "
              f"missing pair means the install is wrong, not that the pair is new. "
              f"Refusing to report agreement on a comparison that did not happen.")
        return 1
    print(f"browser and evalgate agree on all {total} values (tol {TOL:g})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
