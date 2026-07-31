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
    if hasattr(L, "constant_baseline"):
        out["constantBaseline"] = [[(a := L.constant_baseline(k)).answer, a.score, a.chance]
                                   for k in KEYS]
    if show:
        print("  py :", json.dumps(out)[:300])
    return out


def main() -> int:
    if shutil.which("node") is None:
        print("node not installed — parity not measured, skipping")
        return 0
    try:
        import evalgate  # noqa: F401
    except ModuleNotFoundError:
        print("evalgate not installed — parity not measured, skipping")
        return 0

    show = "--show" in sys.argv
    js, py = _js_results(show), _py_results(show)

    bad = []
    for name in CASES:
        for args, a, b in zip(CASES[name], js[name], py[name]):
            if a is None or abs(a - b) > TOL:
                bad.append(f"{name}{args}: browser {a!r} vs evalgate {b!r}")

    # constant_baseline ships in evalgate 0.6.0. An older installed copy cannot be compared,
    # and saying so is honest where silently passing would claim a check that never ran.
    if "constantBaseline" not in py:
        print("installed evalgate predates constant_baseline — that pair NOT measured")
    for i, (key, a, b) in enumerate(zip(KEYS, js.get("constantBaseline", []),
                                        py.get("constantBaseline", []))):
        label = f"constantBaseline[{i}] ({len(key)} items)"   # index too: two keys are 100 items long
        if a[0] != b[0]:
            bad.append(f"{label}: browser answers {a[0]!r}, evalgate answers {b[0]!r}")
        for field, x, y in zip(("floor", "chance"), a[1:], b[1:]):
            # evalgate rounds its reported score to 6 dp; compare at that resolution
            if abs(round(x, 6) - round(y, 6)) > 1e-9:
                bad.append(f"{label} {field}: browser {x!r} vs evalgate {y!r}")

    total = sum(len(v) for v in CASES.values()) + 3 * len(py.get("constantBaseline", []))
    if bad:
        print(f"\nDIVERGED ({len(bad)} of {total}):")
        for line in bad:
            print(f"  {line}")
        return 1
    print(f"browser and evalgate agree on all {total} values (tol {TOL:g})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
