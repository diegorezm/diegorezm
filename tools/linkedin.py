"""Builds the LinkedIn banner (1584x396) from profile.toml, in the Lagoa style.

Writes linkedin/banner-{light,dark}.svg and, when Chrome or Edge is installed,
linkedin/banner-{light,dark}.png ready to upload.

Usage: python tools/linkedin.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

from lagoa import ROOT, THEMES, Svg, hill, hill_path, load_profile, measure, pine, round_tree

W, H = 1584, 396
OUT = ROOT / "linkedin"

# LinkedIn covers the bottom-left with the profile photo (roughly x<440, y>170 at this size)
# and the top-right with the edit button. It also shows the banner at about half size,
# so the text is drawn large and kept on the right, over a clean panel.


def banner(theme, p):
    t = THEMES[theme]
    s = Svg(W, H, theme, f"{p['name']} · {p['role']}. {p['banner_line']}")

    # ---- landscape on the left, fading into the panel
    s.add(f'<circle cx="300" cy="84" r="36" fill="{t["sun"]}"/>')
    far = hill(W, lambda x: 300, 12, 5, wl=(640, 340))
    s.add(hill_path(W, H, far, t["hill_far"]))
    for x, sz in [(150, 130), (205, 170), (262, 120), (560, 120), (610, 86)]:
        s.add(pine(x, far(x) + 34, sz, t))
    mid = hill(W, lambda x: 340, 8, 9, wl=(560, 300))
    s.add(hill_path(W, H, mid, t["hill_mid"]))
    for x, sz in [(40, 110), (440, 96), (690, 80)]:
        s.add(round_tree(x, mid(x) + 8, sz, t))
    near = hill(W, lambda x: 372, 5, 13, wl=(500, 280))
    s.add(hill_path(W, H, near, t["hill_near"]))
    s.defs.append(
        f'<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{t["paper"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{t["paper"]}"/></linearGradient>'
    )
    s.add(f'<rect x="600" width="{W - 600}" height="{H}" fill="url(#fade)"/>')

    # ---- text: name, role (first word roman, rest italic), value line, stack + site
    x0, top = 900, 118
    s.text(x0, top, p["name"], "mono5", 19, t["muted"], ls=3.6, upper=True)
    first, _, rest = p["role"].partition(" ")
    w = s.text(x0 - 4, top + 84, first + " ", "serif", 88, t["ink"], ls=-1.6)
    s.text(x0 - 4 + w, top + 84, rest.lower(), "serif-i", 88, t["muted"])
    s.text(x0, top + 132, p["banner_line"], "sans", 22, t["muted"])
    s.add(f'<line x1="{x0}" y1="{top + 166}" x2="{x0 + 40}" y2="{top + 166}" stroke="{t["pink"]}" '
          f'stroke-width="3" stroke-linecap="round"/>')
    s.text(x0, top + 204, "  ·  ".join(p["banner_stack"]), "mono5", 18, t["ink"], ls=1.6)
    s.text(W - 64, top + 204, p["site"].split("://")[-1].rstrip("/"), "mono", 18, t["muted"], anchor="end")
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
