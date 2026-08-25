#!/usr/bin/env python3
"""Draw the social preview cards.

A link posted to LinkedIn or X is previewed before it is read, and a generic
brand card says the same thing about every page. The case studies each have one
number worth arriving with — 72.1%, 12%, k=6 — so those get their own card. The
rest share the brand card.

Deterministic: same inputs, same PNGs, so re-running does not churn the repo.

    python make_og_cards.py           # write any card that is missing or stale
    python make_og_cards.py --force   # redraw all of them
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1200, 630
PAPER, INK, MUTED, ACCENT, LINE = "#0D1117", "#E8EDF3", "#93A0B1", "#37C6D0", "#222A35"

# name -> (eyebrow, headline lines, the number, what the number means)
CARDS = {
    "og-card": ("EVAL INTEGRITY  ·  INDEPENDENT AUDITS",
                ["Measured,", "Not Believed"], None,
                "Is the #1 real, or a coin flip wearing a crown?"),
    "og-curse": ("CASE STUDY  ·  SEVEN PUBLIC LEADERBOARDS",
                 ["The announced #1", "is probably not", "the best model"], "72.1%",
                 "chance SWE-bench Verified's leader is not the true leader"),
    "og-basefail": ("CASE STUDY  ·  BASE RATES",
                    ["0.978 AUC on the", "benchmark. 12%", "in the clinic."], "12%",
                    "of its alarms are real where the condition is rare"),
    "og-helm": ("CASE STUDY  ·  HELM CLASSIC MMLU",
                ["A fixed answer", "outranks most of", "this leaderboard"], "22/29",
                "published runs beaten by answering D to everything"),
    "og-zerostderr": ("CASE STUDY  ·  OPEN LLM LEADERBOARD v2",
                      ["A standard error", "of exactly zero"], "423",
                      "published records claim no uncertainty at all"),
    "og-choices": ("CASE STUDY  ·  44 BOARD/CHOICE PAIRS",
                   ["Change one", "defensible choice,", "and the #1 changes"], "19/44",
                   "board rankings whose leader survives the alternative"),
    "og-dimensions": ("CASE STUDY  ·  LEADERBOARD DIMENSIONALITY",
                      ["Your leaderboard", "is not one-", "dimensional"], "k ≈ 6",
                      "independent skills hidden inside one MTEB column"),
}


def font(name: str, size: int):
    for candidate in (name, "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw(eyebrow, headline, number, caption) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=LINE, width=1)
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=LINE, width=1)
    d.rectangle([0, 0, W - 1, H - 1], outline=LINE, width=2)
    d.line([(72, 150), (72, 470)], fill=ACCENT, width=4)

    d.text((110, 132), eyebrow, font=font("segoeuib.ttf", 24), fill=ACCENT)
    size = 92 if len(headline) < 3 else 68
    y = 190 if len(headline) < 3 else 186
    for line in headline:
        d.text((108, y), line, font=font("georgiab.ttf", size), fill=INK)
        y += size + 10

    if number:
        d.text((760, 300), number, font=font("georgiab.ttf", 116), fill=ACCENT)
    d.text((110, 470 if len(headline) > 2 else 418), caption,
           font=font("segoeui.ttf", 30 if number else 34), fill=MUTED)
    d.text((110, 530), "ipezygj.com",
           font=font("consola.ttf", 26), fill=ACCENT)
    return img


def main() -> int:
    force = "--force" in sys.argv
    for name, spec in CARDS.items():
        out = ROOT / f"{name}.png"
        if out.exists() and not force:
            print(f"  kept    {out.name}")
            continue
        draw(*spec).save(out, optimize=True)
        print(f"  wrote   {out.name}  ({out.stat().st_size // 1024} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
