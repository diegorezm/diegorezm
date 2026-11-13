"""Builds the LinkedIn banner (1584x396) from profile.toml, in the Lagoa style.

Writes linkedin/banner-{light,dark}.svg and, when Chrome or Edge is installed,
linkedin/banner-{light,dark}.png ready to upload.

Usage: python tools/linkedin.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

from build import short
from lagoa import (
    ROOT, THEMES, Svg, birds, ghost, hill, hill_path, load_profile, meadow, measure, pine, river, round_tree,
    strip, swimmer,
)

W, H = 1584, 396
OUT = ROOT / "linkedin"

# LinkedIn covers the bottom-left with the profile photo (roughly x<420, y>170 at this size)
# and the top-right with the edit button: text stays right of x=900 and below y=80.


def banner(theme, p):
    t = THEMES[theme]
    s = Svg(W, H, theme, f"{p['name']} · {p['role']}. {p['headline']} {p['headline_italic']}")

    # ---- landscape (the site footer, recomposed)
    s.add(f'<circle cx="300" cy="84" r="40" fill="{t["sun"]}"/>')
    ghost(s, 372, 312, p["name"].split()[0], 214, anchor="start")
    s.add(birds(560, 76, t, 1.6))
    far = hill(W, lambda x: 292 + max(0, x - 900) * 0.03, 12, 5, wl=(640, 340))
    s.add(hill_path(W, H, far, t["hill_far"]))
    for x, sz in [(120, 120), (172, 170), (230, 130)]:
        s.add(pine(x, far(x) + 30, sz, t))
    mid = hill(W, lambda x: 336, 8, 9, wl=(560, 300))
    s.add(hill_path(W, H, mid, t["hill_mid"]))
    for x, sz in [(36, 110), (486, 110), (552, 70), (880, 84)]:
        s.add(round_tree(x, mid(x) + 8, sz, t))
    for x, sz in [(800, 120), (842, 90)]:
        s.add(pine(x, mid(x) + 10, sz, t))
    near = hill(W, lambda x: 368, 5, 13, wl=(500, 280))
    s.add(hill_path(W, H, near, t["hill_near"]))
    s.add(river(700, far(700) + 2, 18, 690, H, 300, t))
    s.add(meadow(0, 560, near, t, seed=3))
    s.add(meadow(840, W, near, t, seed=8))
    swimmer(s, 692, 360, 66)

    # ---- text block, right side
    x0 = 940
    s.text(x0, 116, f"{p['name']}  ·  " + "  ·  ".join(p["tags"]), "mono5", 13, t["muted"], ls=2.6, upper=True)
    s.text(x0 - 4, 196, p["headline"], "serif", 88, t["ink"], ls=-1.8)
    s.text(x0, 256, p["headline_italic"], "serif-i", 62, t["muted"])


    cells = [("Email", p["email"]), ("Website", short(p["site"])), ("GitHub", short(p["github"]))]
    widths = [max(measure(l.upper(), "mono5", 10, 2), measure(v, "mono", 13)) + 58 for l, v in cells]
    strip(s, W - 72 - sum(widths), 296, cells, widths)
    return s


def browser():
    for c in [
        shutil.which("chrome"), shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]:
        if c and Path(c).exists():
            return c


def main():
    p = load_profile()["profile"]
    OUT.mkdir(exist_ok=True)
    exe = browser()
    for theme in THEMES:
        svg = OUT / f"banner-{theme}.svg"
        svg.write_text(banner(theme, p).render(), encoding="utf-8")
        if exe:
            png = OUT / f"banner-{theme}.png"
            subprocess.run(
                [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                 f"--window-size={W},{H}", svg.resolve().as_uri()],
                check=False, capture_output=True,
            )
    print(f"banners em {OUT}" + ("" if exe else " (só SVG: instale Chrome/Edge para gerar o PNG)"))


if __name__ == "__main__":
    sys.exit(main())
