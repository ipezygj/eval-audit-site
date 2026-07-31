#!/usr/bin/env python3
"""Run every check this site has, and say plainly which ones did not run.

Four checks accumulated, each answering a question the others cannot:

  check_links.py        the repo is self-consistent — no dead link, no mojibake,
                        no counted claim ("Ten audits", "all eight checks") that
                        disagrees with the pages it describes
  check_calc_parity.py  the browser calculator still computes what evalgate computes
  check_calc_render.py  the page actually renders numbers, in a real browser
  check_live.py         production serves what the repo says it should

The offline pair runs by default. The two that need a browser or the network are
opt-in, because a check that fails for want of a dependency teaches people to
ignore failures.

    python check_all.py           # links + parity
    python check_all.py --full    # everything
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

OFFLINE = [("repo consistency", "check_links.py", []),
           ("browser vs evalgate", "check_calc_parity.py", [])]
FULL = [("renders in a browser", "check_calc_render.py", []),
        ("production", "check_live.py", ["--quiet"])]


def run(label: str, script: str, args: list[str]) -> tuple[str, int, str]:
    p = subprocess.run([sys.executable, str(ROOT / script), *args],
                       capture_output=True, text=True, timeout=600)
    tail = [l for l in p.stdout.strip().splitlines() if l.strip()]
    return label, p.returncode, (tail[-1] if tail else "(no output)")


def main() -> int:
    checks = OFFLINE + (FULL if "--full" in sys.argv else [])
    if "--full" not in sys.argv:
        print("running the offline checks; add --full for the browser and production ones\n")

    results, skipped = [], []
    for label, script, args in checks:
        name, code, last = run(label, script, args)
        # the scripts say so themselves when a dependency is missing
        if code == 0 and ("skipping" in last or "not measured" in last):
            skipped.append((name, last))
            print(f"  SKIP  {name:22} {last}")
        else:
            results.append((name, code, last))
            print(f"  {'PASS' if code == 0 else 'FAIL'}  {name:22} {last}")

    failed = [r for r in results if r[1] != 0]
    print()
    if skipped:
        print(f"{len(skipped)} check(s) did not run — that is not a pass:")
        for name, why in skipped:
            print(f"  {name}: {why}")
    if failed:
        print(f"{len(failed)} check(s) FAILED — rerun that script alone for the detail.")
        return 1
    print(f"{len(results)} check(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
