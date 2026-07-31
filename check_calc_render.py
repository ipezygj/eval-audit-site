#!/usr/bin/env python3
"""Fail if the calculator page loads but computes nothing.

A JavaScript error kills the whole script block, so one broken line in one card
silently blanks every card on the page. The layout still renders, the inputs
still accept typing, and nothing tells the visitor that no number is coming —
which is how this page shipped for the length of one commit on 2026-07-31.

Neither of the other checks sees it. check_links reads the HTML as text;
check_calc_parity runs the pure helpers in node and would catch a *syntax*
error, but not a handler that throws only once the DOM is involved.

So: open the real page in a real browser, refuse any console or page error, and
require every result box to have produced text.

    python check_calc_render.py           # exit 1 if a card is silent
    python check_calc_render.py --show    # print what each card rendered

Skips (exit 0) when Playwright is unavailable, rather than reporting a pass it
did not measure.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "calculator.html"
RESULT_IDS = ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8out"]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        print("playwright not installed — render not measured, skipping")
        return 0

    show = "--show" in sys.argv
    errors, empty = [], []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: errors.append(f"console.error: {m.text}")
                if m.type == "error" else None)
        page.goto(PAGE.as_uri(), wait_until="load")
        page.wait_for_timeout(4000)          # the resampling card takes a beat

        for rid in RESULT_IDS:
            try:
                text = page.inner_text(f"#{rid}").strip()
            except Exception as exc:
                empty.append(f"#{rid}: not on the page ({type(exc).__name__})")
                continue
            if not text:
                empty.append(f"#{rid}: rendered nothing")
            elif show:
                print(f"  #{rid}: {text[:90]}")
        browser.close()

    print(f"{len(RESULT_IDS)} result boxes checked in a real browser")
    if errors or empty:
        if errors:
            print(f"SCRIPT ERRORS ({len(errors)}):")
            for e in dict.fromkeys(errors):
                print(f"  {e[:160]}")
        if empty:
            print(f"SILENT CARDS ({len(empty)}):")
            for e in empty:
                print(f"  {e}")
        return 1
    print("every card computed something, with no script errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
